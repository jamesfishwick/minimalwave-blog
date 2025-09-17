#!/bin/bash

echo "=== Diagnosing Production Migration Issue ==="

# Wait for deployment
echo "1. Waiting for deployment to complete..."
sleep 60

echo "2. Downloading latest logs..."
az webapp log download --resource-group minimalwave-blog-rg --name minimalwave-blog --log-file .claude-sandbox/prod_diagnosis.zip

echo "3. Extracting logs..."
unzip -q .claude-sandbox/prod_diagnosis.zip -d .claude-sandbox/prod_diagnosis/

echo "4. Checking for migration errors..."
grep -A20 -B5 "migrations\|migrate" .claude-sandbox/prod_diagnosis/LogFiles/*docker.log | tail -50

echo "5. Checking for model mismatch errors..."
grep -A5 "Your models in app" .claude-sandbox/prod_diagnosis/LogFiles/*docker.log | tail -20

echo "6. Restarting the app to force migration..."
az webapp restart --resource-group minimalwave-blog-rg --name minimalwave-blog

echo "7. Waiting for restart..."
sleep 30

echo "8. Testing admin access..."
curl -I https://jamesfishwick.com/admin/ | grep "HTTP\|500"

echo "=== Diagnosis Complete ==="