#!/usr/bin/env python3
"""
Test script to verify the evaluation system works end-to-end
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.google_api import GoogleAPIHandler
from src.evaluator import DocumentEvaluator

def test_config():
    """Test configuration"""
    print("=" * 60)
    print("Testing Configuration...")
    print("=" * 60)
    try:
        Config.validate()
        print("✅ Configuration is valid")
        print(f"   - AI Provider: {Config.AI_PROVIDER}")
        print(f"   - Spreadsheet ID: {Config.SPREADSHEET_ID[:20]}...")
        print(f"   - Max Workers: {Config.MAX_WORKERS}")
        return True
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        return False

def test_google_api():
    """Test Google API connection"""
    print("\n" + "=" * 60)
    print("Testing Google API Connection...")
    print("=" * 60)
    try:
        api = GoogleAPIHandler()
        print("✅ Google API Handler initialized")
        
        # Test reading sheet
        range_name = f"{Config.DOC_LINK_COLUMN}2:{Config.STUDENT_NAME_COLUMN}3"
        rows = api.read_sheet_rows(range_name)
        print(f"✅ Successfully read {len(rows)} rows from sheet")
        
        if rows and len(rows) > 0:
            doc_url = rows[0][0] if len(rows[0]) > 0 else ""
            if doc_url:
                doc_id = api.extract_doc_id(doc_url)
                if doc_id:
                    print(f"✅ Successfully extracted doc ID: {doc_id[:20]}...")
                else:
                    print("⚠️ Warning: Could not extract doc ID from URL")
        
        return True
    except Exception as e:
        print(f"❌ Google API Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_evaluator():
    """Test evaluator initialization"""
    print("\n" + "=" * 60)
    print("Testing Evaluator...")
    print("=" * 60)
    try:
        evaluator = DocumentEvaluator()
        print("✅ Evaluator initialized successfully")
        print(f"   - AI Provider: {evaluator.ai_provider}")
        print(f"   - Use JSON Mode: {evaluator.use_json_mode}")
        
        # Test with sample text
        sample_text = """
        CREATE TABLE students (
            id INT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE
        );
        
        INSERT INTO students VALUES (1, 'John Doe', 'john@example.com');
        
        SELECT * FROM students WHERE id = 1;
        """
        
        print("\n   Testing evaluation with sample text...")
        result = evaluator.evaluate(sample_text, "Test Student")
        print(f"✅ Evaluation successful")
        print(f"   - Total Score: {result.get('total_score', 'N/A')}")
        print(f"   - Breakdown: {result.get('breakdown', {})}")
        
        return True
    except Exception as e:
        print(f"❌ Evaluator Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "🔥" * 30)
    print("AAG - System Diagnostics")
    print("🔥" * 30 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_config()))
    results.append(("Google API", test_google_api()))
    results.append(("Evaluator", test_evaluator()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready to evaluate documents.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please fix the issues above before running evaluation.")
        return 1

if __name__ == "__main__":
    exit(main())
