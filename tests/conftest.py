"""Shared test configuration and fixtures."""

import os
import sys

# Ensure project root is on sys.path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
