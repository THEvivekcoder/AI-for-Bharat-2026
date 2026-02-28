#!/usr/bin/env python3
"""Test security implementation"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.security.encryption import EncryptionService, generate_encryption_key
from app.security.hashing import hash_phone_number, hash_email
from app.security.rbac import RBACService, Role, Permission
from app.models.user import User


def test_encryption():
    """Test encryption functionality"""
    print("\n" + "="*60)
    print("Testing Encryption")
    print("="*60)
    
    # Generate test key
    key = generate_encryption_key()
    print(f"✓ Generated encryption key: {key[:20]}...")
    
    # Create encryption service
    encryption = EncryptionService(key)
    print("✓ Created encryption service")
    
    # Test string encryption
    plaintext = "1234567890"
    encrypted = encryption.encrypt(plaintext)
    decrypted = encryption.decrypt(encrypted)
    
    print(f"  Plaintext: {plaintext}")
    print(f"  Encrypted: {encrypted[:40]}...")
    print(f"  Decrypted: {decrypted}")
    
    assert plaintext == decrypted, "Decryption failed"
    assert encrypted != plaintext, "Encryption didn't change data"
    print("✓ String encryption/decryption works")
    
    # Test dictionary encryption
    data = {
        "name": "John Doe",
        "phone": "1234567890",
        "email": "john@example.com"
    }
    
    encrypted_data = encryption.encrypt_dict(data, ["phone", "email"])
    print(f"\n  Original: {data}")
    print(f"  Encrypted: phone={encrypted_data['phone'][:30]}...")
    
    decrypted_data = encryption.decrypt_dict(encrypted_data, ["phone", "email"])
    print(f"  Decrypted: {decrypted_data}")
    
    assert decrypted_data["phone"] == data["phone"], "Dict decryption failed"
    print("✓ Dictionary encryption/decryption works")
    
    # Test empty string
    empty_encrypted = encryption.encrypt("")
    empty_decrypted = encryption.decrypt(empty_encrypted)
    assert empty_decrypted == "", "Empty string handling failed"
    print("✓ Empty string handling works")
    
    print("\n✅ All encryption tests passed!")


def test_hashing():
    """Test hashing functionality"""
    print("\n" + "="*60)
    print("Testing Hashing")
    print("="*60)
    
    # Test phone number hashing
    phone = "1234567890"
    hash1 = hash_phone_number(phone)
    hash2 = hash_phone_number(phone)
    
    print(f"  Phone: {phone}")
    print(f"  Hash: {hash1}")
    
    assert hash1 == hash2, "Hashing not deterministic"
    assert len(hash1) == 64, "Hash length incorrect"
    print("✓ Phone number hashing works")
    
    # Test email hashing
    email = "test@example.com"
    email_hash = hash_email(email)
    email_hash_upper = hash_email("TEST@EXAMPLE.COM")
    
    print(f"\n  Email: {email}")
    print(f"  Hash: {email_hash}")
    
    assert email_hash == email_hash_upper, "Email hashing not case-insensitive"
    print("✓ Email hashing works (case-insensitive)")
    
    # Test different inputs produce different hashes
    phone2 = "9876543210"
    hash3 = hash_phone_number(phone2)
    assert hash1 != hash3, "Different inputs produced same hash"
    print("✓ Different inputs produce different hashes")
    
    print("\n✅ All hashing tests passed!")


def test_rbac():
    """Test RBAC functionality"""
    print("\n" + "="*60)
    print("Testing RBAC")
    print("="*60)
    
    # Create mock users
    class MockUser:
        def __init__(self, user_id, role):
            self.user_id = user_id
            self.role = role
    
    user = MockUser("user-1", "user")
    admin = MockUser("admin-1", "admin")
    analyst = MockUser("analyst-1", "analyst")
    
    # Test role detection
    user_role = RBACService.get_user_role(user)
    admin_role = RBACService.get_user_role(admin)
    analyst_role = RBACService.get_user_role(analyst)
    
    print(f"  User role: {user_role}")
    print(f"  Admin role: {admin_role}")
    print(f"  Analyst role: {analyst_role}")
    
    assert user_role == Role.USER, "User role detection failed"
    assert admin_role == Role.ADMIN, "Admin role detection failed"
    assert analyst_role == Role.ANALYST, "Analyst role detection failed"
    print("✓ Role detection works")
    
    # Test user permissions
    print("\n  Testing USER permissions:")
    assert RBACService.has_permission(user, Permission.READ_OWN_PROFILE), "User should read own profile"
    assert RBACService.has_permission(user, Permission.QUERY_SCHEMES), "User should query schemes"
    assert not RBACService.has_permission(user, Permission.READ_ALL_USERS), "User shouldn't read all users"
    assert not RBACService.has_permission(user, Permission.READ_ANALYTICS), "User shouldn't read analytics"
    print("    ✓ User has correct permissions")
    
    # Test admin permissions
    print("\n  Testing ADMIN permissions:")
    assert RBACService.has_permission(admin, Permission.READ_OWN_PROFILE), "Admin should read own profile"
    assert RBACService.has_permission(admin, Permission.READ_ALL_USERS), "Admin should read all users"
    assert RBACService.has_permission(admin, Permission.MANAGE_SCHEMES), "Admin should manage schemes"
    assert RBACService.has_permission(admin, Permission.READ_ANALYTICS), "Admin should read analytics"
    print("    ✓ Admin has correct permissions")
    
    # Test analyst permissions
    print("\n  Testing ANALYST permissions:")
    assert RBACService.has_permission(analyst, Permission.READ_OWN_PROFILE), "Analyst should read own profile"
    assert RBACService.has_permission(analyst, Permission.READ_ANALYTICS), "Analyst should read analytics"
    assert not RBACService.has_permission(analyst, Permission.READ_ALL_USERS), "Analyst shouldn't read all users"
    assert not RBACService.has_permission(analyst, Permission.MANAGE_SCHEMES), "Analyst shouldn't manage schemes"
    print("    ✓ Analyst has correct permissions")
    
    # Test permission lists
    user_perms = RBACService.get_role_permissions(Role.USER)
    admin_perms = RBACService.get_role_permissions(Role.ADMIN)
    analyst_perms = RBACService.get_role_permissions(Role.ANALYST)
    
    print(f"\n  User permissions: {len(user_perms)}")
    print(f"  Admin permissions: {len(admin_perms)}")
    print(f"  Analyst permissions: {len(analyst_perms)}")
    
    assert len(admin_perms) > len(user_perms), "Admin should have more permissions than user"
    assert len(admin_perms) > len(analyst_perms), "Admin should have more permissions than analyst"
    print("✓ Permission counts correct")
    
    print("\n✅ All RBAC tests passed!")


def test_integration():
    """Test integration scenarios"""
    print("\n" + "="*60)
    print("Testing Integration Scenarios")
    print("="*60)
    
    # Scenario: User registration with encryption
    print("\n  Scenario: User registration with encrypted phone")
    
    key = generate_encryption_key()
    encryption = EncryptionService(key)
    
    phone = "9876543210"
    encrypted_phone = encryption.encrypt(phone)
    phone_hash = hash_phone_number(phone)
    
    print(f"    Original phone: {phone}")
    print(f"    Encrypted: {encrypted_phone[:40]}...")
    print(f"    Hash: {phone_hash[:16]}...")
    
    # Simulate lookup by hash
    stored_hash = phone_hash
    lookup_hash = hash_phone_number(phone)
    
    assert stored_hash == lookup_hash, "Hash lookup failed"
    print("    ✓ Can lookup user by phone hash")
    
    # Decrypt for display
    decrypted_phone = encryption.decrypt(encrypted_phone)
    assert decrypted_phone == phone, "Phone decryption failed"
    print("    ✓ Can decrypt phone for display")
    
    print("\n✅ All integration tests passed!")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BharatSahayak Security Implementation Tests")
    print("="*60)
    
    try:
        test_encryption()
        test_hashing()
        test_rbac()
        test_integration()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSecurity implementation is working correctly.")
        print("\nNext steps:")
        print("1. Generate encryption key: python scripts/generate_encryption_key.py")
        print("2. Add ENCRYPTION_KEY to .env")
        print("3. Run database migrations: alembic upgrade head")
        print("4. (Optional) Generate TLS certificates: python scripts/generate_self_signed_cert.py")
        print("5. (Optional) Enable TLS in .env: TLS_ENABLED=true")
        
        return 0
    
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
