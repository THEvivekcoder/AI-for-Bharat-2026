#!/usr/bin/env python3
"""
Quick script to disable rate limiting for demo
Run this before demo to ensure smooth experience
"""

import re
from pathlib import Path

def disable_rate_limiting():
    """Comment out rate limiting middleware in app/main.py"""
    
    main_py = Path("app/main.py")
    
    if not main_py.exists():
        print("❌ app/main.py not found")
        return False
    
    content = main_py.read_text()
    
    # Check if already disabled
    if "# RATE LIMITING DISABLED FOR DEMO" in content:
        print("✓ Rate limiting already disabled")
        return True
    
    # Find and comment out rate limiting middleware
    patterns = [
        (r'app\.add_middleware\(RateLimitMiddleware\)', 
         '# RATE LIMITING DISABLED FOR DEMO\n# app.add_middleware(RateLimitMiddleware)'),
        (r'from app\.middleware\.rate_limiter import',
         '# from app.middleware.rate_limiter import'),
    ]
    
    modified = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
    
    if modified:
        # Backup original
        backup = main_py.with_suffix('.py.backup')
        backup.write_text(main_py.read_text())
        print(f"✓ Backed up to {backup}")
        
        # Write modified
        main_py.write_text(content)
        print("✓ Rate limiting disabled in app/main.py")
        print("\n⚠️  RESTART THE SERVER for changes to take effect:")
        print("   uvicorn app.main:app --reload")
        return True
    else:
        print("⚠️  Could not find rate limiting middleware to disable")
        print("   You may need to manually comment it out in app/main.py")
        return False

def restore_rate_limiting():
    """Restore rate limiting from backup"""
    
    main_py = Path("app/main.py")
    backup = main_py.with_suffix('.py.backup')
    
    if backup.exists():
        main_py.write_text(backup.read_text())
        backup.unlink()
        print("✓ Rate limiting restored from backup")
        print("\n⚠️  RESTART THE SERVER for changes to take effect")
        return True
    else:
        print("❌ No backup found")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_rate_limiting()
    else:
        print("🎙️  Disabling Rate Limiting for Demo\n")
        disable_rate_limiting()
        print("\n💡 To restore later, run:")
        print("   python scripts/disable_rate_limiting_for_demo.py restore")
