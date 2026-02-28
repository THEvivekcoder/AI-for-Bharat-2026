"""
Unit tests for Security Implementation

Tests TLS configuration, encryption/decryption, access control, and audit logging.

Feature: bharatsahayak
Requirements: 11.1, 11.2, 11.4
"""

import pytest
import ssl
import os
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import uuid

from app.security.tls_config import TLSConfig
from app.security.encryption import EncryptionService, generate_encryption_key, PII_FIELDS
from app.security.rbac import RBACService, Role, Permission, ROLE_PERMISSIONS
from app.security.audit_log import AuditLogger, AuditLog
from app.models.user import User


# ============================================================================
# TLS Configuration Tests
# ============================================================================

class TestTLSConfiguration:
    """Test TLS/HTTPS configuration"""
    
    def test_tls_config_initialization(self):
        """Test TLS config can be initialized with paths"""
        config = TLSConfig(
            cert_path="/path/to/cert.pem",
            key_path="/path/to/key.pem"
        )
        
        assert config.cert_path == "/path/to/cert.pem"
        assert config.key_path == "/path/to/key.pem"
        assert config.is_configured is True
    
    def test_tls_config_not_configured(self):
        """Test TLS config when paths not provided"""
        config = TLSConfig(cert_path=None, key_path=None)
        
        assert config.is_configured is False
    
    def test_create_ssl_context_missing_files(self):
        """Test SSL context creation fails when certificate files don't exist"""
        config = TLSConfig(
            cert_path="/nonexistent/cert.pem",
            key_path="/nonexistent/key.pem"
        )
        
        with pytest.raises(FileNotFoundError):
            config.create_ssl_context()
    
    def test_create_ssl_context_with_valid_files(self):
        """Test SSL context creation with valid certificate files"""
        # Create temporary certificate files
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = Path(tmpdir) / "cert.pem"
            key_path = Path(tmpdir) / "key.pem"
            
            # Create dummy certificate files
            cert_path.write_text("-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----")
            key_path.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----")
            
            config = TLSConfig(
                cert_path=str(cert_path),
                key_path=str(key_path)
            )
            
            # This will fail with invalid cert format, but we're testing file existence
            with pytest.raises(ssl.SSLError):
                config.create_ssl_context()
    
    def test_ssl_context_returns_none_when_not_configured(self):
        """Test SSL context returns None when TLS not configured"""
        config = TLSConfig(cert_path=None, key_path=None)
        
        context = config.create_ssl_context()
        assert context is None
    
    def test_get_uvicorn_ssl_config(self):
        """Test getting uvicorn SSL configuration"""
        config = TLSConfig(
            cert_path="/path/to/cert.pem",
            key_path="/path/to/key.pem"
        )
        
        ssl_config = config.get_uvicorn_ssl_config()
        
        assert ssl_config['ssl_keyfile'] == "/path/to/key.pem"
        assert ssl_config['ssl_certfile'] == "/path/to/cert.pem"
        assert 'ssl_version' in ssl_config
    
    def test_get_uvicorn_ssl_config_empty_when_not_configured(self):
        """Test uvicorn SSL config is empty when TLS not configured"""
        config = TLSConfig(cert_path=None, key_path=None)
        
        ssl_config = config.get_uvicorn_ssl_config()
        assert ssl_config == {}


# ============================================================================
# Encryption Tests
# ============================================================================

