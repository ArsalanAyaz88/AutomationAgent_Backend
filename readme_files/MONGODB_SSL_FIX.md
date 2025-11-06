# MongoDB Atlas SSL Connection Fix

## Problem
The application was failing to start with the error:
```
pymongo.errors.ServerSelectionTimeoutError: SSL handshake failed: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
```

This occurred when trying to connect to MongoDB Atlas from Windows during application initialization.

## Root Cause
MongoDB Atlas connections require proper SSL/TLS configuration, especially on Windows. The connection was failing because:
1. No SSL/TLS parameters were specified in the MongoClient connection
2. Missing SSL certificate handling (certifi package)
3. No DNS resolution support for `mongodb+srv://` URIs (dnspython package)
4. No error handling for connection failures

## Fixes Applied

### 1. Updated Dependencies (`requirements.txt`)
Added two new packages:
```
certifi>=2023.0.0  # SSL certificates for MongoDB Atlas
dnspython>=2.0.0   # Required for mongodb+srv:// connections
```

### 2. Updated Central Memory DB (`databasess/agents_CentralMemory/central_memory.py`)
- ✅ Added SSL/TLS configuration with proper certificate handling
- ✅ Automatic detection of MongoDB Atlas vs local connections
- ✅ Graceful error handling with fallback behavior
- ✅ Connection status checking in all database methods
- ✅ Informative warning messages when connections fail

**Key Changes:**
- Uses `certifi.where()` for CA certificate file
- Configures TLS with proper security settings
- Reduced timeouts to prevent long startup delays
- All methods check connection before database operations

### 3. Updated LTM DB (`databasess/agents_LTM/mongodb_memory.py`)
Applied the same SSL/TLS fixes as Central Memory DB.

## How to Use

### Option 1: MongoDB Atlas (Recommended)
1. **Install new dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

2. **Set environment variables:**
   Create a `.env` file in the `Backend` directory:
   ```env
   # MongoDB Atlas URIs
   LTM_DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   CENTRALMEMORY_DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```

3. **Verify MongoDB Atlas settings:**
   - Ensure your IP address is whitelisted in MongoDB Atlas Network Access
   - Check that database user has read/write permissions
   - Verify connection string is correct

4. **Start the application:**
   ```bash
   uv run python -m uvicorn main:app --reload
   ```

### Option 2: Local MongoDB (Development)
If you don't have MongoDB Atlas credentials, use local MongoDB:

1. **Install MongoDB locally** (if not already installed)

2. **Update .env file:**
   ```env
   LTM_DATABASE_URL=mongodb://localhost:27017
   CENTRALMEMORY_DATABASE_URL=mongodb://localhost:27017
   ```

3. **Start MongoDB service:**
   ```bash
   # Windows
   net start MongoDB
   ```

4. **Start the application:**
   ```bash
   uv run python -m uvicorn main:app --reload
   ```

## Graceful Degradation

The application now handles MongoDB connection failures gracefully:

- ⚠️ **Connection warnings are displayed** but don't crash the app
- 📋 **Database operations will fail softly** with warning messages
- 🔄 **RL features requiring database will be disabled** until connection succeeds
- ✅ **Other application features continue to work**

You'll see messages like:
```
⚠️  Warning: MongoDB Central Memory initialization failed: [error details]
   Connection will be retried on first use.
```

## Testing the Connection

Run the test script to verify MongoDB connections:
```bash
python test_mongodb_connection.py
```

This will test both Central Memory and LTM connections and provide diagnostic information.

## Troubleshooting

### Issue: "IP not whitelisted" in MongoDB Atlas
**Solution:** Add your IP address to Network Access in MongoDB Atlas dashboard

### Issue: "Authentication failed"
**Solution:** Check username/password in connection string

### Issue: Still getting SSL errors
**Solution:** 
1. Ensure certifi and dnspython are installed: `uv pip install certifi dnspython`
2. Try updating pymongo: `uv pip install --upgrade pymongo`
3. Check Windows firewall/antivirus isn't blocking MongoDB connections

### Issue: Connection timeout
**Solution:**
1. Check internet connection
2. Verify MongoDB Atlas cluster is running
3. Try increasing timeout values in the connection configuration

## Technical Details

### SSL/TLS Configuration (Atlas)
```python
MongoClient(
    uri,
    tls=True,
    tlsAllowInvalidCertificates=False,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
    retryWrites=True,
    retryReads=True
)
```

### Connection Detection
The code automatically detects Atlas URIs:
- `mongodb+srv://` prefix
- `mongodb.net` domain in URI

Local MongoDB connections use simpler configuration without SSL.

## Next Steps

1. ✅ Install new dependencies
2. ✅ Configure environment variables
3. ✅ Test MongoDB connection
4. ✅ Start the application

The application should now start successfully even if MongoDB connections have issues, with appropriate warnings displayed in the console.
