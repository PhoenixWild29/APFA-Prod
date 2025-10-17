"""
Locust Performance Testing Configuration
Simulates user load on the APFA application
"""

from locust import HttpUser, task, between
import random


class APFAUser(HttpUser):
    """Simulates a typical APFA application user"""
    
    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts - simulate login"""
        # Health check on start
        self.client.get("/health")
    
    @task(3)
    def view_health(self):
        """Check application health endpoint"""
        self.client.get("/health", name="/health")
    
    @task(2)
    def view_metrics(self):
        """Check metrics endpoint"""
        self.client.get("/metrics", name="/metrics")
    
    @task(5)
    def api_root(self):
        """Access API root/docs"""
        self.client.get("/", name="/")
        
    @task(1)
    def view_docs(self):
        """Access API documentation"""
        self.client.get("/docs", name="/docs")
        self.client.get("/redoc", name="/redoc")


class AdminUser(HttpUser):
    """Simulates an admin user performing administrative tasks"""
    
    wait_time = between(2, 5)
    
    @task(2)
    def admin_dashboard(self):
        """Access admin dashboard"""
        # Note: In real scenario, would need authentication
        self.client.get("/health", name="admin-health-check")
    
    @task(1)
    def view_metrics(self):
        """View detailed metrics"""
        self.client.get("/metrics", name="admin-metrics")


class APIUser(HttpUser):
    """Simulates API consumers hitting various endpoints"""
    
    wait_time = between(0.5, 2)
    
    @task(10)
    def health_check(self):
        """Frequent health checks"""
        self.client.get("/health")
    
    @task(5)
    def metrics_endpoint(self):
        """Monitor metrics"""
        self.client.get("/metrics")
    
    @task(1)
    def api_info(self):
        """Get API information"""
        self.client.get("/")


# Performance test scenarios
class QuickLoadTest(HttpUser):
    """Quick load test - simulates normal traffic"""
    wait_time = between(1, 2)
    
    @task
    def normal_workflow(self):
        """Typical user workflow"""
        # Health check
        self.client.get("/health")
        
        # View metrics
        self.client.get("/metrics")


class StressTest(HttpUser):
    """Stress test - simulates heavy load"""
    wait_time = between(0.1, 0.5)
    
    @task
    def rapid_requests(self):
        """Rapid fire requests"""
        endpoints = ["/health", "/metrics", "/"]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)


class SpikeTest(HttpUser):
    """Spike test - simulates sudden traffic spikes"""
    wait_time = between(0, 0.1)
    
    @task
    def spike_requests(self):
        """Rapid requests to simulate spike"""
        self.client.get("/health")


# Custom load shape for gradual ramp-up
from locust import LoadTestShape


class GradualRampUp(LoadTestShape):
    """
    A load shape that gradually increases users over time
    
    Stages:
    1. 0-60s: Ramp up to 50 users
    2. 60-120s: Ramp up to 100 users
    3. 120-180s: Hold at 100 users
    4. 180-240s: Ramp down to 50 users
    5. 240-300s: Ramp down to 0 users
    """
    
    stages = [
        {"duration": 60, "users": 50, "spawn_rate": 1},
        {"duration": 120, "users": 100, "spawn_rate": 2},
        {"duration": 180, "users": 100, "spawn_rate": 0},
        {"duration": 240, "users": 50, "spawn_rate": 1},
        {"duration": 300, "users": 0, "spawn_rate": 2},
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None


# Usage instructions:
"""
Basic Usage:
-----------
# Run quick test (10 users, 1 per second, 60 seconds)
locust -f tests/locustfile.py --headless -u 10 -r 1 -t 60s --host http://localhost:8000

# Run with web UI
locust -f tests/locustfile.py --host http://localhost:8000

# Run specific user class
locust -f tests/locustfile.py --headless -u 50 -r 5 -t 120s --host http://localhost:8000 APIUser

# Run stress test
locust -f tests/locustfile.py --headless -u 100 -r 10 -t 60s --host http://localhost:8000 StressTest

# Run with custom load shape
locust -f tests/locustfile.py --headless --host http://localhost:8000 GradualRampUp

Performance Metrics to Monitor:
------------------------------
- Response time (p50, p95, p99)
- Requests per second (RPS)
- Failure rate
- Active users
- CPU and memory usage

Expected Results:
----------------
- /health endpoint: < 50ms response time
- /metrics endpoint: < 100ms response time
- 99.9% success rate
- Able to handle 100+ concurrent users
"""

