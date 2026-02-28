#!/usr/bin/env python3
"""Generate self-signed certificates for development/testing"""
import os
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta


def generate_self_signed_cert(
    cert_dir: str = "certs",
    days_valid: int = 365,
    key_size: int = 2048
):
    """
    Generate self-signed certificate for development
    
    Args:
        cert_dir: Directory to store certificates
        days_valid: Number of days certificate is valid
        key_size: RSA key size in bits
    """
    # Create certs directory
    cert_path = Path(cert_dir)
    cert_path.mkdir(exist_ok=True)
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    
    # Generate certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Maharashtra"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Mumbai"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "BharatSahayak"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=days_valid)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("127.0.0.1"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Write private key
    key_file = cert_path / "key.pem"
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Write certificate
    cert_file = cert_path / "cert.pem"
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print(f"✓ Generated self-signed certificate")
    print(f"  Certificate: {cert_file}")
    print(f"  Private Key: {key_file}")
    print(f"  Valid for: {days_valid} days")
    print(f"\nTo use with uvicorn:")
    print(f"  uvicorn app.main:app --ssl-keyfile={key_file} --ssl-certfile={cert_file}")
    print(f"\nOr add to .env:")
    print(f"  TLS_CERT_PATH={cert_file}")
    print(f"  TLS_KEY_PATH={key_file}")


if __name__ == "__main__":
    generate_self_signed_cert()
