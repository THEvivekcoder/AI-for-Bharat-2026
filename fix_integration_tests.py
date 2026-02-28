#!/usr/bin/env python3
"""
Script to fix test_integration_e2e.py by replacing TestingSessionLocal() with test_db parameter
"""

import re

# Read the file
with open('.kiro/specs/bharatsahayak/tests/test_integration_e2e.py', 'r') as f:
    content = f.read()

# Pattern 1: Replace setup_database parameter with test_db in function signatures
content = re.sub(
    r'(def test_\w+\([^)]*),\s*setup_database([^)]*\))',
    r'\1, test_db\2',
    content
)

# Pattern 2: Replace db = TestingSessionLocal() with using test_db directly
# We need to be careful here - we'll replace the pattern and then fix the subsequent db. references

# Find all occurrences of "db = TestingSessionLocal()"
lines = content.split('\n')
new_lines = []
skip_next_close = False

for i, line in enumerate(lines):
    if 'db = TestingSessionLocal()' in line:
        # Skip this line - we'll use test_db parameter instead
        continue
    elif 'db.close()' in line and i > 0:
        # Check if this is a standalone db.close() that should be removed
        # (when it's after a TestingSessionLocal() usage)
        prev_lines = '\n'.join(lines[max(0, i-20):i])
        if 'TestingSessionLocal()' in prev_lines:
            continue
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# Write back
with open('.kiro/specs/bharatsahayak/tests/test_integration_e2e.py', 'w') as f:
    f.write(content)

print("✓ Fixed test_integration_e2e.py")
print("  - Replaced setup_database with test_db in function signatures")
print("  - Removed TestingSessionLocal() calls")
print("  - Removed standalone db.close() calls")
