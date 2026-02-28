#!/usr/bin/env python3
"""Generate encryption key for AES-256"""
from app.security.encryption import generate_encryption_key


def main():
    """Generate and display encryption key"""
    key = generate_encryption_key()
    
    print("=" * 60)
    print("AES-256 Encryption Key Generated")
    print("=" * 60)
    print(f"\nEncryption Key: {key}")
    print(f"\nAdd this to your .env file:")
    print(f"ENCRYPTION_KEY={key}")
    print("\n⚠️  IMPORTANT: Keep this key secure and never commit it to version control!")
    print("=" * 60)


if __name__ == "__main__":
    main()
