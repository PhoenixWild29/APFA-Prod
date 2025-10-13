"""
Query analysis schemas with linguistic processing
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal


class LinguisticAnalysis(BaseModel):
    """Linguistic analysis results"""
    sentence_structure: str = Field(..., description="Sentence structure assessment")
    readability_score: float = Field(..., ge=0.0, le=100.0, description="Readability score")
    financial_terminology_density: float = Field(..., ge=0.0, le=1.0, description="Financial term density")
    grammatical_complexity: int = Field(..., ge=1, le=10, description="Grammar complexity (1-10)")


class IntentClassification(BaseModel):
    """Intent classification results"""
    primary_intent: Literal[
        'loan_application',
        'rate_inquiry',
        'eligibility_check',
        'comparison_request',
        'general_advice'
    ] = Field(..., description="Primary user intent")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    secondary_intents: List[str] = Field(default_factory=list, description="Secondary intents")


class ExtractedEntity(BaseModel):
    """Extracted financial entity"""
    entity_type: str = Field(..., description="Entity type")
    value: str = Field(..., description="Extracted value")
    position_start: int = Field(..., description="Start position in query")
    position_end: int = Field(..., description="End position in query")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")


class ComplexityAssessment(BaseModel):
    """Query complexity assessment"""
    complexity_score: int = Field(..., ge=1, le=10, description="Complexity score (1-10)")
    vocabulary_complexity: int = Field(..., ge=1, le=10, description="Vocabulary difficulty")
    multi_part_questions: int = Field(..., description="Number of sub-questions")
    required_domain_knowledge: int = Field(..., ge=1, le=10, description="Required expertise level")


class ProcessingRecommendations(BaseModel):
    """Processing recommendations"""
    optimal_routing: str = Field(..., description="Recommended agent routing")
    required_data_sources: List[str] = Field(..., description="Required data sources")
    estimated_processing_time_ms: float = Field(..., description="Estimated processing time")


class QueryAnalysisMetadata(BaseModel):
    """Analysis metadata"""
    analysis_timestamp: str = Field(..., description="Analysis timestamp")
    processing_time_ms: float = Field(..., description="Processing time")
    confidence_scores: Dict[str, float] = Field(..., description="Component confidence scores")
    suggested_improvements: List[str] = Field(..., description="Query improvement suggestions")


class QueryAnalysisResponse(BaseModel):
    """Comprehensive query analysis response"""
    query_text: str = Field(..., description="Analyzed query")
    linguistic_analysis: LinguisticAnalysis = Field(..., description="Linguistic analysis")
    intent_classification: IntentClassification = Field(..., description="Intent classification")
    entity_extraction: List[ExtractedEntity] = Field(..., description="Extracted entities")
    complexity_assessment: ComplexityAssessment = Field(..., description="Complexity assessment")
    processing_recommendations: ProcessingRecommendations = Field(..., description="Processing recommendations")
    metadata: QueryAnalysisMetadata = Field(..., description="Analysis metadata")

