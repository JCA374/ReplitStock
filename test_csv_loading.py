"""
Simple test to verify CSV loading without dependencies
"""
import pandas as pd
from pathlib import Path

def test_csv_loading():
    """Test that CSV files can be loaded with new format"""

    csv_dir = Path("data/csv")
    csv_files = {
        'large_cap': csv_dir / "updated_large.csv",
        'mid_cap': csv_dir / "updated_mid.csv",
        'small_cap': csv_dir / "updated_small.csv"
    }

    all_stocks = []

    for category, csv_path in csv_files.items():
        if not csv_path.exists():
            print(f"ERROR: CSV file not found: {csv_path}")
            continue

        try:
            df = pd.read_csv(csv_path)

            # Normalize column names (handle different formats)
            df.columns = df.columns.str.strip().str.lower()

            print(f"\n{category} - Columns found: {list(df.columns)}")

            # Extract relevant columns (updated CSV format)
            # CSV columns: tickersymbol, yahooticker, yahooexchange, companyname
            if 'yahooticker' in df.columns:
                ticker_col = 'yahooticker'  # Already has .ST suffix
            elif 'ticker' in df.columns:
                ticker_col = 'ticker'
            elif 'symbol' in df.columns:
                ticker_col = 'symbol'
            elif 'tickersymbol' in df.columns:
                ticker_col = 'tickersymbol'
            else:
                print(f"ERROR: No ticker column found in {csv_path}")
                continue

            # Get company name
            if 'companyname' in df.columns:
                name_col = 'companyname'
            elif 'name' in df.columns:
                name_col = 'name'
            elif 'company' in df.columns:
                name_col = 'company'
            else:
                name_col = None

            # Create standardized dataframe
            stock_df = pd.DataFrame({
                'ticker': df[ticker_col].str.strip(),
                'name': df[name_col].fillna('') if name_col else '',
                'sector': (df['sector'].fillna('Unknown') if 'sector' in df.columns
                          else df['gics sector'].fillna('Unknown') if 'gics sector' in df.columns
                          else 'Unknown'),
                'csv_category': category
            })

            all_stocks.append(stock_df)

            print(f"Loaded {len(stock_df)} stocks from {category}")
            print(f"Sample tickers: {stock_df['ticker'].head(3).tolist()}")

        except Exception as e:
            print(f"ERROR loading {csv_path}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if not all_stocks:
        print("\nERROR: No stocks loaded!")
        return False

    # Combine all stocks
    universe = pd.concat(all_stocks, ignore_index=True)

    # Remove duplicates (keep first occurrence)
    universe = universe.drop_duplicates(subset=['ticker'], keep='first')

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total universe: {len(universe)} stocks")
    print(f"\nBreakdown by category:")
    print(universe['csv_category'].value_counts())

    print(f"\nFirst 10 stocks:")
    print(universe[['ticker', 'name', 'csv_category']].head(10))

    print(f"\n{'='*60}")
    print("✓ CSV LOADING TEST PASSED")
    print(f"{'='*60}")

    return True

if __name__ == "__main__":
    success = test_csv_loading()
    exit(0 if success else 1)
