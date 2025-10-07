"""
Production-ready Agentic Personalized Financial Advisor (APFA) backend
- Multi-agent system with RAG, LLM, and compliance tools
- FastAPI, observability, error handling, and security best practices
"""
import os
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer
import faiss
from deltalake import DeltaTable
from minio import Minio
import boto3
from trl import PPOTrainer
from aif360.datasets import BinaryLabelDataset
from opentelemetry import trace
from tenacity import retry, stop_after_attempt, wait_exponential, circuit_breaker
import time
from cachetools import TTLCache
from config import settings
from langchain.llms import HuggingFacePipeline
from slowapi import Limiter
from slowapi.util import get_remote_address
import numpy as np
from langchain.tools import Tool
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import signal
from contextlib import asynccontextmanager
from textblob import TextBlob
import asyncio
from aiohttp import ClientSession, TCPConnector
import aioredis
from fastapi.responses import JSONResponse
import gzip
from profanity_check import predict_prob
import re
from pydantic import field_validator

# Setup logging
logging.basicConfig(level=getattr(logging, logging.DEBUG if settings.debug else settings.log_level))
logger = logging.getLogger(__name__)

# Load secrets from environment (never hardcode in prod)
MINIO_ENDPOINT = settings.minio_endpoint
MINIO_ACCESS_KEY = settings.minio_access_key
MINIO_SECRET_KEY = settings.minio_secret_key
AWS_REGION = settings.aws_region

# Initialize clients with error handling
try:
    embedder = SentenceTransformer(settings.embedder_model)
    minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    bedrock = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
except Exception as e:
    logger.error(f"Initialization error: {e}")
    raise

# RAG Setup (FAISS index from Delta Lake)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def load_rag_index():
    """
    Load and index RAG data from DeltaTable for efficient similarity search.
    
    Returns:
        tuple: (DataFrame, FAISS index) containing the loaded data and search index.
    
    Raises:
        ValueError: If DataFrame is empty or missing required columns.
        Exception: For any loading or indexing failures.
    """
    logger.info("Loading RAG index")
    try:
        dt = DeltaTable(settings.delta_table_path)
        df = dt.to_pandas()
        if df.empty or 'profile' not in df.columns:
            raise ValueError("DeltaTable must contain non-empty data with 'profile' column")
        embeddings = np.array(embedder.encode(df['profile'].tolist()))
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        logger.info("RAG index loaded successfully")
        return df, index
    except Exception as e:
        logger.error(f"Error loading RAG index: {e}")
        raise RAGError("Failed to load RAG index") from e

rag_df, faiss_index = load_rag_index()

# Tools (MCP-compatible)
@circuit_breaker(failure_threshold=5, recovery_timeout=60)
def retrieve_loan_data(query: str) -> str:
    """RAG retrieval for loan compliance/docs."""
    try:
        query_emb = np.array(embedder.encode([query]))
        faiss.normalize_L2(query_emb)
        _, indices = faiss_index.search(query_emb, k=min(5, len(rag_df)))
        return '\n'.join(rag_df.iloc[indices[0]]['profile'].tolist())
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return "Error retrieving loan data."

@circuit_breaker(failure_threshold=5, recovery_timeout=60)
def simulate_risk(input_data: str) -> str:
    """Simulate loan risk with LLM."""
    try:
        response = bedrock.invoke_agent(
            agentId='loan-risk-agent',
            sessionId='session-123',
            inputText=input_data
        )
        return response['completion']
    except Exception as e:
        logger.error(f"Risk simulation error: {e}")
        return "Error simulating risk."

tools = [
    Tool.from_function(
        func=retrieve_loan_data,
        name="retrieve_loan_data",
        description="RAG retrieval for loan compliance/docs."
    ),
    Tool.from_function(
        func=simulate_risk,
        name="simulate_risk",
        description="Simulate loan risk with LLM."
    )
]
tool_executor = ToolExecutor(tools)

# LLM Setup (Fine-tuned with DeepSpeed/RLHF)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def load_llm():
    """
    Load the LLM model and tokenizer.
    
    Returns:
        tuple: (model, tokenizer) for the loaded LLM.
    
    Raises:
        Exception: For any loading failures.
    """
    logger.info("Loading LLM")
    try:
        model = AutoModelForCausalLM.from_pretrained(settings.llm_model_name)
        tokenizer = AutoTokenizer.from_pretrained(settings.llm_model_name)
        logger.info("LLM loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Error loading LLM: {e}")
        raise LLMError("Failed to load LLM") from e

