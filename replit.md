# Stock Analysis Application - Architecture and System Design

## Overview

This is a comprehensive stock analysis application built with **Streamlit** as the frontend framework. The application provides advanced stock screening, technical and fundamental analysis capabilities, with a focus on Swedish market stocks. It implements a robust data collection system with multiple data sources and intelligent caching strategies.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application
- **UI Components**: Modular component-based architecture in `/ui/` directory
- **Navigation**: Tab-based interface with specialized analysis modules
- **State Management**: Streamlit session state for user preferences and data caching

### Backend Architecture
- **Data Layer**: Dual-database architecture with SQLite and Supabase PostgreSQL
- **Analysis Engine**: Modular analysis components for technical and fundamental analysis
- **Data Sources**: Multi-provider data fetching with Alpha Vantage and Yahoo Finance APIs
- **Caching Strategy**: Intelligent multi-layer caching with configurable TTL

### Database Design
- **Primary**: Supabase PostgreSQL (cloud-based)
- **Fallback**: SQLite (local file-based)
- **Models**: SQLAlchemy ORM with automatic table creation
- **Connection Management**: Context managers with proper session handling

## Key Components

### Data Management (`/data/`)
- **`db_connection.py`**: Central database connection manager with automatic fallback
- **`db_integration.py`**: Unified data access layer abstracting database operations
- **`db_models.py`**: SQLAlchemy ORM models defining database schema
- **`stock_data.py`**: Multi-source stock data fetcher with intelligent provider selection
- **`supabase_client.py`**: Supabase-specific client wrapper with connection management

### Analysis Modules (`/analysis/`)
- **`strategy.py`**: Value Momentum Strategy implementation with technical scoring
- **`technical.py`**: Technical indicator calculations (RSI, MACD, Moving Averages)
- **`fundamental.py`**: Fundamental analysis with P/E ratio and margin analysis
- **`scanner.py`**: Stock screening engine with customizable criteria
- **`bulk_scanner.py`**: High-performance bulk analysis with parallel processing

### User Interface (`/ui/`)
- **`enhanced_scanner.py`**: Advanced stock scanner with ranking and filtering
- **`batch_analysis.py`**: Bulk stock analysis interface
- **`watchlist.py`**: Watchlist management with multiple collections
- **`company_explorer.py`**: Company search and exploration interface
- **`database_viewer.py`**: Database content visualization and management

### Services (`/services/`)
- **`watchlist_manager.py`**: Watchlist operations with cross-database support
- **`company_explorer.py`**: Swedish market company data and search functionality
- **`stock_data_manager.py`**: Centralized stock data operations

## Data Flow

### Primary Data Flow
1. **Database Cache Check**: SQLite → Supabase (if connected)
2. **API Fallback**: Alpha Vantage (preferred) → Yahoo Finance (fallback)
3. **Data Caching**: Store results in both SQLite and Supabase
4. **Analysis Pipeline**: Technical → Fundamental → Signal Generation

### Caching Strategy
- **Fundamentals**: 48-hour cache (expensive API calls)
- **Daily Prices**: 6-hour cache (moderate cost)
- **Weekly Prices**: 24-hour cache (lower priority)
- **Intraday**: 2-hour cache (high volatility)

### Error Handling
- **API Failures**: Automatic fallback between data providers
- **Database Failures**: Seamless switching between Supabase and SQLite
- **Data Quality**: Validation and sanitization at multiple layers

## External Dependencies

### APIs and Data Sources
- **Alpha Vantage**: Primary data source for fundamentals and historical data
- **Yahoo Finance**: Fallback data source with rate limiting protection
- **Supabase**: Cloud PostgreSQL database with REST API

### Python Libraries
- **Core**: `streamlit`, `pandas`, `numpy`
- **Database**: `sqlalchemy`, `pg8000`, `supabase`
- **Financial**: `yfinance`, `alpha-vantage`
- **Visualization**: `plotly`, `matplotlib`
- **Utilities**: `requests`, `trafilatura`

### Configuration Management
- **Environment Variables**: API keys and database credentials
- **Config File**: Application settings and analysis parameters
- **Secrets Management**: Streamlit secrets.toml for sensitive data

## Deployment Strategy

### Local Development
- SQLite database for immediate functionality
- Environment variables for API configuration
- Streamlit development server
- VS Code integration with automated setup scripts

### VS Code Preview Setup
- **Windows**: `setup-windows.bat` for automated environment setup
- **Mac/Linux**: `setup-linux-mac.sh` for automated environment setup
- **VS Code Configuration**: `.vscode/` folder with tasks, debugging, and settings
- **Quick Launch**: Integrated tasks for one-click app startup
- **Debug Support**: Full debugging capabilities with breakpoints

### Cloud Deployment
- Supabase PostgreSQL for production database
- Environment variable injection for credentials
- Streamlit Cloud or custom deployment platform

### Database Migration
- Automated table creation via SQLAlchemy
- Migration scripts for watchlist data transfer
- Fallback mechanisms ensure continuous operation

## Changelog

- June 27, 2025. Initial setup
- June 27, 2025. Migrated from Replit Agent to standard environment, improved batch analysis table readability with consistent font sizing, set app to start on batch scan with first watchlist as default
- June 27, 2025. Optimized batch scanner for mobile devices: added full-width responsive layout, simplified controls to 2-column layout, reduced table from 8 to 5 columns, added collapsible filters, removed "Manual Entry" option and "BUY Signals" counter
- June 27, 2025. Added VS Code preview support for Windows users: created automated setup scripts (.bat and .sh), VS Code configuration files (settings, tasks, debugging), comprehensive README documentation for GitHub downloads, and one-click launch capabilities
- June 27, 2025. Fixed stock scanning CSV data loading: created ticker cleaning utility to handle malformed tickers (ACADST -> ACAD.ST), populated default watchlist with 29 Swedish companies, fixed port configuration for Streamlit Cloud compatibility (8501), now properly loads 351 total stocks (108 small, 143 mid, 100 large cap)

## User Preferences

Preferred communication style: Simple, everyday language.