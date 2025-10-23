"""
Comprehensive API test script for Coffee Shop API.
Tests all authentication and user management endpoints.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

# Global variables for test data
access_token = None
refresh_token = None
admin_token = None
user_id = None
admin_user_id = None
test_results = {"passed": 0, "failed": 0}

def test_passed():
    test_results["passed"] += 1

def test_failed():
    test_results["failed"] += 1

# Test 1: Root endpoint
print_test("1. Root Endpoint")
try:
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print_success(f"Root endpoint working: {response.json()}")
        test_passed()
    else:
        print_error(f"Root endpoint failed: {response.status_code}")
        test_failed()
except Exception as e:
    print_error(f"Connection error: {e}")
    print_warning("Is the server running? Start with: uv run fastapi dev app/main.py")
    exit(1)

# Test 2: Signup
print_test("2. User Signup")
signup_data = {
    "email": "test@example.com",
    "password": "TestPass123",
    "first_name": "John",
    "last_name": "Doe"
}
response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
if response.status_code == 201:
    data = response.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    print_success(f"Signup successful!")
    print_info(f"Access Token: {access_token[:50]}...")
    print_info(f"Refresh Token: {refresh_token[:50]}...")
    test_passed()
else:
    print_error(f"Signup failed: {response.status_code} - {response.text}")
    test_failed()

# Test 3: Duplicate email signup (should fail)
print_test("3. Duplicate Email Signup (Should Fail)")
response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
if response.status_code == 400:
    print_success(f"Correctly rejected duplicate email: {response.json()}")
    test_passed()
else:
    print_error(f"Should have rejected duplicate email: {response.status_code}")
    test_failed()

# Test 4: Weak password (should fail)
print_test("4. Weak Password Signup (Should Fail)")
weak_password_data = {
    "email": "weak@example.com",
    "password": "weak"  # Less than 8 chars
}
response = requests.post(f"{BASE_URL}/auth/signup", json=weak_password_data)
if response.status_code == 422:
    print_success(f"Correctly rejected weak password")
    test_passed()
else:
    print_error(f"Should reject weak password: {response.status_code}")
    test_failed()

# Test 5: Login
print_test("5. User Login")
login_data = {
    "email": "test@example.com",
    "password": "TestPass123"
}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if response.status_code == 200:
    data = response.json()
    access_token = data["access_token"]
    print_success(f"Login successful!")
    test_passed()
else:
    print_error(f"Login failed: {response.status_code} - {response.text}")
    test_failed()

# Test 6: Wrong password login (should fail)
print_test("6. Wrong Password Login (Should Fail)")
wrong_login = {
    "email": "test@example.com",
    "password": "WrongPassword"
}
response = requests.post(f"{BASE_URL}/auth/login", json=wrong_login)
if response.status_code == 401:
    print_success(f"Correctly rejected wrong password: {response.json()}")
    test_passed()
else:
    print_error(f"Should have rejected wrong password: {response.status_code}")
    test_failed()

# Test 7: Get current user profile
print_test("7. Get Current User Profile")
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/users/me", headers=headers)
if response.status_code == 200:
    data = response.json()
    user_id = data["id"]
    print_success(f"Profile retrieved:")
    print(json.dumps(data, indent=2))
    test_passed()
else:
    print_error(f"Get profile failed: {response.status_code}")
    test_failed()

# Test 8: Check verification status (should be false)
print_test("8. Check Verification Status (Should be False)")
if response.status_code == 200:
    if not data["is_verified"]:
        print_success(f"User correctly marked as unverified")
        test_passed()
    else:
        print_error(f"User should be unverified")
        test_failed()

# Test 9: Verify email with wrong code (should fail)
print_test("9. Verify Email with Wrong Code (Should Fail)")
verify_data = {"code": "000000"}
response = requests.post(f"{BASE_URL}/auth/verify", json=verify_data, headers=headers)
if response.status_code == 400:
    print_success(f"Correctly rejected wrong code: {response.json()}")
    test_passed()
else:
    print_error(f"Should have rejected wrong code: {response.status_code}")
    test_failed()

# Test 10: Verify email with correct code
print_test("10. Verify Email with Correct Code")
print_info("Check your FastAPI server console for the verification code!")
print_warning("Look for a message like: 'VERIFICATION CODE FOR test@example.com'")
verification_code = input(f"\n{Colors.CYAN}Enter 6-digit verification code: {Colors.END}")

if verification_code and len(verification_code) == 6:
    verify_data = {"code": verification_code}
    response = requests.post(f"{BASE_URL}/auth/verify", json=verify_data, headers=headers)
    if response.status_code == 200:
        print_success(f"Email verified: {response.json()}")
        test_passed()
    else:
        print_error(f"Verification failed: {response.status_code} - {response.text}")
        test_failed()
else:
    print_warning("Skipped verification test (no code entered)")

# Test 11: Check verification status again (should be true)
print_test("11. Check Verification Status (Should be True)")
response = requests.get(f"{BASE_URL}/users/me", headers=headers)
if response.status_code == 200:
    data = response.json()
    if data["is_verified"]:
        print_success(f"User correctly marked as verified")
        test_passed()
    else:
        print_error(f"User should be verified")
        test_failed()

# Test 12: Resend verification code (should fail - already verified)
print_test("12. Resend Verification (Should Fail - Already Verified)")
response = requests.post(f"{BASE_URL}/auth/resend-verification", headers=headers)
if response.status_code == 400:
    print_success(f"Correctly rejected resend for verified user: {response.json()}")
    test_passed()
else:
    print_error(f"Should reject resend for verified user: {response.status_code}")
    test_failed()

# Test 13: Refresh token
print_test("13. Refresh Access Token")
refresh_data = {"refresh_token": refresh_token}
response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
if response.status_code == 200:
    data = response.json()
    new_access_token = data["access_token"]
    new_refresh_token = data["refresh_token"]
    print_success(f"Token refreshed successfully!")
    print_info(f"New Access Token: {new_access_token[:50]}...")
    access_token = new_access_token
    refresh_token = new_refresh_token
    test_passed()
else:
    print_error(f"Token refresh failed: {response.status_code} - {response.text}")
    test_failed()

# Test 14: Invalid refresh token (should fail)
print_test("14. Invalid Refresh Token (Should Fail)")
invalid_refresh = {"refresh_token": "invalid.token.here"}
response = requests.post(f"{BASE_URL}/auth/refresh", json=invalid_refresh)
if response.status_code == 401:
    print_success(f"Correctly rejected invalid refresh token")
    test_passed()
else:
    print_error(f"Should reject invalid token: {response.status_code}")
    test_failed()

# Test 15: Access admin endpoint as regular user (should fail)
print_test("15. Access Admin Endpoint as Regular User (Should Fail)")
response = requests.get(f"{BASE_URL}/users", headers=headers)
if response.status_code == 403:
    print_success(f"Correctly blocked non-admin access: {response.json()}")
    test_passed()
else:
    print_error(f"Should block non-admin access: {response.status_code}")
    test_failed()

# Test 16: Create admin user
print_test("16. Create Admin User")
print_info("To test admin endpoints, we need to create and promote an admin user")
print_info("Run this command in another terminal: python create_admin.py admin@example.com")
print_info("Or press ENTER to skip admin tests")

input("\nPress ENTER when ready to continue...")

# Try to login as admin
admin_login = {
    "email": "admin@example.com",
    "password": "AdminPass123"
}
response = requests.post(f"{BASE_URL}/auth/login", json=admin_login)
if response.status_code == 200:
    data = response.json()
    admin_token = data["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get admin user info
    response = requests.get(f"{BASE_URL}/users/me", headers=admin_headers)
    if response.status_code == 200:
        admin_user_id = response.json()["id"]
        print_success(f"Admin user logged in successfully!")
        test_passed()
    else:
        print_warning("Admin login successful but couldn't get profile")
        admin_headers = None
else:
    print_warning("Admin user not found or wrong credentials - skipping admin tests")
    admin_headers = None

# Test 17: List all users (admin only)
if admin_headers:
    print_test("17. List All Users (Admin Only)")
    response = requests.get(f"{BASE_URL}/users", headers=admin_headers)
    if response.status_code == 200:
        users = response.json()
        print_success(f"Retrieved {len(users)} users:")
        for user in users:
            print(f"  - {user['email']} (ID: {user['id']}, Role: {user['role']})")
        test_passed()
    else:
        print_error(f"List users failed: {response.status_code} - {response.text}")
        test_failed()
else:
    print_warning("Skipping test 17 (admin not available)")

# Test 18: Get specific user by ID (admin only)
if admin_headers and user_id:
    print_test("18. Get User by ID (Admin Only)")
    response = requests.get(f"{BASE_URL}/users/{user_id}", headers=admin_headers)
    if response.status_code == 200:
        print_success(f"Retrieved user: {response.json()['email']}")
        test_passed()
    else:
        print_error(f"Get user failed: {response.status_code}")
        test_failed()
else:
    print_warning("Skipping test 18 (admin not available)")

# Test 19: Update user (admin only)
if admin_headers and user_id:
    print_test("19. Update User Profile (Admin Only)")
    update_data = {
        "first_name": "Jane",
        "last_name": "Smith"
    }
    response = requests.patch(f"{BASE_URL}/users/{user_id}", json=update_data, headers=admin_headers)
    if response.status_code == 200:
        updated_user = response.json()
        print_success(f"User updated: {updated_user['first_name']} {updated_user['last_name']}")
        test_passed()
    else:
        print_error(f"Update failed: {response.status_code} - {response.text}")
        test_failed()
else:
    print_warning("Skipping test 19 (admin not available)")

# Test 20: Delete user as regular user (should fail)
print_test("20. Delete User as Regular User (Should Fail)")
response = requests.delete(f"{BASE_URL}/users/999", headers=headers)
if response.status_code == 403:
    print_success(f"Correctly blocked non-admin from deleting users")
    test_passed()
else:
    print_error(f"Should block non-admin: {response.status_code}")
    test_failed()

# Test 21: Access without token (should fail)
print_test("21. Access Protected Endpoint Without Token (Should Fail)")
response = requests.get(f"{BASE_URL}/users/me")
if response.status_code == 403:
    print_success(f"Correctly blocked access without token")
    test_passed()
else:
    print_error(f"Should block access without token: {response.status_code}")
    test_failed()

# Test 22: OpenAPI docs
print_test("22. OpenAPI Documentation")
response = requests.get(f"{BASE_URL}/docs")
if response.status_code == 200:
    print_success(f"Swagger UI accessible at {BASE_URL}/docs")
    test_passed()
else:
    print_error(f"Swagger UI failed: {response.status_code}")
    test_failed()

# Final summary
print(f"\n{Colors.CYAN}{'='*70}")
print("TEST SUMMARY".center(70))
print(f"{'='*70}{Colors.END}")

total_tests = test_results["passed"] + test_results["failed"]
pass_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

print(f"\n{Colors.GREEN}Passed: {test_results['passed']}/{total_tests}{Colors.END}")
print(f"{Colors.RED}Failed: {test_results['failed']}/{total_tests}{Colors.END}")
print(f"{Colors.CYAN}Success Rate: {pass_rate:.1f}%{Colors.END}")

if test_results["failed"] == 0:
    print(f"\n{Colors.GREEN}{'='*70}")
    print("🎉 ALL TESTS PASSED! 🎉".center(70))
    print(f"{'='*70}{Colors.END}\n")
else:
    print(f"\n{Colors.YELLOW}Some tests failed. Review the output above for details.{Colors.END}\n")

print_info(f"API Documentation: {BASE_URL}/docs")
print_info(f"ReDoc: {BASE_URL}/redoc")
print_info(f"User ID: {user_id}")
print_info(f"Access Token: {access_token[:50] if access_token else 'N/A'}...\n")
