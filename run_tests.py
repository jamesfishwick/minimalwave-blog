#!/usr/bin/env python
"""
Script to run tests for the Minimal Wave Blog project
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'minimalwave-blog.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["blog", "til"])
    sys.exit(bool(failures))
