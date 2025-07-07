#!/usr/bin/env python3
"""
Debug script to test update system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.update import UpdateManager

# Test update manager
print("Testing Update System...")
update_manager = UpdateManager()

print("\n1. Checking for updates...")
result = update_manager.check_for_updates()
print(f"Update available: {result['update_available']}")
print(f"Current version: {result['current_version']}")
print(f"Latest version: {result['latest_version']}")

print("\n2. Getting status...")
status = update_manager.get_status()
print(f"Repo path: {status['repo_path']}")
print(f"Backups: {status['backups']}")

print("\nUpdate system test completed!")