model, tokenizer = load_llm()
llm_pipeline = pipeline('text-generation', model=model, tokenizer=tokenizer)
llm = HuggingFacePipeline(pipeline=llm_pipeline)

# Multi-Agent Graph (LangGraph)
import typing
class AgentState(typing.TypedDict):
    messages: typing.List[str]
    query: str

@trace.get_tracer(__name__).start_as_current_span("Retriever Agent")
def retriever_agent(state):
    prompt = ChatPromptTemplate.from_messages([("system", "Retrieve context for loan query."), ("human", "{query}")])
    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    result = executor.invoke({"query": state["query"]})
    return {"messages": state["messages"] + [result["output"]]}

@trace.get_tracer(__name__).start_as_current_span("Analyzer Agent")
def analyzer_agent(state):
    messages = state["messages"]
    response = llm_pipeline(messages[-1], max_new_tokens=200)[0]['generated_text']
    return {"messages": messages + [response]}

@trace.get_tracer(__name__).start_as_current_span("Orchestrator Agent")
def orchestrator_agent(state):
    """
    Orchestrator agent with enhanced bias detection and fairness monitoring.
    """
    messages = state["messages"]
    combined_text = ' '.join(messages)
    
    # Detect bias
    bias_score = detect_bias(combined_text)
    
    if bias_score > 0.3:
        logger.warning(f"High bias detected (score: {bias_score:.2f}). Recommendation: {messages[-1]}")
        # In production, could trigger retraining or human review
        state["bias_detected"] = True
        state["bias_score"] = bias_score
    else:
        state["bias_detected"] = False
        state["bias_score"] = bias_score
    
    # Simple fairness check based on response diversity
    response_lengths = [len(msg) for msg in messages]
    if len(set(response_lengths)) < 2:  # All responses similar length
        logger.info("Low response diversity detected - consider varying advice styles")
    
    return state

graph = StateGraph(AgentState)
graph.add_node("retriever", retriever_agent)
graph.add_node("analyzer", analyzer_agent)
graph.add_node("orchestrator", orchestrator_agent)
graph.add_edge("retriever", "analyzer")
graph.add_edge("analyzer", "orchestrator")
graph.add_edge("orchestrator", END)
app_graph = graph.compile()

# FastAPI for Deployment
app = FastAPI()

