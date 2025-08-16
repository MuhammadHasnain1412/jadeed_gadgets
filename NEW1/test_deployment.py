#!/usr/bin/env python3
"""
Quick test script to verify deployment readiness
Run this before deploying to catch common issues
"""

import os
import sys
import subprocess
from pathlib import Path

def test_requirements():
    """Test if all required packages can be installed"""
    print("🔍 Testing requirements.txt...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ All requirements can be installed")
            return True
        else:
            print(f"❌ Requirements installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing requirements: {e}")
        return False

def test_django_settings():
    """Test Django settings"""
    print("🔍 Testing Django settings...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jadeedgadgets.settings')
        import django
        django.setup()
        from django.conf import settings
        print(f"✅ Django settings loaded successfully")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        return True
    except Exception as e:
        print(f"❌ Django settings error: {e}")
        return False

def test_static_files():
    """Test static files collection"""
    print("🔍 Testing static files collection...")
    try:
        result = subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Static files collected successfully")
            return True
        else:
            print(f"❌ Static files collection failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error collecting static files: {e}")
        return False

def test_migrations():
    """Test database migrations"""
    print("🔍 Testing database migrations...")
    try:
        result = subprocess.run([sys.executable, "manage.py", "check"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Django system check passed")
            return True
        else:
            print(f"❌ Django system check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running system check: {e}")
        return False

def main():
    print("🚀 Jadeed Gadgets - Deployment Readiness Test")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    tests = [
        test_requirements,
        test_django_settings, 
        test_migrations,
        test_static_files,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Your app is ready for deployment!")
        print("\n📖 Next steps:")
        print("1. Create a GitHub repository")
        print("2. Push your code: git init && git add . && git commit -m 'Initial commit'")
        print("3. Follow the DEPLOYMENT_README.md for your chosen platform")
    else:
        print("⚠️  Please fix the failing tests before deploying")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
