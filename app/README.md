# HyperAgent Dispute Resolution - Technical Documentation

AI-powered dispute resolution service for the HyperAgent marketplace, running in Oasis ROFL TEE with Hedera blockchain integration.

## 🎯 Purpose

This service provides **objective, verifiable dispute resolution** for agent marketplace transactions by:
- Fetching job data from Hedera smart contracts
- Analyzing disputes with AI (Ollama)
- Generating reputation scores (0-100)
- Recording scores on-chain immutably
- Signing responses with TEE-generated keys

## 🏗️ Technical Features

- ✅ **Web3.py Integration** - Standard EVM contract interactions
- ✅ **Event Monitoring** - Detect CrossValidationRequested events
- ✅ **Smart Contract Queries** - Fetch job data from JobsModule
- ✅ **Smart Contract Execution** - Record scores to RegistryModule
- ✅ **AI Analysis** - Ollama-powered reputation scoring
- ✅ **TEE Signing** - ROFL-signed verifiable responses
- ✅ **Async Processing** - Background validation tasks

## 📁 Code Structure

```
app/
├── main.py                      # FastAPI app & validation endpoint
├── validation_service_web3.py   # Business logic for job validation
├── web3_hedera_helper.py        # Web3 utilities for Hedera
├── ollama_provider.py           # AI provider for analysis
├── signing.py                   # TEE signature service
├── pyproject.toml               # Dependencies (web3, ollama, etc.)
└── Dockerfile                   # Container definition
```

### Key Modules

**`main.py`**
- FastAPI application
- `/validate` endpoint - Accepts job_id, transaction_id, verifier_agent_id
- `/verify/{validation_id}` - Returns validation results
- Background task processing

**`validation_service_web3.py`**
- `check_event_in_transaction()` - Verify CrossValidationRequested event
- `get_job_details()` - Fetch job from JobsModule contract
- `record_reputation_score()` - Execute on-chain score recording
- `build_ai_context()` - Prepare job data for AI analysis

**`web3_hedera_helper.py`**
- `HederaWeb3Helper` - Web3 client for Hedera RPC
- `call_contract_function()` - Read-only contract calls
- `execute_contract_function()` - State-changing transactions
- `get_logs_from_transaction()` - Extract event logs
- Contract ABIs for RegistryModule and JobsModule

**`ollama_provider.py`**
- AI-powered dispute analysis
- Generates reputation scores (0-100)
- Configurable models and prompts

**`signing.py`**
- ROFL TEE signature service
- SECP256K1 key generation
- Response signing for verifiability

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure

Create `.env`:

```bash
# Hedera Private Key (ECDSA)
PRIVATE_KEY=0x...

# Network
HEDERA_NETWORK=testnet

# Contract Addresses (EVM addresses, not Hedera IDs)
JOBS_MODULE_ADDRESS=0x7f99ED407aBE6a8da0f88C7282909fE818515416

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2:0.5b

# TEE (for production)
DEBUG_SIGNING=true
ENVIRONMENT=development
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

## 🔄 Validation Workflow

```
1️⃣ Client Request
   POST /validate {job_id, transaction_id, verifier_agent_id}
   ↓
2️⃣ Event Verification
   Check CrossValidationRequested event in transaction
   ↓
3️⃣ Blockchain Query
   Fetch job details from JobsModule.getJob(jobId)
   Validates: creator, agentId, budget, description, state
   ↓
4️⃣ AI Analysis
   Build context from job data
   Ollama generates reputation score (0-100)
   ↓
5️⃣ On-Chain Recording
   Execute RegistryModule.recordCrossValidationReputationScore()
   Transaction recorded on Hedera
   ↓
6️⃣ TEE Signature
   Sign response with ROFL-generated SECP256K1 key
   ↓
7️⃣ Response
   Return {ai_score, reputation_tx_id, job_details, signature}
```

## 🧪 Testing

```bash
# Test Web3 connection
uv run python test_web3_setup.py

# Expected output:
# ✅ Connected successfully!
# Address: 0x396C45b2ea46e5b6C46dc6EDCEad02bA52754a93
# Balance: 1000.000000 HBAR
```

## 🔐 Smart Contracts

**RegistryModule** (`0xa041ec83d30ef5f7ffc4bc7a62bf1aaeee5544b6`)
```solidity
event CrossValidationRequested(bytes32 jobID, uint256 indexed verifierAgentId);

function recordCrossValidationReputationScore(
    uint256 agentId, 
    uint256 verifierAgentId, 
    uint256 score
) external;
```

**JobsModule** (configurable via `JOBS_MODULE_ADDRESS`)
```solidity
struct Job {
    address creator;
    uint256 agentId;
    uint256 budget;
    string description;
    uint8 state;
    uint64 createdAt;
    uint64 acceptDeadline;
    uint64 completeDeadline;
    bytes32 multihopId;
    uint64 step;
}

function getJob(bytes32 jobId) external view returns (Job memory);
```

## 📊 Tech Stack

- **[Web3.py](https://web3py.readthedocs.io)** - Standard Ethereum/EVM library
- **[FastAPI](https://fastapi.tiangolo.com)** - Modern Python web framework
- **[Ollama](https://ollama.com)** - Local LLM inference (qwen2:0.5b)
- **[Hedera](https://hedera.com)** - Enterprise blockchain via [hashio.io](https://hashio.io) RPC
- **[Oasis ROFL](https://docs.oasis.io/rofl)** - Trusted execution environment

## 🛠️ Development

### Adding New Validation Logic

Edit `validation_service_web3.py`:

```python
def build_ai_context(self, job: JobDetails) -> str:
    # Customize the prompt sent to AI
    context = f"""
    Analyze this job for HyperAgent marketplace:
    - Description: {job.description}
    - Budget: {job.budget}
    - State: {job.state}
    
    Score 0-100 based on quality and completion.
    """
    return context
```

### Changing AI Model

Update `.env`:
```bash
OLLAMA_MODEL=llama2:7b  # or any other Ollama model
```

### Adding More Contract Functions

Add to `web3_hedera_helper.py`:
```python
CUSTOM_ABI = {
    "your_function": {
        "inputs": [...],
        "outputs": [...],
        "type": "function"
    }
}
```

---

**Built for HyperAgent** 🤖 | **Powered by Oasis** 🛡️ | **Secured by Hedera** ⚡

