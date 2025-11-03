# Minimalwave Blog - Project Overview

## Purpose
A Django-based personal blog inspired by Simon Willison's website, featuring a dark mode minimal wave aesthetic. The blog supports multiple content types with scheduled publishing, markdown editing, and social media integration.

## Core Features
- **Blog Posts (Entry)**: Full-length posts with markdown support, syntax highlighting, and reading time estimates
- **Link Blog (Blogmarks)**: Share and comment on external links
- **TIL (Today I Learned)**: Short-form content organized by topic
- **Unified Tagging**: Shared tag system across all content types
- **Content Workflow**: Draft → Review → Published status with preview functionality
- **Scheduled Publishing**: Automatic content publishing via cron/management command
- **Social Media**: Auto-generated Open Graph and Twitter Card metadata
- **Search**: Full-text search across all content types
- **Atom Feeds**: Separate feeds for blog and TIL sections

## Tech Stack
- **Framework**: Django 5.2 (Python 3.10+)
- **Database**: PostgreSQL (development and production)
- **Caching**: Redis (production)
- **Static Files**: WhiteNoise with manifest storage
- **Markdown**: markdown + pygments for syntax highlighting
- **Extended Apps**: django-taggit, django-markdownx, django-allauth
- **Deployment**: Docker + Azure App Service
- **Storage**: Azure Blob Storage (django-storages[azure])
- **WSGI Server**: Gunicorn (production)

## Architecture
- **Multi-app Django structure**: blog/, til/, core/, linkedin/ apps
- **Modular settings**: base.py, development.py, production.py, ci.py
- **Abstract base models**: BaseEntry provides common fields (title, slug, status, scheduling)
- **Date-based URLs**: `/<year>/<month>/<day>/<slug>/`
- **Preview system**: `/preview/entry/<slug>/` for draft/review content (auth required)