class TestEncryption:
    """Test encryption and decryption functionality"""
    
    def test_generate_encryption_key(self):
        """Test encryption key generation"""
        key = generate_encryption_key()
        
        assert key is not None
        assert len(key) > 0
        # Base64 encoded 32-byte key should be 44 characters
        assert len(key) == 44
    
    def test_encryption_service_initialization(self):
        """Test encryption service can be initialized with valid key"""
        key = generate_encryption_key()
        service = EncryptionService(key)
        
        assert service.key is not None
        assert len(service.key) == 32  # 256 bits
    
    def test_encryption_service_invalid_key_length(self):
        """Test encryption service fails with invalid key length"""
        import base64
        invalid_key = base64.b64encode(b"short").decode('utf-8')
        
        with pytest.raises(ValueError, match="Invalid key length"):
            EncryptionService(invalid_key)
    
    def test_encryption_service_no_key(self):
        """Test encryption service fails when no key provided"""
        with pytest.raises(ValueError, match="Encryption key not configured"):
            EncryptionService(None)
    
    def test_encrypt_decrypt_string(self):
        """Test basic string encryption and decryption"""
        key = generate_encryption_key()
        service = EncryptionService(key)
        
        plaintext = "sensitive data 123"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert encrypted != plaintext
        assert decrypted == plaintext
        assert len(encrypted) > len(plaintext)
    
    def test_encrypt_empty_string(self):
        """Test encrypting empty string"""
        key = generate_encryption_key()
        service = EncryptionService(key)
        
        encrypted = service.encrypt("")
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == ""
    
    def test_encrypt_unicode_string(self):
        """Test encrypting unicode characters"""
        key = generate_encryption_key()
        service = EncryptionService(key)
        
        plaintext = "नमस्ते भारत 🇮🇳"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_decrypt_invalid_data(self):
        """Test decrypting invalid data raises error"""
        key = generate_encryption_key()
        service = EncryptionService(key)
        
        with pytest.raises(ValueError, match="Decryption failed"):
            service.decrypt("invalid_base64_data")
    
    def test_encrypt_dict_specific_fields(self):
        """Test encrypting specific fields in dictionary"""
        key = generate_encryption_key()
        service = EncryptionService(key)
        
        data = {
            "name": "John Doe",
            "phone_number": "1234567890",
            "email": "john@example.com",
            "age": 30
        }
        
        encrypted_data = service.encrypt_dict(data, ["phone_number", "email"])
        
        assert encrypted_data["name"] == "John Doe"  # Not encrypted
        assert encrypted_data["age"] == 30  # Not encrypted
        assert encrypted_data["phone_number"] != "1234567890"  # Encrypted
        assert encrypted_data["email"] != "john@example.com"  # Encrypted
    
    def test_decrypt_dict_specific_fields(self):
        """Test decrypting specific fields in dictionary"""
        key = generate_encryption_key()
        service = EncryptionService(key)
        
        data = {
            "name": "John Doe",
            "phone_number": "1234567890",
            "email": "john@example.com"
        }
        
        encrypted_data = service.encrypt_dict(data, ["phone_number", "email"])
        decrypted_data = service.decrypt_dict(encrypted_data, ["phone_number", "email"])
        
        assert decrypted_data["phone_number"] == "1234567890"
        assert decrypted_data["email"] == "john@example.com"
        assert decrypted_data["name"] == "John Doe"
    
    def test_decrypt_dict_handles_unencrypted_fields(self):
        """Test decrypt_dict gracefully handles fields that aren't encrypted"""
        key = generate_encryption_key()
        service = EncryptionService(key)
        
        data = {
            "name": "John Doe",
            "phone_number": "1234567890"
        }
        
        # Try to decrypt without encrypting first
        decrypted_data = service.decrypt_dict(data, ["phone_number"])
        
        # Should not raise error, field remains unchanged
        assert decrypted_data["phone_number"] == "1234567890"
    
    def test_encryption_produces_different_ciphertext(self):
        """Test that encrypting same plaintext twice produces different ciphertext (due to random IV)"""
        key = generate_encryption_key()
        service = EncryptionService(key)
        
        plaintext = "test data"
        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)
        
        assert encrypted1 != encrypted2  # Different due to random IV
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext
    
    def test_pii_fields_defined(self):
        """Test that PII fields are properly defined"""
        assert 'phone_number' in PII_FIELDS
        assert 'email' in PII_FIELDS
        assert len(PII_FIELDS) > 0


# ============================================================================
# RBAC (Access Control) Tests
# ============================================================================

