# ROFL x402 Verifier Agent

AI-powered job validation with Hedera blockchain integration.

## 🎯 Features

- ✅ **AI Validation** - Ollama-powered dispute resolution
- ✅ **Blockchain Verification** - Check events on Hedera
- ✅ **Smart Contract Integration** - Call & execute EVM contracts
- ✅ **TEE Signing** - ROFL-signed verifiable responses
- ✅ **Web3 Standard** - Uses web3.py for EVM interactions

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure

Create `.env`:

```bash
# Private Key
PRIVATE_KEY=0x...

# Hedera Network
HEDERA_NETWORK=testnet

# Contract Addresses (EVM addresses)
JOBS_MODULE_ADDRESS=0x...

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2:0.5b
```

### 3. Test Connection

```bash
uv run python test_web3_setup.py
```

### 4. Start Service

```bash
uv run uvicorn main:app --reload --port 4021
```

## 📡 API Endpoints

### POST /validate

Validate a job and record reputation score.

**Request:**
```json
{
  "job_id": "0xabc123...",
  "transaction_id": "0xdef456...",
  "verifier_agent_id": 42
}
```

**Response:**
```json
{
  "validation_id": "uuid",
  "status": "processing",
  "status_url": "/verify/uuid"
}
```

### GET /verify/{validation_id}

Get validation result.

**Response:**
```json
{
  "status": "completed",
  "ai_score": 85,
  "reputation_tx_id": "0x...",
  "signature": "0x...",
  "job_details": { ... }
}
```

## 📚 Documentation

- **[WEB3_MIGRATION.md](./WEB3_MIGRATION.md)** - Web3.py migration guide
- **[VALIDATION_GUIDE.md](./VALIDATION_GUIDE.md)** - Validation endpoint guide
- **[EVM_LOGS_GUIDE.md](./EVM_LOGS_GUIDE.md)** - Event logs guide

## 🧪 Testing

```bash
# Test Web3 setup
uv run python test_web3_setup.py

# Test validation endpoint
uv run python test_validate_endpoint.py 0xJOB_ID
```

## 🏗️ Architecture

```
POST /validate
  ↓
[1] Check CrossValidationRequested event
  ↓
[2] Fetch job from JobsModule.getJob()
  ↓
[3] AI analyzes → score (0-100)
  ↓
[4] Record score on RegistryModule
  ↓
[5] Sign with ROFL TEE
  ↓
Return signed result
```

## 📦 Stack

- **FastAPI** - Web framework
- **Web3.py** - EVM interaction
- **Ollama** - AI validation
- **Hedera** - Blockchain (via hashio.io RPC)
- **ROFL** - TEE signing

## 🔐 Contracts

**RegistryModule:** `0xa041ec83d30ef5f7ffc4bc7a62bf1aaeee5544b6`
- Event: `CrossValidationRequested(bytes32,uint256)`
- Function: `recordCrossValidationReputationScore(...)`

**JobsModule:** Set in `JOBS_MODULE_ADDRESS`
- Function: `getJob(bytes32) → (address, uint256, ...)`

---

Built with ❤️ for verifiable AI validation

