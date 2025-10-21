"""
Simple test for Python SDK v2.1.0
Tests the SDK with supported parameters
"""

from serpex_sdk import SerpexClient

API_KEY = 'sk_50d69d9ba447b7425cfdc6084ef60bafa169e3d1db68c5285f2b8f724d683fa0'
BASE_URL = 'http://localhost:3002'


def main():
    print('🧪 Testing Python SDK v2.1.0\n')
    
    # Initialize client
    client = SerpexClient(api_key=API_KEY, base_url=BASE_URL)

    try:
        # Single comprehensive test with minimal query
        print('Testing search with supported parameters:')
        print('  - q: "python"')
        print('  - engine: "google"')
        print('  - category: "web"')
        print('  - time_range: "all"')
        print('  - format: "json"\n')
        
        result = client.search({
            'q': 'python',
            'engine': 'google',
            'category': 'web',
            'time_range': 'all',
            'format': 'json'
        })
        
        print('✅ Test passed!')
        print(f'\n📊 Results:')
        print(f'   Query: {result.query}')
        print(f'   Engines: {result.engines}')
        print(f'   Results count: {len(result.results)}')
        print(f'   Credits used: {result.metadata.credits_used}')
        print(f'   Response time: {result.metadata.response_time}ms')
        
        # Show first result as sample
        if result.results:
            print(f'\n📄 Sample result:')
            first = result.results[0]
            print(f'   Title: {first.title}')
            print(f'   URL: {first.url}')
            if hasattr(first, 'snippet') and first.snippet:
                snippet = first.snippet[:100] + '...' if len(first.snippet) > 100 else first.snippet
                print(f'   Snippet: {snippet}')
        
        print('\n✅ Python SDK is working correctly!')
        
    except Exception as error:
        print(f'❌ Test failed: {error}')
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)


if __name__ == '__main__':
    main()
