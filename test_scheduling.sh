#!/bin/bash

# This script helps test scheduled publishing functionality by creating test content
# scheduled to be published in the near future

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing scheduled publishing functionality...${NC}"

# Get the current date and time in ISO format
NOW=$(date +"%Y-%m-%d %H:%M:%S")
# Add 5 minutes for the scheduled time
SCHEDULE_TIME=$(date -v+5M +"%Y-%m-%d %H:%M:%S")

echo -e "Current time: ${GREEN}$NOW${NC}"
echo -e "Will schedule content for: ${GREEN}$SCHEDULE_TIME${NC}"

# Create a Python script to create test content
cat > /tmp/create_scheduled_content.py << EOF
"""
Create test content for scheduled publishing
"""
from django.utils import timezone
from datetime import datetime, timedelta
from blog.models import Entry, Blogmark, Tag
from django.contrib.auth.models import User

# Parse the scheduled time
scheduled_time_str = "$SCHEDULE_TIME"
scheduled_time = datetime.strptime(scheduled_time_str, "%Y-%m-%d %H:%M:%S")
scheduled_time = timezone.make_aware(scheduled_time)

# Get or create a test user
try:
    user = User.objects.get(username='testuser')
except User.DoesNotExist:
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    print("Created test user 'testuser'")

# Get or create a test tag
tag, created = Tag.objects.get_or_create(
    name='ScheduledTest',
    defaults={'slug': 'scheduledtest'}
)
if created:
    print("Created tag 'ScheduledTest'")

# Create a scheduled entry
entry = Entry.objects.create(
    title=f'Scheduled Post - Test {timezone.now().strftime("%Y-%m-%d %H:%M")}',
    summary='This is a test post scheduled for publishing.',
    body='This content was automatically scheduled for publishing using the test script.',
    status='review',
    publish_date=scheduled_time,
    slug=f'scheduled-test-{timezone.now().strftime("%Y%m%d%H%M%S")}'
)
entry.tags.add(tag)
print(f"Created scheduled entry with publish date {scheduled_time}")

# Create a scheduled blogmark
blogmark = Blogmark.objects.create(
    title=f'Scheduled Blogmark - Test {timezone.now().strftime("%Y-%m-%d %H:%M")}',
    url='https://example.com/test-scheduledpublishing',
    commentary='This is a test blogmark that was scheduled for publishing.',
    status='review',
    publish_date=scheduled_time,
    slug=f'scheduled-link-{timezone.now().strftime("%Y%m%d%H%M%S")}'
)
blogmark.tags.add(tag)
print(f"Created scheduled blogmark with publish date {scheduled_time}")

print("Test complete. Content will be published at the scheduled time.")
EOF

# Run the Python script with Django
echo -e "${YELLOW}Creating scheduled test content...${NC}"
python manage.py shell < /tmp/create_scheduled_content.py
rm /tmp/create_scheduled_content.py

echo -e "\n${GREEN}Test content created successfully!${NC}"
echo -e "The content is scheduled for publishing at ${GREEN}$SCHEDULE_TIME${NC}"
echo -e "\nTo publish immediately, run: ${YELLOW}python manage.py publish_scheduled${NC}"
echo -e "To check content status run: ${YELLOW}python manage.py shell -c \"from blog.models import Entry, Blogmark; print(f'Entries: {Entry.objects.filter(status=\\'review\\').count()}'); print(f'Blogmarks: {Blogmark.objects.filter(status=\\'review\\').count()}')\"${NC}"
