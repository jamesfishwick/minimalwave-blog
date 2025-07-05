# Utility Scripts

This directory contains utility scripts for managing and testing the Minimal Wave Blog.

## Scripts

### `test_scheduling.sh`
Creates test content scheduled for publishing in 5 minutes. Useful for testing the scheduled publishing functionality.

**Usage:**
```bash
./scripts/test_scheduling.sh
# or via Makefile
make test-schedule
```

### `setup_scheduled_publishing.sh`
Sets up a cron job to run the `publish_scheduled` management command every hour. This enables automatic publishing of scheduled content.

**Usage:**
```bash
./scripts/setup_scheduled_publishing.sh
# or via Makefile
make crontab
```

### `run_tests.py`
Alternative test runner script that can run tests directly without using `manage.py test`.

**Usage:**
```bash
python scripts/run_tests.py
```

## Notes

- The shell scripts require execution permissions (`chmod +x`)
- The cron job setup script creates a `logs/` directory if it doesn't exist
- Test scheduling creates content with the tag "ScheduledTest" for easy identification