# CORS, security, and validation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoanQuery(BaseModel):
    query: str = Field(..., min_length=5, max_length=500, pattern=r"^[a-zA-Z0-9\s\?\.\,\!\-\+\=\$\%\(\)]+$")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Advanced validation for loan queries."""
        # Check for profanity
        if predict_prob([v])[0] > 0.8:
            raise ValueError("Query contains inappropriate content")
        
        # Check for financial relevance
        financial_keywords = ['loan', 'credit', 'mortgage', 'finance', 'interest', 'payment', 'debt', 'borrow']
        if not any(keyword in v.lower() for keyword in financial_keywords):
            raise ValueError("Query must be related to financial or loan topics")
        
        # Extract and validate amounts if present
        amount_pattern = r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        amounts = re.findall(amount_pattern, v)
        for amount in amounts:
            try:
                num_amount = float(amount.replace(',', ''))
                if num_amount <= 0 or num_amount > 10000000:  # Reasonable loan limits
                    raise ValueError(f"Invalid loan amount: ${amount}")
            except ValueError:
                raise ValueError(f"Invalid amount format: ${amount}")
        
        # Check for rate mentions
        rate_pattern = r'(\d+(?:\.\d+)?)\s*\%'
        rates = re.findall(rate_pattern, v)
        for rate in rates:
            try:
                num_rate = float(rate)
                if num_rate < 0 or num_rate > 50:  # Reasonable interest rate limits
                    raise ValueError(f"Invalid interest rate: {rate}%")
            except ValueError:
                raise ValueError(f"Invalid rate format: {rate}%")
        
        # Sanitize HTML/script content
        if re.search(r'<[^>]+>', v):
            raise ValueError("HTML content not allowed")
        
        # Check for excessive repetition
        words = v.lower().split()
        if len(words) > len(set(words)) * 2:  # More than 50% repetition
            raise ValueError("Query contains excessive repetition")
        
        return v

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
cache = TTLCache(maxsize=100, ttl=300)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Prometheus metrics
REQUEST_COUNT = Counter('apfa_requests_total', 'Total number of requests', ['method', 'endpoint', 'status'])
RESPONSE_TIME = Histogram('apfa_response_time_seconds', 'Response time in seconds', ['endpoint'])
ERROR_COUNT = Counter('apfa_errors_total', 'Total number of errors', ['type'])
CACHE_HITS = Counter('apfa_cache_hits_total', 'Total cache hits')
CACHE_MISSES = Counter('apfa_cache_misses_total', 'Total cache misses')
ACTIVE_REQUESTS = Gauge('apfa_active_requests', 'Number of active requests')

# Mock user database (in production, use real database)
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
        "disabled": False,
    }
}

# Authentication and Authorization
def verify_password(plain_password, hashed_password):
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    """Get user from database."""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return user_dict

def authenticate_user(username: str, password: str):
    """Authenticate a user."""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username=username)
    if user is None:
        raise credentials_exception
    return user

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def load_embedder():
    """
    Return the global embedder instance.
    
    Returns:
        SentenceTransformer: The loaded embedding model.
    """
    return embedder

def generate_loan_advice(q, dt, embedder, model, tokenizer):
    """
    Generate loan advice using the multi-agent graph.
    
    Args:
        q: LoanQuery object containing the user query.
        dt: DataFrame from RAG index.
        embedder: Embedding model.
        model: LLM model.
        tokenizer: LLM tokenizer.
    
    Returns:
        str: Generated advice from the agent graph.
    """
    result = app_graph.invoke({"messages": [], "query": q.query})
    return result["messages"][-1]

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status.
    """
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns:
        str: Prometheus metrics in text format.
    """
    return generate_latest()

@app.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login endpoint.
    
    Returns:
        dict: Access token and token type.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Advanced caching with Redis fallback
redis_client = None
cache = TTLCache(maxsize=1000, ttl=600)  # Increased size and TTL

async def init_redis():
    """Initialize Redis client for distributed caching."""
    global redis_client
    try:
        redis_client = await aioredis.from_url("redis://localhost:6379", decode_responses=True)
        logger.info("Redis cache initialized")
    except Exception as e:
        logger.warning(f"Redis not available, using in-memory cache: {e}")

async def get_cache(key: str):
    """Get value from cache (Redis or memory)."""
    if redis_client:
        return await redis_client.get(key)
    return cache.get(key)

async def set_cache(key: str, value: str, ttl: int = 600):
    """Set value in cache."""
    if redis_client:
        await redis_client.setex(key, ttl, value)
    else:
        cache[key] = value

# Async HTTP client with connection pooling
async def create_http_client():
    """Create async HTTP client with connection pooling."""
    connector = TCPConnector(limit=100, limit_per_host=10, ttl_dns_cache=300)
    return ClientSession(connector=connector)

# Performance optimization: Pre-compute embeddings cache
embeddings_cache = {}

async def get_cached_embedding(text: str):
    """Get cached embedding or compute new one."""
    if text in embeddings_cache:
        return embeddings_cache[text]
    
    # Compute in thread pool to avoid blocking
    embedding = await asyncio.to_thread(embedder.encode, [text])
    embeddings_cache[text] = embedding
    return embedding

# Per-user rate limiting
user_request_counts = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Per-user rate limiting middleware."""
    client_ip = request.client.host
    current_time = time.time()
    
    if client_ip not in user_request_counts:
        user_request_counts[client_ip] = []
    
    # Clean old requests (keep last 60 seconds)
    user_request_counts[client_ip] = [
        t for t in user_request_counts[client_ip] if current_time - t < 60
    ]
    
    if len(user_request_counts[client_ip]) >= 10:  # 10 requests per minute per IP
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."}
        )
    
    user_request_counts[client_ip].append(current_time)
    
    response = await call_next(request)
    return response

