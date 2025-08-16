#!/usr/bin/env python3
"""
Setup script for Groq API key configuration.
Run this script to set up your Groq API key for the JadeedBot chatbot.
"""

import os
import sys

def setup_groq_api():
    """Set up Groq API key configuration."""
    print("=== JadeedBot Groq API Setup ===")
    print("\n1. First, get your Groq API key from: https://console.groq.com/")
    print("2. Create a free account and generate an API key")
    print("3. Enter your API key below (it will be saved to your environment)")
    
    # Get API key from user
    api_key = input("\nEnter your Groq API key: ").strip()
    
    if not api_key:
        print("❌ Error: API key cannot be empty!")
        return False
    
    # Method 1: Set environment variable (recommended)
    print("\n=== Setting up environment variable ===")
    
    # For Windows
    if os.name == 'nt':
        os.system(f'setx GROQ_API_KEY "{api_key}"')
        print("✅ Environment variable set! (Windows)")
        print("⚠️  Please restart your terminal/IDE for the changes to take effect.")
    
    # For Unix/Linux/Mac
    else:
        bashrc_path = os.path.expanduser("~/.bashrc")
        with open(bashrc_path, "a") as f:
            f.write(f'\nexport GROQ_API_KEY="{api_key}"\n')
        print("✅ Environment variable added to ~/.bashrc")
        print("⚠️  Run 'source ~/.bashrc' or restart your terminal.")
    
    # Method 2: Update the views.py file directly (for development)
    print("\n=== Updating views.py for development ===")
    
    views_path = "chatbot/views.py"
    if os.path.exists(views_path):
        with open(views_path, "r") as f:
            content = f.read()
        
        # Replace the placeholder API key
        updated_content = content.replace(
            'GROQ_API_KEY = "your-groq-api-key-here"',
            f'GROQ_API_KEY = "{api_key}"'
        )
        
        with open(views_path, "w") as f:
            f.write(updated_content)
        
        print("✅ API key updated in views.py")
    else:
        print("❌ views.py not found!")
    
    print("\n=== Setup Complete! ===")
    print("🚀 You can now run the Django server and test the chatbot!")
    print("   Run: python manage.py runserver")
    print("   Visit: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    if setup_groq_api():
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)
