"""
Test script for Python SDK
Tests the updated SDK with only supported parameters
"""

from serpex_sdk import SerpexClient
import time

API_KEY = 'sk_test_dummy_api_key_for_testing_only'
BASE_URL = 'http://localhost:3002'


def test_search():
    print('🧪 Testing Python SDK v2.1.0\n')
    
    client = SerpexClient(api_key=API_KEY, base_url=BASE_URL)


    try:
        # Test 1: Basic search with minimal parameters
        print('Test 1: Basic search with minimal parameters')
        result1 = client.search({'q': 'Python programming'})
        print('✅ Test 1 passed')
        print(f'   Query: {result1.query}')
        print(f'   Results: {len(result1.results)}')
        print(f'   Credits used: {result1.metadata.credits_used}')
        print(f'   Response time: {result1.metadata.response_time}ms\n')
        
        # Wait a bit between requests
        time.sleep(2)

        # Test 2: Search with all supported parameters
        print('Test 2: Search with all supported parameters')
        result2 = client.search({
            'q': 'JavaScript tutorial',
            'engine': 'google',
            'category': 'web',
            'time_range': 'week',
            'format': 'json'
        })
        print('✅ Test 2 passed')
        print(f'   Query: {result2.query}')
        print(f'   Engine: {result2.engines[0]}')
        print(f'   Results: {len(result2.results)}')
        print(f'   Credits used: {result2.metadata.credits_used}\n')
        
        time.sleep(2)

        # Test 3: Different engine
        print('Test 3: Search with different engine (Brave)')
        result3 = client.search({
            'q': 'TypeScript frameworks',
            'engine': 'brave',
            'category': 'web',
            'time_range': 'month'
        })
        print('✅ Test 3 passed')
        print(f'   Query: {result3.query}')
        print(f'   Results: {len(result3.results)}')
        print(f'   Credits used: {result3.metadata.credits_used}\n')
        
        time.sleep(2)

        # Test 4: Time range filter
        print('Test 4: Search with time range filter')
        result4 = client.search({
            'q': 'Machine learning news',
            'engine': 'google',
            'category': 'web',
            'time_range': 'day'
        })
        print('✅ Test 4 passed')
        print(f'   Query: {result4.query}')
        print(f'   Results: {len(result4.results)}')
        print(f'   Time range: day\n')

        print('🎉 All tests passed successfully!')

    except Exception as error:
        print(f'❌ Test failed: {error}')
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)


if __name__ == '__main__':
    test_search()
