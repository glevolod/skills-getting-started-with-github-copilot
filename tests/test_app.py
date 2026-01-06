"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities(monkeypatch):
    """Reset activities to initial state before each test"""
    import app as app_module
    
    initial_activities = {
        "Soccer Team": {
            "description": "Join the school soccer team and compete in regional matches",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 6:00 PM",
            "max_participants": 25,
            "participants": ["alex@mergington.edu", "sarah@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Develop basketball skills and participate in friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu", "emily@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore various art mediums including painting, drawing, and sculpture",
            "schedule": "Wednesdays, 3:30 PM - 5:30 PM",
            "max_participants": 18,
            "participants": ["lily@mergington.edu", "noah@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in plays and learn acting, stage design, and production",
            "schedule": "Thursdays, 3:30 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["ava@mergington.edu", "ethan@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop critical thinking and public speaking through competitive debates",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["isabella@mergington.edu", "liam@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "Compete in science and engineering challenges at regional competitions",
            "schedule": "Fridays, 3:30 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["mia@mergington.edu", "william@mergington.edu"]
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    monkeypatch.setattr(app_module, "activities", initial_activities.copy())
    yield
    monkeypatch.setattr(app_module, "activities", initial_activities.copy())


class TestRoot:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the get activities endpoint"""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # There should be 9 activities
        
        # Check that a known activity exists
        assert "Soccer Team" in data
        assert "Basketball Club" in data
        
    def test_activities_have_required_fields(self, client, reset_activities):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for the signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Soccer Team"]["participants"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/NonExistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test signing up when already registered for an activity"""
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": "alex@mergington.edu"}  # Already registered
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test signing up for multiple different activities"""
        email = "multistudent@mergington.edu"
        
        # Sign up for Soccer Team
        response1 = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for Basketball Club
        response2 = client.post(
            "/activities/Basketball Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Soccer Team"]["participants"]
        assert email in activities["Basketball Club"]["participants"]


class TestUnregister:
    """Tests for the unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successfully unregistering from an activity"""
        # First sign up
        client.post(
            "/activities/Soccer Team/signup",
            params={"email": "student@mergington.edu"}
        )
        
        # Then unregister
        response = client.post(
            "/activities/Soccer Team/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify the student was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "student@mergington.edu" not in activities["Soccer Team"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/NonExistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregistering when not registered for an activity"""
        response = client.post(
            "/activities/Soccer Team/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant"""
        response = client.post(
            "/activities/Soccer Team/unregister",
            params={"email": "alex@mergington.edu"}  # Already registered
        )
        assert response.status_code == 200
        
        # Verify the student was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "alex@mergington.edu" not in activities["Soccer Team"]["participants"]
