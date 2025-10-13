"""
Agent configuration and performance analysis schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal


class HistoricalTrend(BaseModel):
    """Historical performance trend"""
    time_window: str = Field(..., description="Time window (24h/7d/30d)")
    avg_execution_time_ms: float = Field(..., description="Average execution time")
    p50_execution_time_ms: float = Field(..., description="P50 execution time")
    p95_execution_time_ms: float = Field(..., description="P95 execution time")
    p99_execution_time_ms: float = Field(..., description="P99 execution time")
    success_rate_percent: float = Field(..., description="Success rate")
    total_requests: int = Field(..., description="Total requests")


class ErrorPattern(BaseModel):
    """Error pattern analysis"""
    error_type: str = Field(..., description="Error category")
    frequency: int = Field(..., description="Occurrence count")
    percentage: float = Field(..., description="Percentage of total errors")
    sample_message: str = Field(..., description="Sample error message")


class AgentPerformanceAnalysis(BaseModel):
    """Advanced agent performance analysis"""
    agent_name: str = Field(..., description="Agent name")
    
    # Execution time metrics
    execution_times: Dict[str, float] = Field(..., description="Execution time percentiles")
    
    # Success rates
    success_rates: Dict[str, float] = Field(..., description="Success rates by time window")
    
    # Error patterns
    error_patterns: List[ErrorPattern] = Field(..., description="Categorized error analysis")
    
    # Historical trends
    historical_trends: List[HistoricalTrend] = Field(..., description="Performance trends")
    
    # Optimization recommendations
    optimization_recommendations: List[str] = Field(..., description="Performance recommendations")


class AgentConfigurationUpdate(BaseModel):
    """Agent configuration update request"""
    agent_name: Literal['retriever', 'analyzer', 'orchestrator'] = Field(..., description="Agent to configure")
    
    # Configuration parameters
    model_selection: Optional[str] = Field(None, description="Model selection")
    timeout_seconds: Optional[float] = Field(None, ge=1.0, le=300.0, description="Timeout value")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="Max retry attempts")
    performance_tuning: Optional[Dict[str, Any]] = Field(None, description="Performance parameters")


class ConfigurationUpdateResponse(BaseModel):
    """Configuration update response"""
    success: bool = Field(..., description="Whether update succeeded")
    agent_name: str = Field(..., description="Agent name")
    previous_config: Dict[str, Any] = Field(..., description="Previous configuration")
    new_config: Dict[str, Any] = Field(..., description="New configuration")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    rollback_id: str = Field(..., description="Rollback identifier")
    applied_at: str = Field(..., description="Configuration applied timestamp")

