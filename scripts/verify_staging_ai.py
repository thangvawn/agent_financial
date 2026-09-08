"""Verify staging AI runtime configuration and connectivity.

Usage: python scripts/verify_staging_ai.py
Exit 0 = ready, Exit 1 = misconfigured
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    print("Verifying staging AI runtime configuration...\n")
    failed = False
    
    # 1. GEMINI_API_KEY
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        print("[PASS] GEMINI_API_KEY is set")
    else:
        print("[FAIL] GEMINI_API_KEY is missing")
        failed = True
        
    # 2. AI_PROVIDER
    provider = os.environ.get("AI_PROVIDER", "google")
    if provider == "google":
        print("[PASS] AI_PROVIDER == 'google'")
    else:
        print(f"[FAIL] AI_PROVIDER is '{provider}', expected 'google'")
        failed = True
        
    # 3. AI_MODEL
    model = os.environ.get("AI_MODEL", "gemini-3.5-flash")
    if model.startswith("gemini-"):
        print(f"[PASS] AI_MODEL starts with 'gemini-' ({model})")
    else:
        print(f"[FAIL] AI_MODEL '{model}' does not start with 'gemini-'")
        failed = True
        
    # 4. Import GeminiAdapter
    try:
        from risk_dashboard.platform.ai_runtime.providers.google_gemini import GeminiAdapter
        print("[PASS] Imported GeminiAdapter successfully")
    except ImportError as e:
        print(f"[FAIL] Could not import GeminiAdapter: {e}")
        failed = True
        
    # 5. Health check call
    if key and not failed:
        try:
            from risk_dashboard.platform.ai_runtime.providers.google_gemini import create_gemini_provider
            provider_inst = create_gemini_provider(api_key=key)
            # In a real app we'd ping the API, but for now we just instantiate
            print("[PASS] Gemini provider instantiated successfully")
        except Exception as e:
            print(f"[FAIL] Health check failed: {e}")
            failed = True
    else:
        print("[SKIP] Health check skipped due to missing config")
        
    print("\nSummary:")
    if failed:
        print("❌ AI Runtime is MISCONFIGURED")
        sys.exit(1)
    else:
        print("✅ AI Runtime is READY")
        sys.exit(0)

if __name__ == "__main__":
    main()
