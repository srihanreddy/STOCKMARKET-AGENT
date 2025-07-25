import requests
import sys
import json
from datetime import datetime

class StockMarketAPITester:
    def __init__(self, base_url="https://3030ffac-5aab-46d6-8951-e2c8807dde4b.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:500]}...")

            return success, response.json() if response.status_code == expected_status else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root endpoint"""
        return self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )

    def test_trending_stocks(self):
        """Test trending stocks endpoint"""
        success, response = self.run_test(
            "Trending Stocks",
            "GET",
            "api/market/trending",
            200
        )
        
        if success and 'trending_stocks' in response:
            stocks = response['trending_stocks']
            print(f"   Found {len(stocks)} trending stocks")
            if stocks:
                print(f"   Sample stock: {stocks[0].get('symbol', 'N/A')} - ${stocks[0].get('price', 'N/A')}")
        
        return success, response

    def test_stock_data(self, symbol="AAPL"):
        """Test stock chart data endpoint"""
        success, response = self.run_test(
            f"Stock Data for {symbol}",
            "GET",
            f"api/stock/{symbol}/data",
            200
        )
        
        if success and 'data' in response:
            data_points = response['data']
            print(f"   Found {len(data_points)} data points")
            if data_points:
                latest = data_points[-1]
                print(f"   Latest price: ${latest.get('close', 'N/A')} on {latest.get('date', 'N/A')}")
        
        return success, response

    def test_stock_analysis(self, symbol="AAPL"):
        """Test stock analysis endpoint"""
        success, response = self.run_test(
            f"Stock Analysis for {symbol}",
            "POST",
            "api/analyze",
            200,
            data={"symbol": symbol, "timeframe": "1y"},
            timeout=60  # AI analysis might take longer
        )
        
        if success:
            print(f"   Analysis length: {len(response.get('analysis', ''))}")
            print(f"   Risk level: {response.get('risk_level', 'N/A')}")
            print(f"   Confidence score: {response.get('confidence_score', 'N/A')}")
            print(f"   Recommendations: {len(response.get('recommendations', []))}")
        
        return success, response

    def test_ai_chat(self, symbol="AAPL", query="What is the current outlook for this stock?"):
        """Test AI chat endpoint"""
        success, response = self.run_test(
            f"AI Chat for {symbol}",
            "POST",
            "api/chat",
            200,
            data={"symbol": symbol, "query": query},
            timeout=60  # AI chat might take longer
        )
        
        if success:
            print(f"   Chat response length: {len(response.get('analysis', ''))}")
            print(f"   Risk level: {response.get('risk_level', 'N/A')}")
            print(f"   Recommendations: {len(response.get('recommendations', []))}")
        
        return success, response

    def test_multiple_stocks(self):
        """Test multiple stock symbols"""
        test_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        successful_stocks = 0
        
        print(f"\n🔍 Testing multiple stock symbols...")
        for symbol in test_symbols:
            success, _ = self.run_test(
                f"Stock Data for {symbol}",
                "GET",
                f"api/stock/{symbol}/data",
                200,
                timeout=15
            )
            if success:
                successful_stocks += 1
        
        print(f"   Successfully retrieved data for {successful_stocks}/{len(test_symbols)} stocks")
        return successful_stocks == len(test_symbols)

def main():
    print("🚀 Starting AI Stock Market Agent API Tests")
    print("=" * 60)
    
    # Setup
    tester = StockMarketAPITester()
    
    # Test sequence
    print("\n📋 Running API endpoint tests...")
    
    # 1. Test root endpoint
    tester.test_root_endpoint()
    
    # 2. Test trending stocks
    tester.test_trending_stocks()
    
    # 3. Test stock data
    tester.test_stock_data("AAPL")
    
    # 4. Test stock analysis (this might take longer due to AI processing)
    print("\n⚠️  Note: AI analysis tests may take 30-60 seconds...")
    tester.test_stock_analysis("AAPL")
    
    # 5. Test AI chat
    tester.test_ai_chat("AAPL", "Should I buy this stock now?")
    
    # 6. Test multiple stocks
    tester.test_multiple_stocks()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())