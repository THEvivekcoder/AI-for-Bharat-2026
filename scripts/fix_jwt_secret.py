#!/usr/bin/env python3
"""Fix JWT_SECRET references in template.yaml to use parameter instead of Secrets Manager."""

import re

# Read template
with open('template.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Secrets Manager references with parameter reference
old_pattern = r"JWT_SECRET: !Sub '\{\{resolve:secretsmanager:bharatsahayak-jwt-secret-\$\{Environment\}:SecretString:jwt_secret\}\}'"
new_value = "JWT_SECRET: !Ref JWTSecret"

updated_content = re.sub(old_pattern, new_value, content)

# Count replacements
count = content.count("resolve:secretsmanager:bharatsahayak-jwt-secret")

# Write back
with open('template.yaml', 'w', encoding='utf-8') as f:
    f.write(updated_content)

print(f"✅ Replaced {count} JWT_SECRET references")
print(f"✅ template.yaml updated to use parameter instead of Secrets Manager")