class TestRBAC:
    """Test Role-Based Access Control"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user"""
        user = Mock(spec=User)
        user.user_id = str(uuid.uuid4())
        user.role = "user"
        return user
    
    @pytest.fixture
    def mock_admin(self):
        """Create a mock admin"""
        admin = Mock(spec=User)
        admin.user_id = str(uuid.uuid4())
        admin.role = "admin"
        return admin
    
    @pytest.fixture
    def mock_analyst(self):
        """Create a mock analyst"""
        analyst = Mock(spec=User)
        analyst.user_id = str(uuid.uuid4())
        analyst.role = "analyst"
        return analyst
    
    def test_get_user_role(self, mock_user, mock_admin, mock_analyst):
        """Test getting user role"""
        assert RBACService.get_user_role(mock_user) == Role.USER
        assert RBACService.get_user_role(mock_admin) == Role.ADMIN
        assert RBACService.get_user_role(mock_analyst) == Role.ANALYST
    
    def test_get_user_role_defaults_to_user(self):
        """Test that invalid or missing role defaults to USER"""
        user = Mock(spec=User)
        user.user_id = str(uuid.uuid4())
        user.role = "invalid_role"
        
        assert RBACService.get_user_role(user) == Role.USER
    
    def test_get_user_role_no_role_attribute(self):
        """Test getting role when user has no role attribute"""
        user = Mock(spec=User)
        user.user_id = str(uuid.uuid4())
        delattr(user, 'role')
        
        assert RBACService.get_user_role(user) == Role.USER
    
    def test_get_role_permissions_user(self):
        """Test getting permissions for USER role"""
        permissions = RBACService.get_role_permissions(Role.USER)
        
        assert Permission.READ_OWN_PROFILE in permissions
        assert Permission.WRITE_OWN_PROFILE in permissions
        assert Permission.QUERY_SCHEMES in permissions
        assert Permission.READ_ALL_USERS not in permissions
        assert Permission.MANAGE_SCHEMES not in permissions
    
    def test_get_role_permissions_admin(self):
        """Test getting permissions for ADMIN role"""
        permissions = RBACService.get_role_permissions(Role.ADMIN)
        
        assert Permission.READ_OWN_PROFILE in permissions
        assert Permission.READ_ALL_USERS in permissions
        assert Permission.MANAGE_SCHEMES in permissions
        assert Permission.READ_ANALYTICS in permissions
        assert len(permissions) > len(RBACService.get_role_permissions(Role.USER))
    
    def test_get_role_permissions_analyst(self):
        """Test getting permissions for ANALYST role"""
        permissions = RBACService.get_role_permissions(Role.ANALYST)
        
        assert Permission.READ_ANALYTICS in permissions
        assert Permission.READ_IMPACT_METRICS in permissions
        assert Permission.EXPORT_DATA in permissions
        assert Permission.MANAGE_SCHEMES not in permissions
        assert Permission.READ_ALL_USERS not in permissions
    
    def test_has_permission_user(self, mock_user):
        """Test permission checking for regular user"""
        assert RBACService.has_permission(mock_user, Permission.READ_OWN_PROFILE) is True
        assert RBACService.has_permission(mock_user, Permission.QUERY_SCHEMES) is True
        assert RBACService.has_permission(mock_user, Permission.READ_ALL_USERS) is False
        assert RBACService.has_permission(mock_user, Permission.MANAGE_SCHEMES) is False
    
    def test_has_permission_admin(self, mock_admin):
        """Test permission checking for admin"""
        assert RBACService.has_permission(mock_admin, Permission.READ_OWN_PROFILE) is True
        assert RBACService.has_permission(mock_admin, Permission.READ_ALL_USERS) is True
        assert RBACService.has_permission(mock_admin, Permission.MANAGE_SCHEMES) is True
        assert RBACService.has_permission(mock_admin, Permission.READ_ANALYTICS) is True
    
    def test_has_permission_analyst(self, mock_analyst):
        """Test permission checking for analyst"""
        assert RBACService.has_permission(mock_analyst, Permission.READ_ANALYTICS) is True
        assert RBACService.has_permission(mock_analyst, Permission.READ_IMPACT_METRICS) is True
        assert RBACService.has_permission(mock_analyst, Permission.MANAGE_SCHEMES) is False
        assert RBACService.has_permission(mock_analyst, Permission.READ_ALL_USERS) is False
    
    def test_role_permissions_mapping_complete(self):
        """Test that all roles have permission mappings"""
        assert Role.USER in ROLE_PERMISSIONS
        assert Role.ADMIN in ROLE_PERMISSIONS
        assert Role.ANALYST in ROLE_PERMISSIONS
    
    def test_admin_has_most_permissions(self):
        """Test that admin has more permissions than other roles"""
        user_perms = len(RBACService.get_role_permissions(Role.USER))
        admin_perms = len(RBACService.get_role_permissions(Role.ADMIN))
        analyst_perms = len(RBACService.get_role_permissions(Role.ANALYST))
        
        assert admin_perms > user_perms
        assert admin_perms > analyst_perms
    
    def test_require_permission_decorator_structure(self):
        """Test that require_permission returns a callable"""
        decorator = RBACService.require_permission(Permission.READ_OWN_PROFILE)
        assert callable(decorator)
    
    def test_require_role_decorator_structure(self):
        """Test that require_role returns a callable"""
        decorator = RBACService.require_role(Role.ADMIN)
        assert callable(decorator)


