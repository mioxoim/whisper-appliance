#!/usr/bin/env python3
"""
Legacy Update System Cleanup Script
Removes all legacy simple-update code from main.py
"""

import re

def cleanup_main_py():
    # Read the file
    with open('src/main.py', 'r') as f:
        content = f.read()
    
    # Find the pattern from SIMPLE UPDATE ENDPOINTS to if __name__
    pattern = r'# ==================== SIMPLE UPDATE ENDPOINTS.*?(?=if __name__ == "__main__":)'
    
    # Replace with empty string
    cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Write back to file
    with open('src/main.py', 'w') as f:
        f.write(cleaned_content)
    
    print("✅ Legacy update system removed from main.py")

if __name__ == "__main__":
    cleanup_main_py()
