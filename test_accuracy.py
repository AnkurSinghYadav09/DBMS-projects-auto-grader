#!/usr/bin/env python3
"""Quick test script to verify scoring consistency with improved prompt"""

from src.config import Config
from src.google_api import GoogleAPIHandler
from src.evaluator import DocumentEvaluator
import time

def main():
    print("🧪 Testing Accuracy-Focused Prompt (3 runs)")
    print("=" * 60)
    
    api = GoogleAPIHandler()
    evaluator = DocumentEvaluator()
    
    # Get first 2 documents
    rows = api.read_sheet_rows('A2:B3')
    
    if len(rows) < 2:
        print("❌ Need at least 2 documents in sheet")
        return
    
    results = {1: [], 2: []}
    
    for run in range(1, 4):
        print(f"\n📊 Run {run}/3")
        print("-" * 60)
        
        for idx, row in enumerate(rows, 1):
            doc_link = row[0] if row else ''
            student_name = row[1] if len(row) > 1 else f'Student {idx}'
            
            if not doc_link:
                continue
                
            print(f"  Evaluating: {student_name[:30]}")
            
            try:
                # Extract document ID
                if '/d/' in doc_link:
                    doc_id = doc_link.split('/d/')[1].split('/')[0]
                else:
                    doc_id = doc_link
                
                # Get document text
                text = api.extract_doc_text(doc_id)
                
                if not text:
                    print(f"    ⚠️  Empty document")
                    continue
                
                # Evaluate
                result = evaluator.evaluate(text, student_name)
                score = result.get('total_score', 0)
                results[idx].append(score)
                
                print(f"    ✅ Score: {score}")
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:50]}")
        
        if run < 3:
            time.sleep(2)  # Small delay between runs
    
    # Analysis
    print("\n" + "=" * 60)
    print("📈 CONSISTENCY ANALYSIS")
    print("=" * 60)
    
    for doc_num, scores in results.items():
        if not scores:
            continue
        
        min_score = min(scores)
        max_score = max(scores)
        variance = max_score - min_score
        avg_score = sum(scores) / len(scores)
        
        status = "✅ PASS" if variance <= 5 else "❌ FAIL"
        
        print(f"\nDocument {doc_num}:")
        print(f"  Scores: {scores}")
        print(f"  Average: {avg_score:.1f}")
        print(f"  Variance: {variance} points {status}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
