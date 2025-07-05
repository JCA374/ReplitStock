# test/run_tests.py - Simple test runner

import os
import sys
import subprocess
from datetime import datetime


def setup_test_environment():
    """Setup the test environment"""
    print("🔧 Setting up test environment...")

    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    print(f"📁 Project root: {project_root}")
    print(f"📁 Test directory: {script_dir}")

    # Change to project root for imports to work
    os.chdir(project_root)

    return project_root, script_dir


def run_data_retrieval_test():
    """Run the main data retrieval test"""
    print("\n🚀 Running Data Retrieval Test...")
    print("=" * 50)

    try:
        # Add the test directory to Python path
        test_dir = os.path.dirname(os.path.abspath(__file__))
        if test_dir not in sys.path:
            sys.path.insert(0, test_dir)

        # Import directly from the file
        import test_data_retrieval

        tester = test_data_retrieval.DataRetrievalTester()
        tester.run_all_tests()
        tester.test_specific_pe_issue()

        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure you run this from the project root directory")
        print(f"💡 Current working directory: {os.getcwd()}")
        print(
            f"💡 Script directory: {os.path.dirname(os.path.abspath(__file__))}")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        print(f"💡 Full traceback: {traceback.format_exc()}")
        return False


def run_quick_pe_test():
    """Run a quick P/E specific test"""
    print("\n⚡ Quick P/E Test...")
    print("-" * 30)

    try:
        import yfinance as yf

        # Test a few known stocks
        test_stocks = ['AAPL', 'MSFT', 'GOOGL']

        for ticker in test_stocks:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                pe_ratio = info.get('trailingPE') or info.get('forwardPE')
                market_cap = info.get('marketCap')

                print(f"📊 {ticker}:")
                print(f"   P/E Ratio: {pe_ratio}")
                print(f"   Market Cap: {market_cap}")
                print(f"   Available keys: {len(info)} fields")

                # Check if P/E related fields exist
                pe_fields = [k for k in info.keys() if 'pe' in k.lower(
                ) or 'price' in k.lower() and 'earn' in k.lower()]
                if pe_fields:
                    print(f"   P/E related fields: {pe_fields}")
                print()

            except Exception as e:
                print(f"❌ Error testing {ticker}: {e}")

        return True

    except ImportError:
        print("❌ yfinance not available")
        return False
    except Exception as e:
        print(f"❌ Quick test error: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are available"""
    print("\n🔍 Checking Dependencies...")

    required_modules = [
        'yfinance',
        'pandas',
        'sqlalchemy',
        'alpha_vantage'
    ]

    missing = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
            missing.append(module)

    if missing:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing)}")
        print("💡 Install with: pip install " + " ".join(missing))
        return False

    return True


def main():
    """Main test runner"""
    print("🧪 Stock Analysis Test Suite")
    print("=" * 40)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Setup environment
    project_root, test_dir = setup_test_environment()

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot run tests due to missing dependencies")
        return 1

    # Run quick PE test first
    print("\n" + "=" * 50)
    pe_success = run_quick_pe_test()

    # Run comprehensive test
    print("\n" + "=" * 50)
    full_success = run_data_retrieval_test()

    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)

    if pe_success:
        print("✅ Quick P/E Test: PASSED")
    else:
        print("❌ Quick P/E Test: FAILED")

    if full_success:
        print("✅ Full Data Test: PASSED")
    else:
        print("❌ Full Data Test: FAILED")

    print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if pe_success and full_success:
        print("🎉 All tests completed successfully!")
        return 0
    else:
        print("⚠️ Some tests failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