# ============================================================================
# Audit Logging Tests
# ============================================================================

class TestAuditLogging:
    """Test audit logging functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db
    
    @pytest.fixture
    def audit_logger(self, mock_db):
        """Create an audit logger instance"""
        return AuditLogger(mock_db)
    
    def test_audit_logger_initialization(self, mock_db):
        """Test audit logger can be initialized"""
        logger = AuditLogger(mock_db)
        assert logger.db == mock_db
    
    def test_log_event_basic(self, audit_logger, mock_db):
        """Test logging a basic event"""
        audit_logger.log_event(
            event_type="access",
            action="read_profile",
            success=True,
            user_id="user-123"
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_log_event_with_all_fields(self, audit_logger, mock_db):
        """Test logging event with all fields"""
        audit_logger.log_event(
            event_type="access",
            action="read_user_data",
            success=True,
            user_id="user-123",
            user_role="admin",
            resource_type="user",
            resource_id="user-456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            endpoint="/api/users/456",
            metadata={"field": "value"}
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the audit log object
        call_args = mock_db.add.call_args[0]
        audit_log = call_args[0]
        
        assert isinstance(audit_log, AuditLog)
        assert audit_log.event_type == "access"
        assert audit_log.action == "read_user_data"
        assert audit_log.success == "success"
        assert audit_log.user_id == "user-123"
        assert audit_log.resource_type == "user"
    
    def test_log_event_failure(self, audit_logger, mock_db):
        """Test logging a failed event"""
        audit_logger.log_event(
            event_type="auth",
            action="login",
            success=False,
            user_id="user-123",
            error_message="Invalid credentials"
        )
        
        call_args = mock_db.add.call_args[0]
        audit_log = call_args[0]
        
        assert audit_log.success == "failure"
        assert audit_log.error_message == "Invalid credentials"
    
    def test_log_event_handles_db_error(self, audit_logger, mock_db):
        """Test that logging handles database errors gracefully"""
        mock_db.commit.side_effect = Exception("Database error")
        
        # Should not raise exception
        audit_logger.log_event(
            event_type="access",
            action="test",
            success=True
        )
        
        mock_db.rollback.assert_called_once()
    
    def test_log_data_access(self, audit_logger, mock_db):
        """Test logging data access event"""
        audit_logger.log_data_access(
            user_id="user-123",
            user_role="admin",
            resource_type="user",
            resource_id="user-456",
            action="read",
            success=True,
            ip_address="192.168.1.1",
            endpoint="/api/users/456"
        )
        
        mock_db.add.assert_called_once()
        call_args = mock_db.add.call_args[0]
        audit_log = call_args[0]
        
        assert audit_log.event_type == "access"
        assert audit_log.action == "read_user"
        assert audit_log.resource_type == "user"
        assert audit_log.resource_id == "user-456"
    
    def test_log_authentication_success(self, audit_logger, mock_db):
        """Test logging successful authentication"""
        audit_logger.log_authentication(
            user_id="user-123",
            action="login",
            success=True,
            ip_address="192.168.1.1"
        )
        
        call_args = mock_db.add.call_args[0]
        audit_log = call_args[0]
        
        assert audit_log.event_type == "auth"
        assert audit_log.action == "login"
        assert audit_log.success == "success"
        assert audit_log.user_id == "user-123"
    
    def test_log_authentication_failure(self, audit_logger, mock_db):
        """Test logging failed authentication"""
        audit_logger.log_authentication(
            user_id=None,
            action="login",
            success=False,
            ip_address="192.168.1.1",
            error_message="Invalid OTP"
        )
        
        call_args = mock_db.add.call_args[0]
        audit_log = call_args[0]
        
        assert audit_log.event_type == "auth"
        assert audit_log.success == "failure"
        assert audit_log.error_message == "Invalid OTP"
    
    def test_log_data_modification(self, audit_logger, mock_db):
        """Test logging data modification event"""
        audit_logger.log_data_modification(
            user_id="user-123",
            user_role="admin",
            resource_type="scheme",
            resource_id="scheme-456",
            action="update",
            success=True,
            metadata={"fields_changed": ["name", "description"]}
        )
        
        call_args = mock_db.add.call_args[0]
        audit_log = call_args[0]
        
        assert audit_log.event_type == "update"
        assert audit_log.action == "update_scheme"
        assert audit_log.event_metadata == {"fields_changed": ["name", "description"]}
    
    def test_log_data_deletion(self, audit_logger, mock_db):
        """Test logging data deletion event"""
        audit_logger.log_data_modification(
            user_id="user-123",
            user_role="user",
            resource_type="user",
            resource_id="user-123",
            action="delete",
            success=True
        )
        
        call_args = mock_db.add.call_args[0]
        audit_log = call_args[0]
        
        assert audit_log.event_type == "delete"
        assert audit_log.action == "delete_user"
    
    def test_audit_log_model_fields(self):
        """Test that AuditLog model has all required fields"""
        audit_log = AuditLog(
            event_type="test",
            action="test_action",
            success="success"
        )
        
        assert hasattr(audit_log, 'log_id')
        assert hasattr(audit_log, 'timestamp')
        assert hasattr(audit_log, 'user_id')
        assert hasattr(audit_log, 'user_role')
        assert hasattr(audit_log, 'event_type')
        assert hasattr(audit_log, 'resource_type')
        assert hasattr(audit_log, 'resource_id')
        assert hasattr(audit_log, 'action')
        assert hasattr(audit_log, 'ip_address')
        assert hasattr(audit_log, 'user_agent')
        assert hasattr(audit_log, 'endpoint')
        assert hasattr(audit_log, 'success')
        assert hasattr(audit_log, 'error_message')
        assert hasattr(audit_log, 'event_metadata')


# ============================================================================
# Integration Tests
# ============================================================================

class TestSecurityIntegration:
    """Test integration between security components"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db
    
    def test_encrypt_and_audit_user_data(self, mock_db):
        """Test encrypting user data and logging the access"""
        # Setup
        key = generate_encryption_key()
        encryption = EncryptionService(key)
        audit_logger = AuditLogger(mock_db)
        
        # Encrypt user data
        user_data = {
            "user_id": "user-123",
            "phone_number": "1234567890",
            "email": "user@example.com"
        }
        
        encrypted_data = encryption.encrypt_dict(user_data, ["phone_number", "email"])
        
        # Log the encryption operation
        audit_logger.log_data_modification(
            user_id="admin-1",
            user_role="admin",
            resource_type="user",
            resource_id="user-123",
            action="update",
            success=True,
            metadata={"encrypted_fields": ["phone_number", "email"]}
        )
        
        # Verify encryption worked
        assert encrypted_data["phone_number"] != "1234567890"
        assert encrypted_data["email"] != "user@example.com"
        
        # Verify audit log was created
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_rbac_check_and_audit_access(self, mock_db):
        """Test checking permissions and logging access"""
        # Setup
        audit_logger = AuditLogger(mock_db)
        
        user = Mock(spec=User)
        user.user_id = "user-123"
        user.role = "user"
        
        # Check permission
        has_perm = RBACService.has_permission(user, Permission.READ_OWN_PROFILE)
        
        # Log the access attempt
        audit_logger.log_data_access(
            user_id=user.user_id,
            user_role=user.role,
            resource_type="profile",
            resource_id=user.user_id,
            action="read",
            success=has_perm
        )
        
        assert has_perm is True
        mock_db.add.assert_called_once()
    
    def test_failed_permission_check_logged(self, mock_db):
        """Test that failed permission checks are logged"""
        audit_logger = AuditLogger(mock_db)
        
        user = Mock(spec=User)
        user.user_id = "user-123"
        user.role = "user"
        
        # Check permission that user doesn't have
        has_perm = RBACService.has_permission(user, Permission.MANAGE_SCHEMES)
        
        # Log the failed access attempt
        audit_logger.log_data_access(
            user_id=user.user_id,
            user_role=user.role,
            resource_type="schemes",
            resource_id="all",
            action="manage",
            success=has_perm
        )
        
        assert has_perm is False
        
        call_args = mock_db.add.call_args[0]
        audit_log = call_args[0]
        assert audit_log.success == "failure"
