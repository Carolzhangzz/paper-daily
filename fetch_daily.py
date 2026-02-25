#!/usr/bin/env python3
"""Standalone fetch script for launchd / cron."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import init_db, do_fetch

if __name__ == "__main__":
    init_db()
    do_fetch()
