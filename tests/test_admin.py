from django.test import Client
from django.contrib.auth import get_user_model
from blog.models import Entry
import datetime

# Create test client
client = Client()

# Login
User = get_user_model()
login_success = client.login(username='testadmin', password='testpass123')
print(f"Login successful: {login_success}")

# Get the add entry page
response = client.get('/admin/blog/entry/add/')
print(f"Add entry page status: {response.status_code}")

# Create a new entry via admin
form_data = {
    'title': 'Test Post via Admin',
    'slug': 'test-post-via-admin',
    'summary': 'This is a test summary',
    'body': 'This is the test body content',
    'created_0': '2025-07-09',
    'created_1': '10:00:00',
    'status': 'published',
    'is_draft': '0',
    'linkedin_enabled': '1',
    'linkedin_posted': '0',
    '_save': 'Save',
    'tags': '',
    'authorship_set-TOTAL_FORMS': '0',
    'authorship_set-INITIAL_FORMS': '0',
    'authorship_set-MIN_NUM_FORMS': '0',
    'authorship_set-MAX_NUM_FORMS': '1000',
}

# Submit the form
save_response = client.post('/admin/blog/entry/add/', form_data, follow=True)
print(f"Save response status: {save_response.status_code}")

if save_response.status_code == 200:
    if 'was added successfully' in str(save_response.content):
        print("SUCCESS: Entry saved!")
        # Check if entry was created
        entry = Entry.objects.filter(slug='test-post-via-admin').first()
        if entry:
            print(f"Entry created: {entry.title}")
            print(f"Entry URL: {entry.get_absolute_url()}")
            # Test visiting the post page
            post_response = client.get(entry.get_absolute_url())
            print(f"Post page status: {post_response.status_code}")
    else:
        print("ERROR: Save failed")
        if hasattr(save_response, 'context') and 'adminform' in save_response.context:
            print("Form errors:", save_response.context['adminform'].errors)