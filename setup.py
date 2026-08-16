#!/usr/bin/env python3
"""
Setup script for Order & Payment Application
Creates .env file with user-provided credentials
"""

import os
import sys

def setup_environment():
    print("=== Order & Payment Application Setup ===\n")
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/n): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    print("Please provide the following configuration:\n")
    
    # Get configuration values
    secret_key = input("Secret Key (press Enter for random): ").strip()
    if not secret_key:
        import secrets
        secret_key = secrets.token_hex(32)
    
    database_url = input("Database URL (press Enter for default SQLite): ").strip()
    if not database_url:
        database_url = "sqlite:///orders.db"
    
    upi_id = input("UPI ID (e.g., mobile@upi): ").strip()
    while not upi_id:
        print("❌ UPI ID is required!")
        upi_id = input("UPI ID (e.g., mobile@upi): ").strip()
    
    payee_name = input("Payee Name (Your Business/Personal Name): ").strip()
    while not payee_name:
        print("❌ Payee Name is required!")
        payee_name = input("Payee Name (Your Business/Personal Name): ").strip()
    
    flask_env = input("Flask Environment (development/production) [development]: ").strip()
    if not flask_env:
        flask_env = "development"
    
    # Write .env file
    env_content = f"""SECRET_KEY={secret_key}
DATABASE_URL={database_url}
UPI_ID={upi_id}
PAYEE_NAME={payee_name}
FLASK_ENV={flask_env}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n✅ .env file created successfully!")
        print("\n📝 Configuration Summary:")
        print(f"   Secret Key: {'*' * len(secret_key)}")
        print(f"   Database: {database_url}")
        print(f"   UPI ID: {upi_id}")
        print(f"   Payee Name: {payee_name}")
        print(f"   Environment: {flask_env}")
        print("\n🚀 You can now run the application with: python app.py")
        
    except Exception as e:
        print(f"\n❌ Error creating .env file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_environment()
