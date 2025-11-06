# 🧪 Testing & Verification Files

This folder contains all testing and verification scripts for the YouTube Agents RL System.

---

## 🧪 Test Files (10 total)

### ✅ Architecture Verification
- **`verify_agent_architecture.py`** - Detailed architecture verification (all 7 agents)
- **`verify_agents_quick.py`** - Quick verification with summary table

### 🔬 Unit Tests
- **`test_api.py`** - API endpoint tests
- **`test_imports.py`** - Import verification
- **`test_mongodb_connection.py`** - MongoDB connection tests
- **`test_cloud_connections.py`** - Cloud connection tests
- **`test_all_agents_rl.py`** - RL agents comprehensive testing
- **`quick_test.py`** - Quick API tests

### 📊 Examples & Results
- **`rl_enhanced_example.py`** - RL integration examples
- **`rl_test_results.json`** - Test results data

---

## 🚀 How to Run Tests

### Quick System Verification
```bash
cd Backend/testing_files
python verify_agents_quick.py
```
Shows: All 7 agents status in a summary table

### Detailed Architecture Verification
```bash
python verify_agent_architecture.py
```
Shows: Complete details for each agent (STM, LTM, RL Engine)

### API Tests
```bash
python test_api.py
```

### MongoDB Connection Test
```bash
python test_mongodb_connection.py
```

### Cloud Connections Test
```bash
python test_cloud_connections.py
```

---

## 📊 Expected Output

### verify_agents_quick.py
```
┌─────┬───────────────────────────┬─────────────────┬───────┬─────────┬───────┐
│ No. │ Agent Name                │ Type            │ STM   │ LTM     │ RL    │
├─────┼───────────────────────────┼─────────────────┼───────┼─────────┼───────┤
│ 1   │ agent1_channel_auditor    │ channel_analyst │ ✅    │ ✅      │ ✅    │
│ 2   │ agent2_title_auditor      │ content_optimiz │ ✅    │ ✅      │ ✅    │
...
```

### verify_agent_architecture.py
Shows detailed breakdown:
- STM Redis connection and key prefix
- LTM MongoDB collections
- RL Engine hyperparameters
- Agent capabilities
- Central Memory status

---

## 🎯 Test Coverage

### System Components
- ✅ 7 Agents initialization
- ✅ STM (Redis) connection
- ✅ LTM (MongoDB) connection
- ✅ RL Engine (Q-Learning) status
- ✅ Central Memory connection
- ✅ API endpoints

### Architecture Verification
- ✅ Memory isolation per agent
- ✅ Central Memory sharing
- ✅ RL Engine independence
- ✅ Graceful degradation without databases

---

## 📝 Test Results

Results are saved to:
- **`rl_test_results.json`** - Latest test run results

---

## 🔧 Requirements

All tests require:
```bash
# Backend dependencies
pip install -r ../requirements.txt

# Or for production
pip install -r ../requirements.prod.txt
```

---

## ⚠️ Important Notes

1. **Database Connection**: Tests work even without Redis/MongoDB
   - RL Engine tests always pass (in-memory)
   - STM/LTM tests show warnings but don't fail

2. **Running from Root**: Use relative paths
   ```bash
   cd Backend
   python testing_files/verify_agents_quick.py
   ```

3. **CI/CD**: These tests can be run in CI pipelines
   ```yaml
   # Example GitHub Actions
   - name: Verify RL System
     run: python testing_files/verify_agents_quick.py
   ```

---

## 📚 Related Documentation

For testing guides, see:
- `../readme_files/TESTING_GUIDE.md`
- `../readme_files/AGENT_MEMORY_ARCHITECTURE.md`

---

**All tests in one place!** 🧪
