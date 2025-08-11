#!/usr/bin/env python3
"""
Test script for proxy functionality
"""

from scraper.proxy_manager import proxy_manager
import requests
import time

def test_proxy_fetching():
    """Test fetching and validating proxies"""
    print("=" * 50)
    print("Testing Proxy Fetching and Validation")
    print("=" * 50)
    
    # Fetch proxies
    print("\n1. Fetching proxies from multiple sources...")
    proxy_manager.refresh_proxies()
    
    print(f"\nTotal working proxies found: {len(proxy_manager.working_proxies)}")
    
    # Display some working proxies
    if proxy_manager.working_proxies:
        print("\nSample working proxies:")
        for i, proxy in enumerate(proxy_manager.working_proxies[:5]):
            print(f"  {i+1}. {proxy['ip']}:{proxy['port']} ({proxy['country']}) - {proxy['source']}")

def test_proxy_usage():
    """Test using proxies for actual requests"""
    print("\n" + "=" * 50)
    print("Testing Proxy Usage")
    print("=" * 50)
    
    if not proxy_manager.working_proxies:
        print("No working proxies available. Fetching new ones...")
        proxy_manager.refresh_proxies()
    
    if proxy_manager.working_proxies:
        # Test with a few proxies
        test_url = "http://httpbin.org/ip"
        
        print(f"\nTesting with {min(3, len(proxy_manager.working_proxies))} proxies...")
        
        for i in range(min(3, len(proxy_manager.working_proxies))):
            proxy = proxy_manager.get_proxy()
            proxy_dict = proxy_manager.get_proxy_dict(proxy)
            
            print(f"\nTest {i+1}: Using proxy {proxy['ip']}:{proxy['port']}")
            
            try:
                response = requests.get(test_url, proxies=proxy_dict, timeout=10, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✓ Success! Response IP: {data.get('origin', 'Unknown')}")
                else:
                    print(f"  ✗ Failed with status code: {response.status_code}")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
            
            time.sleep(1)

def test_google_search():
    """Test proxies with Google search (what scrapers will use)"""
    print("\n" + "=" * 50)
    print("Testing Proxies with Google Search")
    print("=" * 50)
    
    if not proxy_manager.working_proxies:
        print("No working proxies available.")
        return
    
    proxy = proxy_manager.get_proxy()
    proxy_dict = proxy_manager.get_proxy_dict(proxy)
    
    print(f"\nUsing proxy: {proxy['ip']}:{proxy['port']}")
    
    search_url = "https://www.google.com/search?q=Salesforce+Agentforce"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(
            search_url, 
            proxies=proxy_dict, 
            headers=headers,
            timeout=15, 
            verify=False
        )
        
        if response.status_code == 200:
            print("  ✓ Successfully accessed Google search!")
            print(f"  Response length: {len(response.text)} characters")
        else:
            print(f"  ✗ Failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

def main():
    """Run all proxy tests"""
    print("Starting Proxy Tests...\n")
    
    # Test 1: Fetch and validate proxies
    test_proxy_fetching()
    
    # Test 2: Use proxies for requests
    test_proxy_usage()
    
    # Test 3: Test with Google (what scrapers use)
    test_google_search()
    
    print("\n" + "=" * 50)
    print("Proxy Testing Complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()