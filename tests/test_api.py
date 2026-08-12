import pytest
import requests
import time

BASE_URL = "http://localhost:5001"

class TestVideoAPI:
    """Test suite for Video API endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        response = requests.get(f"{BASE_URL}/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
    
    def test_create_video_valid(self):
        """Test video creation with valid input"""
        payload = {"topic": "How to make coffee"}
        response = requests.post(
            f"{BASE_URL}/api/create-video",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert "video_id" in data
    
    def test_create_video_missing_topic(self):
        """Test video creation without topic"""
        payload = {}
        response = requests.post(
            f"{BASE_URL}/api/create-video",
            json=payload
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_create_video_invalid_chars(self):
        """Test video creation with invalid characters"""
        payload = {"topic": "Topic with <script>alert('xss')</script>"}
        response = requests.post(
            f"{BASE_URL}/api/create-video",
            json=payload
        )
        assert response.status_code == 400
    
    def test_create_video_too_long(self):
        """Test video creation with topic too long"""
        payload = {"topic": "A" * 201}
        response = requests.post(
            f"{BASE_URL}/api/create-video",
            json=payload
        )
        assert response.status_code == 400
    
    def test_rate_limiting(self):
        """Test rate limiting is enforced"""
        payload = {"topic": "Rate limit test"}
        
        # Make 6 rapid requests (limit is 5 per minute)
        responses = []
        for _ in range(6):
            response = requests.post(
                f"{BASE_URL}/api/create-video",
                json=payload
            )
            responses.append(response.status_code)
        
        # At least one should be rate limited
        assert 429 in responses

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
