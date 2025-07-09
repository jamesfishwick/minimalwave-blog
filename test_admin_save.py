#!/usr/bin/env python
"""Test admin save functionality"""
import requests
import re

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "testadmin"
PASSWORD = "testpass123"

# Start a session
session = requests.Session()

# Get the login page to get CSRF token
login_page = session.get(f"{BASE_URL}/admin/login/")
csrf_token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text).group(1)

# Login
login_data = {
    'username': USERNAME,
    'password': PASSWORD,
    'csrfmiddlewaretoken': csrf_token,
    'next': '/admin/'
}
login_response = session.post(f"{BASE_URL}/admin/login/", data=login_data)
print(f"Login status: {login_response.status_code}")

# Get the add entry page
add_entry_page = session.get(f"{BASE_URL}/admin/blog/entry/add/")
print(f"Add entry page status: {add_entry_page.status_code}")

if add_entry_page.status_code == 200:
    # Extract CSRF token from add page
    csrf_token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', add_entry_page.text).group(1)
    
    # Prepare form data for a new entry
    form_data = {
        'csrfmiddlewaretoken': csrf_token,
        'title': 'Test Post from Script',
        'slug': 'test-post-from-script',
        'summary': 'This is a test summary',
        'body': 'This is the test body content',
        'created_0': '2025-07-09',
        'created_1': '10:00:00',
        'status': 'published',
        'is_draft': '0',
        'linkedin_enabled': '1',
        'linkedin_posted': '0',
        '_save': 'Save',
        # M2M fields need special handling
        'tags': '',
        'authorship_set-TOTAL_FORMS': '1',
        'authorship_set-INITIAL_FORMS': '0',
        'authorship_set-MIN_NUM_FORMS': '0',
        'authorship_set-MAX_NUM_FORMS': '1000',
        'authorship_set-0-id': '',
        'authorship_set-0-entry': '',
        'authorship_set-0-author': '',
        'authorship_set-0-DELETE': '',
    }
    
    # Submit the form
    save_response = session.post(f"{BASE_URL}/admin/blog/entry/add/", data=form_data)
    print(f"Save response status: {save_response.status_code}")
    
    if save_response.status_code == 500:
        print("ERROR: Got 500 error on save!")
        # Try to extract error message
        if 'Traceback' in save_response.text:
            traceback_start = save_response.text.find('Traceback')
            traceback_end = save_response.text.find('</pre>', traceback_start)
            if traceback_end > traceback_start:
                print("\nTraceback:")
                print(save_response.text[traceback_start:traceback_end])
    elif save_response.status_code == 302:
        print("SUCCESS: Entry saved successfully!")
        print(f"Redirect to: {save_response.headers.get('Location')}")
    else:
        print(f"Unexpected response: {save_response.status_code}")
else:
    print("Failed to access add entry page!")