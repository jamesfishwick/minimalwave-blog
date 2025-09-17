#!/bin/bash

echo "=== Testing Blog Post Creation Flow ==="

# Clean up from previous runs
rm -f cookies.txt add_entry.html save_result.html post_page.html

# 1. Get login page and CSRF token
echo "1. Getting login page..."
CSRF_LOGIN=$(curl -s -c cookies.txt http://localhost:8000/admin/login/ | grep 'csrfmiddlewaretoken' | head -1 | sed 's/.*value="\([^"]*\)".*/\1/')
echo "   CSRF Token: ${CSRF_LOGIN:0:20}..."

# 2. Login
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -s -b cookies.txt -c cookies.txt -X POST http://localhost:8000/admin/login/ \
  -d "username=testadmin&password=testpass123&csrfmiddlewaretoken=$CSRF_LOGIN&next=/admin/" \
  -w "%{http_code}" -o /dev/null)
echo "   Login response: $LOGIN_RESPONSE"

# 3. Get add entry page
echo "3. Getting add entry page..."
curl -s -b cookies.txt http://localhost:8000/admin/blog/entry/add/ -o add_entry.html
if grep -q "500 Internal Server Error" add_entry.html; then
    echo "   ERROR: Add entry page returned 500!"
    grep -A 5 "exception_value" add_entry.html
    exit 1
fi
echo "   Add entry page loaded successfully"

# 4. Extract CSRF token from form
CSRF_FORM=$(grep 'name="csrfmiddlewaretoken"' add_entry.html | head -1 | sed 's/.*value="\([^"]*\)".*/\1/')
echo "4. Form CSRF Token: ${CSRF_FORM:0:20}..."

# 5. Submit new blog post
echo "5. Creating new blog post..."
TIMESTAMP=$(date +%s)
SAVE_RESPONSE=$(curl -s -b cookies.txt -c cookies.txt -X POST http://localhost:8000/admin/blog/entry/add/ \
  -F "csrfmiddlewaretoken=$CSRF_FORM" \
  -F "title=Test Blog Post $TIMESTAMP" \
  -F "slug=test-blog-post-$TIMESTAMP" \
  -F "summary=This is a test summary for blog post $TIMESTAMP" \
  -F "body=This is the main content of the test blog post. Created at timestamp $TIMESTAMP to test the saving functionality." \
  -F "created_0=2025-07-09" \
  -F "created_1=11:00:00" \
  -F "status=published" \
  -F "is_draft=0" \
  -F "linkedin_enabled=1" \
  -F "linkedin_posted=0" \
  -F "authorship_set-TOTAL_FORMS=0" \
  -F "authorship_set-INITIAL_FORMS=0" \
  -F "authorship_set-MIN_NUM_FORMS=0" \
  -F "authorship_set-MAX_NUM_FORMS=1000" \
  -F "_save=Save" \
  -w "%{http_code}" -o save_result.html)

echo "   Save response code: $SAVE_RESPONSE"

if [ "$SAVE_RESPONSE" = "302" ]; then
    echo "   SUCCESS: Blog post saved (got redirect)"
    
    # 6. Check if post exists in database
    echo "6. Verifying post in database..."
    docker-compose exec -T web python manage.py shell << EOF
from blog.models import Entry
entry = Entry.objects.filter(slug='test-blog-post-$TIMESTAMP').first()
if entry:
    print(f"   Entry found: {entry.title}")
    print(f"   Status: {entry.status}")
    print(f"   URL: {entry.get_absolute_url()}")
else:
    print("   ERROR: Entry not found in database!")
EOF

    # 7. Try to visit the blog post page
    echo "7. Visiting the blog post page..."
    POST_URL="http://localhost:8000/2025/jul/09/test-blog-post-$TIMESTAMP/"
    POST_RESPONSE=$(curl -s -b cookies.txt "$POST_URL" -w "%{http_code}" -o post_page.html)
    echo "   Post page response: $POST_RESPONSE"
    
    if [ "$POST_RESPONSE" = "200" ]; then
        if grep -q "Test Blog Post $TIMESTAMP" post_page.html; then
            echo "   SUCCESS: Blog post page displays correctly!"
        else
            echo "   ERROR: Blog post page loaded but content not found"
        fi
    else
        echo "   ERROR: Blog post page returned status $POST_RESPONSE"
        if grep -q "500 Internal Server Error" post_page.html; then
            echo "   Found 500 error on post page"
            grep -A 5 "exception_value" post_page.html
        fi
    fi
    
elif [ "$SAVE_RESPONSE" = "200" ]; then
    echo "   ERROR: Got 200 response (form redisplayed, likely validation error)"
    # Check for form errors
    grep -E "(errorlist|field-error)" save_result.html | head -5
    
elif [ "$SAVE_RESPONSE" = "500" ]; then
    echo "   ERROR: Got 500 error when saving!"
    grep -A 10 "exception_value" save_result.html | head -20
else
    echo "   ERROR: Unexpected response code $SAVE_RESPONSE"
fi

echo "=== Test Complete ==="