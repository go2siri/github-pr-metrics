#!/usr/bin/env python3
"""
Test script to validate the backend structure and imports
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all backend modules can be imported"""
    print("🧪 Testing backend module imports...")
    
    try:
        print("  📦 Testing backend.models...")
        from backend.models import (
            AnalysisRequest, AnalysisResponse, TaskStatus,
            DeveloperMetrics, RepositoryMetrics
        )
        print("  ✅ backend.models imported successfully")
        
        print("  📦 Testing existing modules...")
        from github_client import GitHubClient
        from pr_analyzer import PRAnalyzer
        print("  ✅ Existing modules imported successfully")
        
        print("  📦 Testing backend.services...")
        from backend.services import AnalysisService, analysis_service
        print("  ✅ backend.services imported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_validation():
    """Test Pydantic model validation"""
    print("\n🔍 Testing model validation...")
    
    try:
        from backend.models import AnalysisRequest
        
        # Test valid request
        valid_request = AnalysisRequest(
            owner="octocat",
            repo="Hello-World", 
            github_token="ghp_1234567890123456789012345678901234567890"
        )
        print("  ✅ Valid request model created successfully")
        
        # Test GitHub URL parsing
        url_request = AnalysisRequest(
            github_url="https://github.com/octocat/Hello-World",
            github_token="ghp_1234567890123456789012345678901234567890"
        )
        print(f"  ✅ URL parsed: owner={url_request.owner}, repo={url_request.repo}")
        
        # Test validation errors
        try:
            invalid_request = AnalysisRequest(
                owner="",
                repo="test",
                github_token="short"
            )
            print("  ❌ Should have failed validation")
            return False
        except Exception:
            print("  ✅ Validation errors caught correctly")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Model validation failed: {e}")
        return False

def test_service_creation():
    """Test service initialization"""
    print("\n⚙️ Testing service creation...")
    
    try:
        from backend.services import AnalysisService
        
        service = AnalysisService()
        print(f"  ✅ Service created with {len(service.tasks)} tasks")
        print(f"  ✅ Service has executor with {service.executor._max_workers} workers")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Service creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 GitHub PR Metrics Analyzer Backend Tests")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Model Validation", test_model_validation), 
        ("Service Creation", test_service_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
        if not passed:
            all_passed = False
    
    print(f"\n🏁 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Backend is ready! You can now:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Start the server: python run_backend.py")
        print("  3. Visit API docs: http://localhost:8000/docs")
        print("  4. Test with: python backend/example_usage.py")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)