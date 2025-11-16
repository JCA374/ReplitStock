# TLS Error Fix for Yahoo Finance

## Problem

```
ERROR: Failed to get ticker 'VOLV-B.ST' reason: Failed to perform,
curl: (35) TLS connect error: error:00000000:invalid library (0):
OPENSSL_internal:invalid library (0)
```

## Root Cause

- `curl_cffi` version 0.13.0 has TLS/SSL compatibility issues
- Affects yfinance's ability to fetch data from Yahoo Finance
- System OpenSSL library incompatibility

## Solution

Downgrade `curl_cffi` to stable version 0.7.x:

```bash
pip uninstall -y curl_cffi
pip install --no-cache-dir "curl_cffi>=0.7.0,<0.8.0"
```

## Verification

Test if Yahoo Finance works:

```bash
python -c "
import yfinance as yf
stock = yf.Ticker('VOLV-B.ST')
hist = stock.history(period='5d')
if not hist.empty:
    print('✓ Yahoo Finance working!')
    print(f'Got {len(hist)} days of data')
else:
    print('✗ Still failing')
"
```

## Alternative Solutions

If the above doesn't work, try these in order:

### 1. Use pure requests (no curl_cffi)
```bash
pip uninstall -y curl_cffi
pip install --no-cache-dir yfinance
```

### 2. Add Twelve Data as backup
```bash
pip install twelvedata

# Add to .env
TWELVE_DATA_API_KEY=your_key_here
```

### 3. Update system OpenSSL
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install --reinstall libssl-dev openssl

# Check version
openssl version
```

## Dependencies After Fix

```
yfinance==0.2.66
curl_cffi==0.7.4  # NOT 0.13.0
```

## Test System

After applying fix, run:

```bash
./quick_test.sh
```

Expected output:
```
Successfully analyzed: 5/5
Top Stock: INVE-B.ST (Score: 52.1)
```

## Status

✅ Fixed with curl_cffi 0.7.4 downgrade
