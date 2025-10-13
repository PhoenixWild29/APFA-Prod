"""
Multi-agent system monitoring schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal


class AgentPerformanceMetrics(BaseModel):
    """Individual agent performance metrics"""
    response_time_ms: float = Field(..., description="Average response time")
    success_rate_percent: float = Field(..., description="Success rate percentage")
    resource_utilization: Dict[str, float] = Field(..., description="Resource usage metrics")


class AgentStatusInfo(BaseModel):
    """Individual agent status"""
    agent_name: str = Field(..., description="Agent name")
    health_status: Literal['healthy', 'unhealthy', 'degraded'] = Field(..., description="Health status")
    processing_capability: Literal['available', 'busy', 'offline'] = Field(..., description="Processing capability")
    performance_metrics: AgentPerformanceMetrics = Field(..., description="Performance metrics")
    last_execution_timestamp: Optional[str] = Field(None, description="Last successful execution")


class MultiAgentStatusResponse(BaseModel):
    """Multi-agent system status response"""
    overall_system_health: str = Field(..., description="Overall system health")
    agents: List[AgentStatusInfo] = Field(..., description="Individual agent statuses")
    response_time_ms: float = Field(..., description="Status check response time")
    timestamp: str = Field(..., description="Status check timestamp")


class AgentTestRequest(BaseModel):
    """Agent testing request"""
    agent_name: Optional[Literal['retriever', 'analyzer', 'orchestrator', 'all']] = Field(
        'all',
        description="Agent to test (or 'all')"
    )
    test_scenarios: List[str] = Field(
        default_factory=lambda: ['basic_functionality', 'performance_benchmark', 'integration_test'],
        description="Test scenarios to run"
    )
    test_parameters: Dict[str, Any] = Field(default_factory=dict, description="Test parameters")


class AgentTestResult(BaseModel):
    """Individual agent test result"""
    agent_name: str = Field(..., description="Agent name")
    test_scenario: str = Field(..., description="Test scenario")
    status: Literal['pass', 'fail'] = Field(..., description="Test status")
    execution_time_ms: float = Field(..., description="Test execution time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    performance_benchmark: Optional[Dict[str, float]] = Field(None, description="Performance metrics")


class AgentTestResponse(BaseModel):
    """Agent testing response"""
    overall_status: Literal['pass', 'fail', 'partial'] = Field(..., description="Overall test status")
    individual_results: List[AgentTestResult] = Field(..., description="Individual test results")
    total_tests: int = Field(..., description="Total tests run")
    passed_tests: int = Field(..., description="Number of passed tests")
    failed_tests: int = Field(..., description="Number of failed tests")
    total_execution_time_ms: float = Field(..., description="Total test execution time")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")

