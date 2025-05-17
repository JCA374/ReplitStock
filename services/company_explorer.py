import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
from typing import Dict, List, Optional

# Import the add_to_watchlist function from data integration
from data.db_integration import add_to_watchlist

# Path for storing CSV data
DATA_DIR = "data/company_data"
SWEDEN_COMPANIES_FILE = os.path.join(DATA_DIR, "sweden_companies.json")

# Swedish indexes and their components
SWEDISH_INDEXES = {
    "OMXS30": "OMX Stockholm 30 Index",
    "OMXSPI": "OMX Stockholm All-Share Index",
    "OMXSMCPI": "OMX Stockholm Mid Cap Index",
    "OMXS Large Cap": "OMX Stockholm Large Cap Index"
}

# Common Swedish stock classes
STOCK_CLASSES = {
    "A": "A-shares (typically with more voting rights)",
    "B": "B-shares (typically with fewer voting rights, more liquid)",
    "PREF": "Preferred shares",
    "C": "C-shares (special purpose shares)",
    "D": "D-shares (typically dividend focused)",
    "SDB": "Swedish Depositary Receipts"
}

class CompanyExplorer:
    """
    Enhanced company search and exploration service with rich data display,
    focused on the Swedish market.
    """
    def __init__(self, db_storage=None):
        """Initialize the explorer with database access."""
        self.db_storage = db_storage
        
        # Create data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Load or initialize company data
        self._load_company_data()
        
    def _load_company_data(self):
        """Load and cache company data with extended information."""
        # Initialize empty DataFrame
        self.companies_df = pd.DataFrame(columns=["CompanyName", "Ticker", "Exchange", "Sector", "Industry", "Country"])
        
        # Load Swedish companies if available
        self._load_swedish_companies()
        
        # Load popular US stocks (as a fallback and for comparison)
        self._load_popular_us_stocks()
    
    def _load_swedish_companies(self):
        """Load Swedish companies data, or create it if it doesn't exist."""
        if os.path.exists(SWEDEN_COMPANIES_FILE):
            try:
                with open(SWEDEN_COMPANIES_FILE, 'r') as f:
                    companies = json.load(f)
                
                swedish_df = pd.DataFrame(companies)
                self.companies_df = pd.concat([self.companies_df, swedish_df], ignore_index=True)
                print(f"Loaded {len(swedish_df)} Swedish companies")
                return
            except Exception as e:
                print(f"Error loading Swedish companies: {e}")
        
        # If we couldn't load data, create a basic list of OMXS30 companies
        self._create_swedish_companies_data()
    
    def _create_swedish_companies_data(self):
        """Create basic Swedish company data if not available."""
        # This is a basic list of OMXS30 companies with their tickers
        omxs30_companies = [
            {"CompanyName": "ABB Ltd", "Ticker": "ABB.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Industrial Goods", "Country": "Sweden"},
            {"CompanyName": "Alfa Laval", "Ticker": "ALFA.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Industrial Goods", "Country": "Sweden"},
            {"CompanyName": "Assa Abloy", "Ticker": "ASSA-B.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Building Products", "Country": "Sweden"},
            {"CompanyName": "AstraZeneca", "Ticker": "AZN.ST", "Exchange": "Stockholm", "Sector": "Healthcare", "Industry": "Pharmaceuticals", "Country": "Sweden"},
            {"CompanyName": "Atlas Copco", "Ticker": "ATCO-A.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Industrial Goods", "Country": "Sweden"},
            {"CompanyName": "Atlas Copco", "Ticker": "ATCO-B.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Industrial Goods", "Country": "Sweden"},
            {"CompanyName": "Boliden", "Ticker": "BOL.ST", "Exchange": "Stockholm", "Sector": "Basic Materials", "Industry": "Mining", "Country": "Sweden"},
            {"CompanyName": "Electrolux", "Ticker": "ELUX-B.ST", "Exchange": "Stockholm", "Sector": "Consumer Cyclical", "Industry": "Household Appliances", "Country": "Sweden"},
            {"CompanyName": "Ericsson", "Ticker": "ERIC-B.ST", "Exchange": "Stockholm", "Sector": "Technology", "Industry": "Communication Equipment", "Country": "Sweden"},
            {"CompanyName": "Essity", "Ticker": "ESSITY-B.ST", "Exchange": "Stockholm", "Sector": "Consumer Defensive", "Industry": "Household Products", "Country": "Sweden"},
            {"CompanyName": "Getinge", "Ticker": "GETI-B.ST", "Exchange": "Stockholm", "Sector": "Healthcare", "Industry": "Medical Devices", "Country": "Sweden"},
            {"CompanyName": "Hennes & Mauritz", "Ticker": "HM-B.ST", "Exchange": "Stockholm", "Sector": "Consumer Cyclical", "Industry": "Retail", "Country": "Sweden"},
            {"CompanyName": "Hexagon", "Ticker": "HEXA-B.ST", "Exchange": "Stockholm", "Sector": "Technology", "Industry": "Software", "Country": "Sweden"},
            {"CompanyName": "Investor", "Ticker": "INVE-B.ST", "Exchange": "Stockholm", "Sector": "Financial Services", "Industry": "Investment Services", "Country": "Sweden"},
            {"CompanyName": "Kinnevik", "Ticker": "KINV-B.ST", "Exchange": "Stockholm", "Sector": "Financial Services", "Industry": "Investment Services", "Country": "Sweden"},
            {"CompanyName": "Nordea Bank", "Ticker": "NDA-SE.ST", "Exchange": "Stockholm", "Sector": "Financial Services", "Industry": "Banks", "Country": "Sweden"},
            {"CompanyName": "Sandvik", "Ticker": "SAND.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Industrial Goods", "Country": "Sweden"},
            {"CompanyName": "SCA", "Ticker": "SCA-B.ST", "Exchange": "Stockholm", "Sector": "Basic Materials", "Industry": "Paper & Forestry Products", "Country": "Sweden"},
            {"CompanyName": "SEB", "Ticker": "SEB-A.ST", "Exchange": "Stockholm", "Sector": "Financial Services", "Industry": "Banks", "Country": "Sweden"},
            {"CompanyName": "Securitas", "Ticker": "SECU-B.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Security & Protection", "Country": "Sweden"},
            {"CompanyName": "Skanska", "Ticker": "SKA-B.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Construction", "Country": "Sweden"},
            {"CompanyName": "SKF", "Ticker": "SKF-B.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Industrial Goods", "Country": "Sweden"},
            {"CompanyName": "SSAB", "Ticker": "SSAB-A.ST", "Exchange": "Stockholm", "Sector": "Basic Materials", "Industry": "Steel", "Country": "Sweden"},
            {"CompanyName": "Swedbank", "Ticker": "SWED-A.ST", "Exchange": "Stockholm", "Sector": "Financial Services", "Industry": "Banks", "Country": "Sweden"},
            {"CompanyName": "Swedish Match", "Ticker": "SWMA.ST", "Exchange": "Stockholm", "Sector": "Consumer Defensive", "Industry": "Tobacco", "Country": "Sweden"},
            {"CompanyName": "Tele2", "Ticker": "TEL2-B.ST", "Exchange": "Stockholm", "Sector": "Communication Services", "Industry": "Telecom", "Country": "Sweden"},
            {"CompanyName": "Telia Company", "Ticker": "TELIA.ST", "Exchange": "Stockholm", "Sector": "Communication Services", "Industry": "Telecom", "Country": "Sweden"},
            {"CompanyName": "Volvo", "Ticker": "VOLV-B.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Auto Manufacturers", "Country": "Sweden"},
            {"CompanyName": "Volvo", "Ticker": "VOLV-A.ST", "Exchange": "Stockholm", "Sector": "Industrials", "Industry": "Auto Manufacturers", "Country": "Sweden"},
            {"CompanyName": "Latour", "Ticker": "LATO-B.ST", "Exchange": "Stockholm", "Sector": "Financial Services", "Industry": "Investment Services", "Country": "Sweden"}
        ]
        
        # Add the OMXS30 companies to our DataFrame
        swedish_df = pd.DataFrame(omxs30_companies)
        self.companies_df = pd.concat([self.companies_df, swedish_df], ignore_index=True)
        
        # Save this data for future use
        try:
            os.makedirs(os.path.dirname(SWEDEN_COMPANIES_FILE), exist_ok=True)
            with open(SWEDEN_COMPANIES_FILE, 'w') as f:
                json.dump(omxs30_companies, f, indent=2)
            print(f"Created Swedish companies data file with {len(omxs30_companies)} companies")
        except Exception as e:
            print(f"Error saving Swedish companies data: {e}")
    
    def _load_popular_us_stocks(self):
        """Load popular US stocks for comparison."""
        popular_us_stocks = [
            {"CompanyName": "Apple Inc.", "Ticker": "AAPL", "Exchange": "NASDAQ", "Sector": "Technology", "Industry": "Consumer Electronics", "Country": "USA"},
            {"CompanyName": "Microsoft Corporation", "Ticker": "MSFT", "Exchange": "NASDAQ", "Sector": "Technology", "Industry": "Software", "Country": "USA"},
            {"CompanyName": "Alphabet Inc. (Google)", "Ticker": "GOOGL", "Exchange": "NASDAQ", "Sector": "Technology", "Industry": "Internet Services", "Country": "USA"},
            {"CompanyName": "Amazon.com Inc.", "Ticker": "AMZN", "Exchange": "NASDAQ", "Sector": "Consumer Cyclical", "Industry": "E-commerce", "Country": "USA"},
            {"CompanyName": "Tesla, Inc.", "Ticker": "TSLA", "Exchange": "NASDAQ", "Sector": "Consumer Cyclical", "Industry": "Auto Manufacturers", "Country": "USA"},
            {"CompanyName": "Meta Platforms (Facebook)", "Ticker": "META", "Exchange": "NASDAQ", "Sector": "Technology", "Industry": "Internet Services", "Country": "USA"},
            {"CompanyName": "NVIDIA Corporation", "Ticker": "NVDA", "Exchange": "NASDAQ", "Sector": "Technology", "Industry": "Semiconductors", "Country": "USA"},
            {"CompanyName": "JPMorgan Chase & Co.", "Ticker": "JPM", "Exchange": "NYSE", "Sector": "Financial Services", "Industry": "Banks", "Country": "USA"},
            {"CompanyName": "Johnson & Johnson", "Ticker": "JNJ", "Exchange": "NYSE", "Sector": "Healthcare", "Industry": "Pharmaceuticals", "Country": "USA"},
            {"CompanyName": "Visa Inc.", "Ticker": "V", "Exchange": "NYSE", "Sector": "Financial Services", "Industry": "Credit Services", "Country": "USA"}
        ]
        
        us_df = pd.DataFrame(popular_us_stocks)
        self.companies_df = pd.concat([self.companies_df, us_df], ignore_index=True)
    
    def search(self, query: str, filters: Optional[Dict] = None, limit: int = 20) -> pd.DataFrame:
        """
        Search for companies using partial matching and filters.
        
        Args:
            query: The search string
            filters: Optional dictionary of filters (sector, country, etc.)
            limit: Maximum number of results to return
            
        Returns:
            DataFrame with matching companies
        """
        if not query or self.companies_df.empty:
            return self.companies_df.head(0)  # Return empty DataFrame with same structure
        
        # Normalize query
        query = query.lower().strip()
        
        # Search using case-insensitive partial matching
        mask = (
            self.companies_df["CompanyName"].str.lower().str.contains(query, na=False) |
            self.companies_df["Ticker"].str.lower().str.contains(query, na=False)
        )
        
        # Apply any additional filters
        if filters:
            if "sector" in filters and filters["sector"] != "All Sectors":
                mask &= self.companies_df["Sector"] == filters["sector"]
                
            if "country" in filters and filters["country"] != "All Countries":
                mask &= self.companies_df["Country"] == filters["country"]
                
            if "exchange" in filters and filters["exchange"] != "All Exchanges":
                mask &= self.companies_df["Exchange"] == filters["exchange"]
        
        results = self.companies_df[mask].head(limit)
        return results
    
    def get_stock_class_info(self, ticker: str) -> Dict:
        """Get information about the stock class for Swedish stocks."""
        ticker = ticker.upper()
        
        # Check for various Swedish stock class patterns
        for class_code, description in STOCK_CLASSES.items():
            if f"-{class_code}." in ticker:
                return {
                    "class": class_code,
                    "description": description
                }
                
        # Handle SDB separately as it's often at the end
        if "SDB" in ticker:
            return {
                "class": "SDB",
                "description": STOCK_CLASSES["SDB"]
            }
        
        # No specific class identified
        return {
            "class": "Unknown",
            "description": "Regular shares or unknown class"
        }
    
    def get_enhanced_stock_info(self, ticker: str) -> Dict:
        """
        Get enhanced stock information, including company details, 
        stock class, and description.
        """
        result = {
            "ticker": ticker,
            "name": "",
            "exchange": "",
            "sector": "",
            "stock_class": {},
            "description": "",
            "country": ""
        }
        
        # Look up in our companies DataFrame first
        company_match = self.companies_df[self.companies_df["Ticker"] == ticker]
        if not company_match.empty:
            row = company_match.iloc[0]
            result["name"] = row["CompanyName"]
            result["exchange"] = row["Exchange"]
            result["sector"] = row["Sector"]
            result["country"] = row["Country"]
        
        # Add stock class information for Swedish stocks
        if ".ST" in ticker:
            result["stock_class"] = self.get_stock_class_info(ticker)
            
            # Add index membership for Swedish stocks
            if ticker in ["OMXS30.ST", "OMXSPI.ST"]:
                result["description"] = f"Swedish Market Index: {SWEDISH_INDEXES.get(ticker.replace('.ST', ''), '')}"
        
        return result
    
    def get_sectors(self) -> List[str]:
        """Get a list of available sectors from the company data."""
        if self.companies_df.empty or "Sector" not in self.companies_df.columns:
            return []
        
        sectors = sorted(self.companies_df["Sector"].dropna().unique().tolist())
        return sectors
    
    def get_countries(self) -> List[str]:
        """Get a list of available countries from the company data."""
        if self.companies_df.empty or "Country" not in self.companies_df.columns:
            return []
        
        countries = sorted(self.companies_df["Country"].dropna().unique().tolist())
        return countries
    
    def get_exchanges(self) -> List[str]:
        """Get a list of available exchanges from the company data."""
        if self.companies_df.empty or "Exchange" not in self.companies_df.columns:
            return []
        
        exchanges = sorted(self.companies_df["Exchange"].dropna().unique().tolist())
        return exchanges
    
    def render_company_card(self, company_data: Dict):
        """Render a rich company information card with stock class information for Swedish stocks."""
        ticker = company_data.get("Ticker", "")
        
        with st.container():
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Company name and ticker
                st.subheader(company_data.get("CompanyName", "Unknown Company"))
                st.caption(f"Ticker: {ticker}")
                
                # Company info
                st.write(f"**Sector:** {company_data.get('Sector', 'N/A')}")
                st.write(f"**Industry:** {company_data.get('Industry', 'N/A')}")
                st.write(f"**Exchange:** {company_data.get('Exchange', 'N/A')}")
                
                # Add stock class information for Swedish stocks
                if ".ST" in ticker:
                    stock_class = self.get_stock_class_info(ticker)
                    st.write(f"**Stock Class:** {stock_class['class']} - {stock_class['description']}")
            
            with col2:
                # Action buttons
                analyze_button_key = f"analyze_{ticker}"
                watchlist_button_key = f"watchlist_{ticker}"
                
                if st.button("📊 Analyze", key=analyze_button_key):
                    st.session_state["analyze_ticker"] = ticker
                    st.rerun()
                
                if st.button("➕ Add to Watchlist", key=watchlist_button_key):
                    success = add_to_watchlist(
                        ticker=ticker,
                        name=company_data.get("CompanyName", ""),
                        exchange=company_data.get("Exchange", ""),
                        sector=company_data.get("Sector", "")
                    )
                    
                    if success:
                        st.success(f"Added {ticker} to watchlist!")
                    else:
                        st.info(f"{ticker} is already in your watchlist.")


