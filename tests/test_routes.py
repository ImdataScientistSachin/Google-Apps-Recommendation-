import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client

def test_api_info(client):
    response = client.get('/api/info')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert data['status'] == 'active'

def test_api_popular(client):
    response = client.get('/api/popular')
    assert response.status_code == 200
    data = response.get_json()
    assert 'popular_apps' in data
    assert isinstance(data['popular_apps'], list)

def test_api_recommendations_missing_param(client):
    response = client.get('/api/recommendations')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_api_recommendations_valid(client):
    # This test assumes at least one app exists in the dataset
    # Try with a common app name, fallback to 404 if not found
    response = client.get('/api/recommendations?app_name=Facebook')
    assert response.status_code in (200, 404)
    data = response.get_json()
    if response.status_code == 200:
        assert 'recommendations' in data
    else:
        assert 'error' in data 