# Verifier Agent Test Clients

Test clients for the verifier agent service running on Oasis ROFL.

## Installation

```bash
cd test
uv sync
```

## Configuration

Create a `.env` file:

```bash
# API endpoint
API_URL=http://localhost:4021
```

## Test Scripts

### 1. test_client.py - Document Verification (Legacy)

Tests the general document verification endpoint.

**Usage:**

```bash
# Test with default test data
uv run python test_client.py

# Test with your own data
uv run python test_client.py /path/to/your/document.txt
```

**What it tests:**
- `/verify` endpoint - General document summarization
- Ollama AI processing
- Background task processing

---

### 2. test_validation.py - Blockchain Job Validation (New)

Tests the blockchain job validation endpoint with Hedera integration.

**Usage:**

```bash
# Validate without event check
uv run python test_validation.py 0xJOB_ID

# Validate with event verification
uv run python test_validation.py 0xJOB_ID 0xTRANSACTION_HASH

# Validate with custom verifier agent ID
uv run python test_validation.py 0xJOB_ID 0xTX_HASH 42
```

**Example:**

```bash
uv run python test_validation.py \
  0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef \
  0x94dc1274cbd021f76ea853ed40038baeaecd34325c11c133a0201123aa8d9638 \
  2
```

**What it tests:**
- `/validate` endpoint - Blockchain job validation
- CrossValidationRequested event checking
- Job data fetching from smart contracts
- AI reputation scoring (0-100)
- On-chain reputation recording
- TEE signature verification

**Output includes:**
- ✅ Validation status
- 🎯 AI-generated reputation score
- 📝 On-chain transaction hash
- 📋 Job details from blockchain
- 🔐 TEE cryptographic signature

---

## Testing Against Production

To test against the deployed ROFL instance:

```bash
# Update .env
API_URL=https://your-rofl-endpoint.oasis.io

# Run tests
uv run python test_validation.py 0xYOUR_JOB_ID
```

## AI Provider

The service uses **Ollama** (qwen2:0.5b) for AI-powered validation and scoring.

## Blockchain Integration

- **Network:** Hedera Testnet
- **Web3 Provider:** hashio.io RPC
- **Contracts:**
  - RegistryModule: `0xa041ec83d30ef5f7ffc4bc7a62bf1aaeee5544b6`
  - JobsModule: (configurable via env)

## Troubleshooting

**Service not responding:**
```bash
curl http://localhost:4021/
```

**Check logs:**
```bash
docker compose logs app -f
```

**Verify Hedera connection:**
```bash
# In app directory
uv run python test_web3_setup.py
```
