# list_my_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API key from your .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in environment variables or .env file.")
    print("Please ensure your .env file is set up correctly.")
    exit(1) # Exit if no key found

try:
    # Configure the SDK with your API key
    genai.configure(api_key=api_key)

    print("Available Gemini Models accessible by your API key:\n")

    # List the models
    # The list_models() function returns an iterator
    for model in genai.list_models():
        # Check if the model supports the 'generateContent' method used by the app
        if 'generateContent' in model.supported_generation_methods:
            print(f"--- Model: {model.name} ---")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
            print(f"  Supports 'generateContent': Yes")
            print("-" * (len(model.name) + 14)) # Separator line
        else:
            # Optionally show models that *don't* support generateContent
            # print(f"--- Model (Does NOT support generateContent): {model.name} ---")
            # print(f"  Display Name: {model.display_name}")
            # print(f"  Supported Methods: {model.supported_generation_methods}")
            # print("-" * (len(model.name) + 45))
            pass # Or just ignore them if you only care about usable ones

    print("\nRecommendation: Use one of the models listed above that supports 'generateContent'.")
    print("Update the GEMINI_MODEL_NAME in your .env file accordingly.")
    print("Common choices include 'models/gemini-1.5-pro-latest' or 'models/gemini-pro'.")


except Exception as e:
    print(f"\nAn error occurred while trying to list models:")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Details: {e}")
    print("\nPlease check your API key, internet connection, and permissions in Google AI Studio / Cloud Console.")
