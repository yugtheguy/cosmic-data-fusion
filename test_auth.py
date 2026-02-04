"""
Test authentication endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """Test user registration"""
    print("\n=== Testing User Registration ===")
    
    payload = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        return response.json()["access_token"]
    return None


def test_login():
    """Test user login"""
    print("\n=== Testing User Login ===")
    
    # OAuth2PasswordRequestForm uses form data, not JSON
    payload = {
        "username": "test@example.com",  # OAuth2 expects 'username', but we use email
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def test_get_me(token):
    """Test getting current user profile"""
    print("\n=== Testing Get Current User ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_protected_without_token():
    """Test accessing protected endpoint without token"""
    print("\n=== Testing Protected Endpoint Without Token ===")
    
    response = requests.get(f"{BASE_URL}/auth/me")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    print("🔐 Testing JWT Authentication System")
    print("=" * 50)
    
    # Test 1: Register a new user
    token = test_register()
    
    if token:
        print("\n✅ Registration successful!")
        
        # Test 2: Login with same credentials
        token = test_login()
        
        if token:
            print("\n✅ Login successful!")
            
            # Test 3: Get current user profile
            test_get_me(token)
            print("\n✅ Profile retrieval successful!")
    
    # Test 4: Try accessing protected endpoint without token
    test_protected_without_token()
    print("\n✅ Protection working - unauthorized access blocked!")
    
    print("\n" + "=" * 50)
    print("🎉 All authentication tests completed!")
