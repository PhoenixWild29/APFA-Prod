"""
Enhanced API response models for optimized loan advisory

Provides comprehensive response structures with:
- Performance metrics
- Bias detection results
- Agent execution traces
- Transparency and monitoring support
"""
from datetime import datetime, timezone
from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from app.models.performance_tracking import ResponseMetrics, CacheInteraction, AgentExecutionStep


class BiasDetectionResults(BaseModel):
    """
    Bias detection and fairness validation results
    
    Provides transparency into bias detection and mitigation
    for loan advisory responses.
    
    Attributes:
        bias_score: Overall bias score (0.0-1.0, lower is better)
        fairness_metrics: Fairness assessment metrics
        validation_passed: Whether response passed bias validation
        detected_issues: List of detected bias issues
        mitigation_applied: List of mitigation strategies applied
        orchestrator_confidence: Orchestrator's confidence in fairness
    
    Example:
        >>> bias_results = BiasDetectionResults(
        ...     bias_score=0.15,
        ...     fairness_metrics={"demographic_parity": 0.95, "equal_opportunity": 0.93},
        ...     validation_passed=True,
        ...     detected_issues=[],
        ...     mitigation_applied=["neutral_language", "inclusive_examples"],
        ...     orchestrator_confidence=0.92
        ... )
    """
    bias_score: float = Field(
        ...,
        description="Overall bias score (0.0-1.0, lower is better)",
        ge=0.0,
        le=1.0
    )
    fairness_metrics: Dict[str, float] = Field(
        ...,
        description="Fairness assessment metrics",
        examples=[{
            "demographic_parity": 0.95,
            "equal_opportunity": 0.93,
            "predictive_parity": 0.94,
            "treatment_equality": 0.96
        }]
    )
    validation_passed: bool = Field(
        ...,
        description="Whether response passed bias validation"
    )
    detected_issues: List[str] = Field(
        default_factory=list,
        description="List of detected bias issues"
    )
    mitigation_applied: List[str] = Field(
        default_factory=list,
        description="List of mitigation strategies applied"
    )
    orchestrator_confidence: float = Field(
        ...,
        description="Orchestrator's confidence in fairness (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "bias_score": 0.15,
                "fairness_metrics": {
                    "demographic_parity": 0.95,
                    "equal_opportunity": 0.93,
                    "predictive_parity": 0.94
                },
                "validation_passed": True,
                "detected_issues": [],
                "mitigation_applied": [
                    "neutral_language",
                    "inclusive_examples",
                    "balanced_representation"
                ],
                "orchestrator_confidence": 0.92
            }
        }


class OptimizedAdviceResponse(BaseModel):
    """
    Optimized loan advisory response
    
    Comprehensive response structure with performance metrics,
    bias detection, and agent execution transparency.
    
    Attributes:
        advice: Generated loan advice content
        confidence_score: Overall advice confidence (0.0-1.0)
        processing_time_ms: Total processing time
        was_cached: Whether response was served from cache
        cache_hit_rate: Current cache hit rate
        agent_trace: Agent execution steps
        performance_metrics: Detailed performance breakdown
        bias_detection_results: Bias detection and fairness results
    
    Example:
        >>> response = OptimizedAdviceResponse(
        ...     advice="Based on your financial profile...",
        ...     confidence_score=0.88,
        ...     processing_time_ms=185.5,
        ...     was_cached=False,
        ...     cache_hit_rate=0.75,
        ...     agent_trace=[...],
        ...     performance_metrics=metrics,
        ...     bias_detection_results=bias_results
        ... )
    """
    advice: str = Field(
        ...,
        description="Generated loan advice content",
        min_length=1
    )
    confidence_score: float = Field(
        ...,
        description="Overall advice confidence (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    processing_time_ms: float = Field(
        ...,
        description="Total processing time (ms)",
        ge=0.0
    )
    was_cached: bool = Field(
        ...,
        description="Whether response was served from cache"
    )
    cache_hit_rate: float = Field(
        ...,
        description="Current cache hit rate (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    agent_trace: List[AgentExecutionStep] = Field(
        ...,
        description="Agent execution steps"
    )
    performance_metrics: ResponseMetrics = Field(
        ...,
        description="Detailed performance breakdown"
    )
    bias_detection_results: BiasDetectionResults = Field(
        ...,
        description="Bias detection and fairness results"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "advice": "Based on your financial profile and current market conditions...",
                "confidence_score": 0.88,
                "processing_time_ms": 185.5,
                "was_cached": False,
                "cache_hit_rate": 0.75,
                "agent_trace": [],
                "performance_metrics": {
                    "total_latency_ms": 185.5,
                    "rag_retrieval_ms": 45.2,
                    "llm_inference_ms": 125.0,
                    "cache_lookup_ms": 2.5,
                    "agent_coordination_ms": 12.8,
                    "was_cached": False,
                    "cache_hit_rate": 0.75
                },
                "bias_detection_results": {
                    "bias_score": 0.15,
                    "fairness_metrics": {
                        "demographic_parity": 0.95,
                        "equal_opportunity": 0.93
                    },
                    "validation_passed": True,
                    "detected_issues": [],
                    "mitigation_applied": ["neutral_language"],
                    "orchestrator_confidence": 0.92
                }
            }
        }