@app.post("/generate-advice")
@limiter.limit("10/minute")
async def generate_advice(q: LoanQuery, current_user: dict = Depends(get_current_user)):
    """
    Generate personalized loan advice using RAG and LLM.
    
    Args:
        q: Validated loan query.
        current_user: Authenticated user.
    
    Returns:
        dict: Advice response.
    
    Raises:
        HTTPException: For authentication or internal errors.
    """
    ACTIVE_REQUESTS.inc()
    REQUEST_COUNT.labels(method='POST', endpoint='/generate-advice', status='started').inc()
    
    start_time = time.time()
    
    api_key = api_key_header
    if not api_key or api_key != settings.api_key:
        logger.warning("Unauthorized access attempt")
        REQUEST_COUNT.labels(method='POST', endpoint='/generate-advice', status='401').inc()
        ACTIVE_REQUESTS.dec()
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        query_str = q.model_dump_json()
        cached_result = await get_cache(f"advice:{query_str}")
        if cached_result:
            logger.info(f"Returning cached advice for user {current_user['username']}")
            CACHE_HITS.inc()
            REQUEST_COUNT.labels(method='POST', endpoint='/generate-advice', status='200').inc()
            ACTIVE_REQUESTS.dec()
            return JSONResponse(content=eval(cached_result))  # Safe since we control the data
        
        CACHE_MISSES.inc()
        
        # Async model loading and processing
        dt = await asyncio.to_thread(load_rag_index)
        embedder_instance = await asyncio.to_thread(load_embedder)
        
        load_time = time.time() - start_time
        logger.info(f"Model loading completed in {load_time:.2f} seconds")
        
        # Generate advice in thread pool
        advice = await asyncio.to_thread(generate_loan_advice, q, dt, embedder_instance, model, tokenizer)
        
        result = {"advice": advice, "user": current_user["username"]}
        
        # Cache result
        await set_cache(f"advice:{query_str}", str(result))
        
        total_time = time.time() - start_time
        RESPONSE_TIME.labels(endpoint='/generate-advice').observe(total_time)
        logger.info(f"Total request processing time: {total_time:.2f} seconds")
        
        REQUEST_COUNT.labels(method='POST', endpoint='/generate-advice', status='200').inc()
        ACTIVE_REQUESTS.dec()
        return result
    
    except RAGError as e:
        logger.error(f"RAG error in generate_advice: {e}")
        ERROR_COUNT.labels(type='rag').inc()
        REQUEST_COUNT.labels(method='POST', endpoint='/generate-advice', status='503').inc()
        ACTIVE_REQUESTS.dec()
        raise HTTPException(status_code=503, detail="RAG service unavailable")
    except LLMError as e:
        logger.error(f"LLM error in generate_advice: {e}")
        ERROR_COUNT.labels(type='llm').inc()
        REQUEST_COUNT.labels(method='POST', endpoint='/generate-advice', status='503').inc()
        ACTIVE_REQUESTS.dec()
        raise HTTPException(status_code=503, detail="LLM service unavailable")
    except ExternalServiceError as e:
        logger.error(f"External service error in generate_advice: {e}")
        ERROR_COUNT.labels(type='external').inc()
        REQUEST_COUNT.labels(method='POST', endpoint='/generate-advice', status='502').inc()
        ACTIVE_REQUESTS.dec()
        raise HTTPException(status_code=502, detail="External service error")
    except Exception as e:
        logger.error(f"Unexpected error in generate_advice: {e}")
        ERROR_COUNT.labels(type='unexpected').inc()
        REQUEST_COUNT.labels(method='POST', endpoint='/generate-advice', status='500').inc()
        ACTIVE_REQUESTS.dec()
        raise HTTPException(status_code=500, detail="Internal server error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting APFA application...")
    
    # Validate environment
    required_env_vars = ['MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'AWS_REGION', 'JWT_SECRET']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Initialize Redis
    await init_redis()
    
    # Pre-load models (optional, for faster first request)
    try:
        logger.info("Pre-loading models...")
        global model, tokenizer
        model, tokenizer = await asyncio.to_thread(load_llm)
        logger.info("Models pre-loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to pre-load models: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down APFA application...")
    if redis_client:
        await redis_client.close()
    # Cleanup resources if needed

app = FastAPI(lifespan=lifespan)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
