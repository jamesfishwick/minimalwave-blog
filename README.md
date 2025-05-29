# Minimal Wave Blog

A Django-based personal blog inspired by Simon Willison's website (simonwillison.net), featuring a dark mode minimal wave aesthetic.

## Features

* **Blog Posts:** Create and manage blog posts with title, summary, body, publication date, and draft/live status.
* **Link Blog (Blogmarks):** Share and comment on external links, similar to Simon Willison's "blogmarks".
* **TIL (Today I Learned):** A dedicated section for short-form content, organized by topic.
* **Tagging:** Organize all content (posts, links, TILs) using tags.
* **Markdown Support:** Write content using Markdown with syntax highlighting.
* **Search:** Full-text search across blog posts, links, and TILs.
* **Archives:** Browse content by year and month.
* **Atom Feeds:** Separate Atom feeds for the main blog and the TIL section.
* **Social Media Cards:** Automatic generation of social media card metadata (Open Graph and Twitter Cards) for enhanced link sharing.
* **Dark Mode:** A visually appealing dark mode theme with minimal wave aesthetics (neon text, grid patterns).
* **Responsive Design:** Adapts to different screen sizes (desktop, mobile).
* **Reading Time:** Estimated reading time displayed for blog posts and TILs.
* **Related Posts:** Suggests related blog posts based on shared tags.
* **Pagination:** Paginated index and archive pages.
* **Content Management:**
  * **Draft/Review System:** Enhanced content workflow with draft, review, and published states.
  * **Preview Functionality:** Preview draft and review content with visual indicators.
  * **Scheduled Publishing:** Schedule content to be published automatically at a future date and time.
* **Docker Support:** Production-ready Docker and Docker Compose configurations.
* **Azure Deployment:** Ready-to-use GitHub Actions workflow for Azure deployment.

## Local Development Setup

There are two ways to run the blog locally: using a Python virtual environment or using Docker.

### Option 1: Using Python Virtual Environment (venv)

1. **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd minimalwave-blog
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    All subsequent commands assume you're in the root directory (where `manage.py` is located).

4. **Apply database migrations:**

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5. **Create a superuser account:**

    ```bash
    python manage.py createsuperuser
    ```

    (Follow the prompts to set up your admin username and password)

6. **Run the development server:**

    ```bash
    python manage.py runserver
    ```

7. **Access the blog:** Open your web browser and go to `http://127.0.0.1:8000/`
8. **Access the admin interface:** Go to `http://127.0.0.1:8000/admin/` and log in with your superuser credentials to create content.

### Option 2: Using Docker with Docker Compose

1. **Ensure Docker and Docker Compose are installed and running.**
2. **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd minimalwave-blog
    ```

3. **Development Environment:**

    ```bash
    # Start the development environment
    docker-compose up -d

    # Or use the Makefile
    make dev
    ```

4. **Production Environment:**

    ```bash
    # Create a .env file with your production settings (see .env.sample)
    cp .env.sample .env
    # Edit .env with your production values

    # Start the production environment
    docker-compose -f docker-compose.prod.yml up -d

    # Or use the Makefile
    make prod
    ```

5. **Access the blog:** Open your web browser and go to `http://localhost:8000/`
6. **Access the admin interface:** Go to `http://localhost:8000/admin/` and log in with your superuser credentials to create content.

    *Note: This runs the container in the foreground. Use `-d` for detached mode.*

    **Alternatively, run with Docker Compose (recommended):**

    ```bash
    docker-compose up web
    ```

    Open your browser at <http://localhost:8000/>

    *Use `-d` flag to run in detached mode.*

7. **Apply database migrations and create superuser (first time only):**
    * Open another terminal window.
    * Execute the following commands:

        ```bash
        docker-compose exec web python manage.py makemigrations
        docker-compose exec web python manage.py migrate
        docker-compose exec web python manage.py createsuperuser
        ```

        (Follow the prompts to set up your admin username and password)

8. **Access the blog:** Open your web browser and go to `http://localhost:8000/` or `http://127.0.0.1:8000/`
9. **Access the admin interface:** Go to `http://localhost:8000/admin/` and log in with your superuser credentials.

10. **To stop the container:**

    ```bash
    docker-compose down  # Stops and removes containers but preserves volumes
    ```

11. **To remove the container:**

    ```bash
    docker rm minimalwave-blog-container
    ```

## Running Tests

To run the test suite:

```bash
pytest
```

## Deployment

This project is configured for deployment to Azure App Service. See the `azure_deployment_guide.md` file for detailed instructions.

## Project Structure

* `minimalwave-blog/`: Main Django project directory.
  * `settings/`: Contains development and production settings.
  * `static/`: Static files (CSS, images).
  * `templates/`: Base HTML templates.
* `blog/`: Django app for core blog posts and blogmarks.
* `til/`: Django app for the "Today I Learned" section.
* `manage.py`: Django management script.
* `requirements.txt`: Python dependencies.
* `Dockerfile`: For building the Docker image.
* `azure_deployment_guide.md`: Instructions for Azure deployment.

## Advanced Features

### Content Status Management

The blog features an enhanced content workflow system with the following status options:

1. **Draft:** Private content that's still being written. Only visible to logged-in users with the preview link.
2. **Review:** Content ready for review but not yet published. Only visible to logged-in users with the preview link.
3. **Published:** Content that's publicly available to all visitors.

### Scheduled Publishing

You can schedule content to be published automatically at a future date and time:

1. In the admin interface, set the content status to "Draft" or "Review"
2. Set the "publish_date" field to the desired future publication date and time
3. Save the content

The scheduled content will automatically change to "Published" status when the publish date arrives if you've set up one of these methods:

#### Method 1: Using the Management Command

Run the `publish_scheduled` management command manually or on a schedule:

```bash
# Run manually
python manage.py publish_scheduled

# Or with the Makefile
make publish
```

#### Method 2: Setting up a Cron Job (recommended for production)

The provided script sets up a cron job to run the publish_scheduled command hourly:

```bash
# Make the script executable (one-time setup)
chmod +x setup_scheduled_publishing.sh

# Run the setup script
./setup_scheduled_publishing.sh

# Or with the Makefile
make crontab
```

#### Method 3: In Docker Production Environment

The production Docker setup includes automatic scheduled publishing through a cron service that runs in the background with Supervisor.

### Testing Scheduled Publishing

To test the scheduled publishing functionality:

```bash
# Run the test script
./test_scheduling.sh

# Or with the Makefile
make test-schedule
```

This will:

* Create a test blog entry scheduled to publish in 5 minutes
* Create a test blogmark scheduled to publish in 5 minutes
* Tag both with the "ScheduledTest" tag

After running the test, you can:

* Wait for the scheduled time to pass and verify the content is published automatically
* Run `python manage.py publish_scheduled` to publish immediately

### Makefile Support

A Makefile is included to make common development tasks easier:

```bash
# Show available commands
make help

# Run the development server
make run

# Start development environment with Docker
make dev

# Start production environment with Docker
make prod

# Format code and templates
make format

# Run tests
make test
```
