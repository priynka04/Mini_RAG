"""
Quick script to list available Gemini models.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.google_api_key)

print("\nAvailable Gemini models:")
print("="*60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"\nModel: {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Description: {model.description}")
        print(f"  Supported methods: {model.supported_generation_methods}")

print("\n" + "="*60)