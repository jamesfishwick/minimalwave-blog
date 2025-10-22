from playwright.sync_api import sync_playwright
import time

def test_blog_post_creation():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set to False to see what's happening
        page = browser.new_page()
        
        try:
            # Go to admin login
            print("1. Navigating to admin login...")
            page.goto("http://localhost:8000/admin/login/")
            
            # Login
            print("2. Logging in...")
            page.fill('input[name="username"]', 'testadmin')
            page.fill('input[name="password"]', 'testpass123')
            page.click('input[type="submit"]')
            
            # Wait for redirect to admin dashboard
            page.wait_for_url("**/admin/**")
            print("3. Login successful!")
            
            # Navigate to add entry page
            print("4. Going to add entry page...")
            page.goto("http://localhost:8000/admin/blog/entry/add/")
            
            # Fill in the form
            print("5. Filling out the blog post form...")
            page.fill('input[name="title"]', 'Test Post via Playwright')
            page.fill('input[name="slug"]', 'test-post-playwright')
            page.fill('textarea[name="summary"]', 'This is a test post created using Playwright automation')
            page.fill('textarea[name="body"]', 'This is the body content of the test post. It was created automatically using Playwright to test the admin interface.')
            
            # Set status to published
            page.select_option('select[name="status"]', 'published')
            
            # Click save
            print("6. Saving the post...")
            page.click('input[name="_save"]')
            
            # Check for success message or error
            time.sleep(2)  # Wait for page to load
            
            if "was added successfully" in page.content():
                print("7. SUCCESS: Blog post created successfully!")
                
                # Try to visit the post
                print("8. Checking if we can visit the post...")
                page.goto("http://localhost:8000/2025/jul/09/test-post-playwright/")
                
                # Check if page loads without error
                if page.title() and "500" not in page.title():
                    print("9. SUCCESS: Blog post page loads correctly!")
                    print(f"   Page title: {page.title()}")
                else:
                    print("9. ERROR: Blog post page returned an error")
                    
            elif "500 Internal Server Error" in page.content():
                print("7. ERROR: Got 500 error when saving!")
                # Try to extract error message
                error_text = page.query_selector('pre.exception_value')
                if error_text:
                    print(f"   Error: {error_text.inner_text()}")
            else:
                print("7. UNKNOWN: Unexpected response")
                
        except Exception as e:
            print(f"ERROR: {str(e)}")
            # Take a screenshot for debugging
            page.screenshot(path="error_screenshot.png")
            print("Screenshot saved as error_screenshot.png")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_blog_post_creation()