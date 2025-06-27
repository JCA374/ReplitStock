#!/usr/bin/env python3
"""
Populate default Swedish stock data for the application
This ensures the app has data available for scanning on first launch
"""

import os
import sys
import json
from data.db_integration import add_to_watchlist

def populate_swedish_watchlist():
    """Add Swedish OMXS30 companies to the default watchlist"""
    
    swedish_companies = [
        {"ticker": "ABB.ST", "name": "ABB Ltd", "sector": "Industrials"},
        {"ticker": "ALFA.ST", "name": "Alfa Laval", "sector": "Industrials"},
        {"ticker": "ASSA-B.ST", "name": "Assa Abloy", "sector": "Industrials"},
        {"ticker": "AZN.ST", "name": "AstraZeneca", "sector": "Healthcare"},
        {"ticker": "ATCO-A.ST", "name": "Atlas Copco A", "sector": "Industrials"},
        {"ticker": "ATCO-B.ST", "name": "Atlas Copco B", "sector": "Industrials"},
        {"ticker": "BOL.ST", "name": "Boliden", "sector": "Basic Materials"},
        {"ticker": "ELUX-B.ST", "name": "Electrolux", "sector": "Consumer Cyclical"},
        {"ticker": "ERIC-B.ST", "name": "Ericsson", "sector": "Technology"},
        {"ticker": "ESSITY-B.ST", "name": "Essity", "sector": "Consumer Defensive"},
        {"ticker": "GETI-B.ST", "name": "Getinge", "sector": "Healthcare"},
        {"ticker": "HM-B.ST", "name": "Hennes & Mauritz", "sector": "Consumer Cyclical"},
        {"ticker": "HEXA-B.ST", "name": "Hexagon", "sector": "Technology"},
        {"ticker": "INVE-B.ST", "name": "Investor", "sector": "Financial Services"},
        {"ticker": "KINV-B.ST", "name": "Kinnevik", "sector": "Financial Services"},
        {"ticker": "NDA-SE.ST", "name": "Nordea Bank", "sector": "Financial Services"},
        {"ticker": "SAND.ST", "name": "Sandvik", "sector": "Industrials"},
        {"ticker": "SCA-B.ST", "name": "SCA", "sector": "Basic Materials"},
        {"ticker": "SEB-A.ST", "name": "SEB", "sector": "Financial Services"},
        {"ticker": "SECU-B.ST", "name": "Securitas", "sector": "Industrials"},
        {"ticker": "SKA-B.ST", "name": "Skanska", "sector": "Industrials"},
        {"ticker": "SKF-B.ST", "name": "SKF", "sector": "Industrials"},
        {"ticker": "SSAB-A.ST", "name": "SSAB", "sector": "Basic Materials"},
        {"ticker": "SWED-A.ST", "name": "Swedbank", "sector": "Financial Services"},
        {"ticker": "SWMA.ST", "name": "Swedish Match", "sector": "Consumer Defensive"},
        {"ticker": "TEL2-B.ST", "name": "Tele2", "sector": "Communication Services"},
        {"ticker": "TELIA.ST", "name": "Telia Company", "sector": "Communication Services"},
        {"ticker": "VOLV-B.ST", "name": "Volvo B", "sector": "Industrials"},
        {"ticker": "VOLV-A.ST", "name": "Volvo A", "sector": "Industrials"},
        {"ticker": "LATO-B.ST", "name": "Latour", "sector": "Financial Services"}
    ]
    
    print(f"Adding {len(swedish_companies)} Swedish companies to watchlist...")
    
    added_count = 0
    for company in swedish_companies:
        try:
            success = add_to_watchlist(
                ticker=company["ticker"],
                name=company["name"],
                exchange="Stockholm",
                sector=company["sector"]
            )
            if success:
                added_count += 1
                print(f"✓ Added {company['ticker']} - {company['name']}")
            else:
                print(f"⚠ Failed to add {company['ticker']}")
        except Exception as e:
            print(f"✗ Error adding {company['ticker']}: {e}")
    
    print(f"\nCompleted: {added_count}/{len(swedish_companies)} companies added to watchlist")
    return added_count

if __name__ == "__main__":
    print("Populating default Swedish stock data...")
    populate_swedish_watchlist()
    print("Default data population complete!")