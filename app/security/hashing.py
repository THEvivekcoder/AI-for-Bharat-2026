"""Hashing utilities for searchable encrypted fields"""
import hashlib


def hash_phone_number(phone_number: str) -> str:
    """
    Create a hash of phone number for indexing/lookup
    
    Args:
        phone_number: Phone number to hash
        
    Returns:
        SHA-256 hash of phone number
    """
    return hashlib.sha256(phone_number.encode('utf-8')).hexdigest()


def hash_email(email: str) -> str:
    """
    Create a hash of email for indexing/lookup
    
    Args:
        email: Email to hash
        
    Returns:
        SHA-256 hash of email
    """
    return hashlib.sha256(email.lower().encode('utf-8')).hexdigest()


def hash_identifier(identifier: str) -> str:
    """
    Create a hash of any identifier for indexing/lookup
    
    Args:
        identifier: Identifier to hash
        
    Returns:
        SHA-256 hash of identifier
    """
    return hashlib.sha256(identifier.encode('utf-8')).hexdigest()