def render_explorer_tab():
    """Render the company explorer tab with Swedish market focus."""
    st.header("Company Explorer")
    st.write("Discover and analyze companies with a focus on the Swedish market")
    
    # Initialize explorer if not already in session state
    if "company_explorer" not in st.session_state:
        db_storage = st.session_state.get("db_storage")
        st.session_state.company_explorer = CompanyExplorer(db_storage)
    
    explorer = st.session_state.company_explorer
    
    # Search bar and filters in clean layout
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Companies:", 
                placeholder="Enter company name or ticker (e.g., Volvo, H&M, ERIC-B)",
                key="company_explorer_search"
            )
        
        with col2:
            # Default to Swedish market filter
            market_filter = st.selectbox(
                "Market:",
                ["Swedish Market", "All Markets", "US Market"],
                index=0  # Default to Swedish Market
            )
    
    # Additional filters in expander
    with st.expander("Advanced Filters"):
        col1, col2 = st.columns(2)
        
        with col1:
            sectors = ["All Sectors"] + explorer.get_sectors()
            selected_sector = st.selectbox("Sector:", sectors)
        
        with col2:
            if market_filter == "All Markets":
                countries = ["All Countries"] + explorer.get_countries()
                selected_country = st.selectbox("Country:", countries)
            else:
                # Set country based on market filter
                selected_country = "Sweden" if market_filter == "Swedish Market" else "USA"
                st.write(f"**Country:** {selected_country}")
    
    # Apply filters
    filters = {}
    if selected_sector != "All Sectors":
        filters["sector"] = selected_sector
    
    if market_filter == "Swedish Market":
        filters["country"] = "Sweden"
    elif market_filter == "US Market":
        filters["country"] = "USA"
    elif 'selected_country' in locals() and selected_country != "All Countries":
        filters["country"] = selected_country
    
    # Popular Swedish Companies section
    st.subheader("Popular Swedish Companies")
    st.write("Click on a company to view details and analysis")
    
    # Display popular Swedish companies in a grid
    popular_swedish = explorer.companies_df[
        (explorer.companies_df["Country"] == "Sweden") & 
        (explorer.companies_df["Ticker"].str.contains("-B.ST")) 
    ].head(6)
    
    if not popular_swedish.empty:
        cols = st.columns(3)
        for i, (_, company) in enumerate(popular_swedish.iterrows()):
            with cols[i % 3]:
                with st.container():
                    st.write(f"**{company['CompanyName']}**")
                    st.caption(company['Ticker'])
                    
                    if st.button("View", key=f"popular_{company['Ticker']}"):
                        # Set as search query and rerun
                        st.session_state["company_explorer_search"] = company['CompanyName']
                        st.rerun()
    
    # Search results
    if search_query:
        results = explorer.search(search_query, filters=filters)
        
        if not results.empty:
            st.subheader(f"Search Results ({len(results)} companies)")
            
            # Display results as rich cards
            for _, company in results.iterrows():
                explorer.render_company_card(company)
                st.divider()
        else:
            st.info("No companies found matching your search criteria.")
            
            # Suggest alternatives for Swedish searches
            if "swedish" in market_filter.lower():
                st.write("**Suggestions:**")
                st.write("- Try searching without stock class (e.g., 'Volvo' instead of 'VOLV-B')")
                st.write("- For Swedish stocks, try both with and without the '.ST' suffix")
                st.write("- Check if the company is listed on OMX Stockholm")