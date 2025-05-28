# Todo List for Minimal Wave Blog Implementation

## Project Setup
- [x] Install required packages
- [x] Create Django project structure
- [x] Create blog and til apps
- [x] Configure project settings

## Core Models
- [x] Implement Tag model
- [x] Implement BaseEntry abstract model
- [x] Implement Entry model for blog posts
- [x] Implement Blogmark model for link blog
- [x] Implement TIL model
- [x] Implement Authorship model

## Admin Interfaces
- [x] Configure admin for blog models
- [x] Configure admin for TIL models

## Views and URLs
- [x] Implement blog views (index, entry, blogmark, archive, tag, search)
- [x] Implement TIL views (index, detail, tag, search)
- [x] Configure URL patterns for blog app
- [x] Configure URL patterns for TIL app
- [x] Configure main URL patterns

## Templates
- [x] Create base template with dark mode and minimal wave aesthetics
- [x] Create blog templates (index, entry, blogmark, archive, tag, search)
- [x] Create TIL templates (index, detail, tag, search)

## Additional Functionality
- [x] Create default social media card image
- [x] Implement custom context processor for common template variables
- [x] Add pagination for index and archive pages
- [x] Implement related posts functionality
- [x] Add reading time estimation
- [x] Implement enhanced draft/preview system
- [x] Add scheduled publishing functionality
- [x] Create management command for scheduled publishing

## Testing
- [x] Test blog post creation and display
- [x] Test blogmark creation and display
- [x] Test TIL creation and display
- [x] Test tag filtering
- [x] Test search functionality
- [x] Test Atom feeds
- [x] Test responsive design
- [x] Create script for testing scheduled publishing

## Docker & Deployment
- [x] Configure Docker with Poetry
- [x] Create Docker Compose for development and production
- [x] Set up Supervisor for process management
- [x] Create GitHub Actions workflow for CI/CD
- [x] Create Azure deployment documentation
- [x] Create deployment checklist

## Remaining Tasks
- [ ] Test complete Azure deployment process
- [ ] Set up monitoring and alerting
- [ ] Create backup strategy
- [ ] Implement performance optimizations
- [ ] Set up SSL certificate for production
