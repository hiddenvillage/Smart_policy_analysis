"""
Test script to verify async implementation works correctly
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insurance_project.settings')

import django
django.setup()

from insurance_project.api.tasks import process_interpretation_async

async def test_async_task():
    """Test the async task function"""
    print("Testing async task implementation...")
    
    # Test data
    task_id = "TEST_20250112_0001"
    task_name = "Test Task"
    company = "Test Company"
    scene = "Test Scene"
    pdf_path = None
    png_paths = []
    
    try:
        # Run the async task
        result = await process_interpretation_async(
            task_id=task_id,
            task_name=task_name,
            company=company,
            scene=scene,
            pdf_path=pdf_path,
            png_paths=png_paths
        )
        
        print(f"✓ Task completed successfully!")
        print(f"  Task ID: {result.get('task_id')}")
        print(f"  Processing time: {result.get('processing_time')}")
        print(f"  Confidence score: {result.get('confidence_score')}")
        return True
        
    except Exception as e:
        print(f"✗ Task failed with error: {e}")
        return False

def run_test():
    """Run the test"""
    print("=" * 60)
    print("Testing Async Implementation (without Celery)")
    print("=" * 60)
    
    # Run the async test
    success = asyncio.run(test_async_task())
    
    print("=" * 60)
    if success:
        print("✓ All tests passed! Async implementation is working correctly.")
    else:
        print("✗ Test failed. Please check the implementation.")
    print("=" * 60)

if __name__ == "__main__":
    run_test()