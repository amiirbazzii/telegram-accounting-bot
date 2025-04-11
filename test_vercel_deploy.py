#!/usr/bin/env python3
# test_vercel_deploy.py - Test file for verifying Vercel deployment readiness

import os
import json
import logging
from dotenv import load_dotenv
import requests

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_env_variables():
    """Check if all required environment variables are set."""
    print("\n=== Checking Environment Variables ===")
    
    required_vars = {
        "BOT_TOKEN": "Telegram Bot Token",
        "SPREADSHEET_ID": "Google Spreadsheet ID",
        "GOOGLE_APPLICATION_CREDENTIALS": "Google Service Account Credentials"
    }
    
    optional_vars = {
        "GOOGLE_SHEET_NAME": "Google Sheet Name (default: 'Expenses')",
        "CUSTOM_DOMAIN": "Custom Domain for Vercel deployment"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: Missing - {description}")
        else:
            masked_value = value[:5] + "..." + value[-5:] if len(value) > 10 else "***"
            print(f"✅ {var}: Set - {description} ({masked_value})")
    
    print("\n=== Optional Variables ===")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if not value:
            print(f"⚠️ {var}: Not set - {description}")
        else:
            print(f"✅ {var}: Set - {description} ({value})")
    
    return len(missing_vars) == 0

def check_google_credentials():
    """Check if Google credentials are valid."""
    print("\n=== Checking Google Credentials ===")
    
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    # Check if it's a file path or JSON content
    if os.path.exists(creds_path):
        try:
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
            print(f"✅ Successfully loaded credentials from file: {creds_path}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in credentials file: {creds_path}")
            return False
        except Exception as e:
            print(f"❌ Error reading credentials file: {e}")
            return False
    else:
        # Try parsing as JSON string
        try:
            if '{' in creds_path and '}' in creds_path:
                creds_data = json.loads(creds_path)
                print("✅ Successfully parsed credentials JSON from environment variable")
            else:
                print(f"❌ Credentials path not found and doesn't look like JSON: {creds_path}")
                return False
        except json.JSONDecodeError:
            print("❌ Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS environment variable")
            return False
    
    # Check for required fields in credentials
    required_fields = ["type", "project_id", "private_key", "client_email"]
    missing_fields = [field for field in required_fields if field not in creds_data]
    
    if missing_fields:
        print(f"❌ Missing fields in credentials: {', '.join(missing_fields)}")
        return False
    
    print(f"✅ Credentials contain all required fields")
    print(f"  - Project ID: {creds_data.get('project_id')}")
    print(f"  - Client Email: {creds_data.get('client_email')}")
    
    return True

def check_vercel_config():
    """Verify Vercel configuration file."""
    print("\n=== Checking Vercel Configuration ===")
    
    try:
        with open('vercel.json', 'r') as f:
            config = json.load(f)
        print("✅ vercel.json exists and is valid JSON")
        
        # Check for required sections
        required_sections = ["version", "builds", "routes"]
        missing_sections = [section for section in required_sections if section not in config]
        
        if missing_sections:
            print(f"❌ Missing sections in vercel.json: {', '.join(missing_sections)}")
            return False
        
        print("✅ vercel.json contains all required sections")
        
        # Check build configuration
        if "builds" in config and len(config["builds"]) > 0:
            build = config["builds"][0]
            if "src" in build and "use" in build:
                print(f"✅ Build configuration looks good:")
                print(f"  - Source: {build['src']}")
                print(f"  - Builder: {build['use']}")
                
                if "config" in build and "buildCommand" in build["config"]:
                    print(f"  - Build Command: {build['config']['buildCommand']}")
            else:
                print("❌ Build configuration is missing src or use fields")
        
        # Check routes
        if "routes" in config and len(config["routes"]) > 0:
            print(f"✅ {len(config['routes'])} route(s) configured")
        
        return True
        
    except FileNotFoundError:
        print("❌ vercel.json not found")
        return False
    except json.JSONDecodeError:
        print("❌ vercel.json contains invalid JSON")
        return False
    except Exception as e:
        print(f"❌ Error checking vercel.json: {e}")
        return False

def check_required_files():
    """Check if all required files exist."""
    print("\n=== Checking Required Files ===")
    
    required_files = {
        "main.py": "Main application file",
        "requirements.txt": "Python dependencies",
        "build.sh": "Build script for Vercel",
        "vercel.json": "Vercel configuration"
    }
    
    all_present = True
    for file, description in required_files.items():
        if os.path.exists(file):
            print(f"✅ {file}: Found - {description}")
        else:
            print(f"❌ {file}: Missing - {description}")
            all_present = False
    
    return all_present

def check_telegram_bot():
    """Check if Telegram bot token is valid."""
    print("\n=== Checking Telegram Bot ===")
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN not set")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        data = response.json()
        
        if response.status_code == 200 and data.get("ok"):
            bot_info = data.get("result", {})
            print(f"✅ Bot token is valid")
            print(f"  - Bot username: @{bot_info.get('username')}")
            print(f"  - Bot name: {bot_info.get('first_name')}")
            if bot_info.get('username'):
                print(f"  - Link: https://t.me/{bot_info.get('username')}")
            return True
        else:
            print(f"❌ Invalid bot token: {data.get('description', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error checking bot token: {e}")
        return False

def main():
    """Run all checks."""
    print("=== Vercel Deployment Readiness Test ===")
    
    checks = [
        ("Environment Variables", check_env_variables),
        ("Google Credentials", check_google_credentials),
        ("Vercel Configuration", check_vercel_config),
        ("Required Files", check_required_files),
        ("Telegram Bot", check_telegram_bot)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error during {name} check: {e}")
            results[name] = False
    
    # Summary
    print("\n=== Deployment Readiness Summary ===")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nPassed {passed}/{total} checks")
    
    if passed == total:
        print("\n🚀 Your application is ready for Vercel deployment!")
    else:
        print("\n⚠️ Please fix the issues above before deploying to Vercel.")

if __name__ == "__main__":
    main() 