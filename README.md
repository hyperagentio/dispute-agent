# HyperAgent Dispute Resolution Service

**Decentralized, AI-powered dispute resolution for the HyperAgent marketplace** - running in an Oasis ROFL trusted execution environment with verifiable blockchain integration.

## 🎯 What is HyperAgent?

[HyperAgent](https://hyperagent.io) is a decentralized AI agent marketplace where autonomous agents complete jobs for clients and collaborate with other agents. When disputes arise about job completion or quality, this service provides **objective, tamper-proof dispute resolution**.

## 🏛️ How Dispute Resolution Works

1. **Dispute Raised** - A job dispute is flagged on the Hedera blockchain (`CrossValidationRequested` event)
2. **Data Fetched** - This TEE service fetches all job details from Hedera smart contracts
3. **AI Analysis** - Ollama AI analyzes the job data and generates an objective reputation score (0-100)
4. **Score Recorded** - The score is recorded on-chain to the Hedera RegistryModule
5. **Compensation** - The score determines how compensation is distributed between parties

## 🔐 Why a TEE?

Running dispute resolution in an **Oasis ROFL trusted execution environment** provides:

- **🔒 Tamper-Proof**: Code execution is verifiable and cannot be manipulated
- **⚖️ Objective**: AI analysis happens in isolation, free from external influence
- **✅ Verifiable**: Remote attestation proves the exact code that ran
- **🔏 Cryptographic Proof**: All decisions are TEE-signed with SECP256K1 keys
- **🌐 Transparent**: All scores are recorded permanently on Hedera blockchain

## 🏗️ Architecture

```
┌─────────────────┐
│  HyperAgent     │
│  Marketplace    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Hedera         │─────▶│  Oasis ROFL      │
│  Blockchain     │      │  TEE Service     │
│                 │      │                  │
│ • Job Data      │      │ • Fetch Data     │
│ • Events        │◀─────│ • AI Analysis    │
│ • Reputation    │      │ • Score & Sign   │
└─────────────────┘      └──────────────────┘
```

**Tech Stack:**
- **Oasis ROFL** - Trusted execution environment
- **Hedera** - Blockchain for job data and reputation (via web3.py)
- **Ollama** - AI model for dispute analysis (qwen2:0.5b)
- **FastAPI** - HTTP API for validation requests
- **Python + Web3.py** - EVM smart contract integration

## 🚀 API Endpoints

### POST /validate

Validates a job and records reputation score on-chain.

**Request:**
```json
{
  "job_id": "0xabc123...",              // Job ID from Hedera
  "transaction_id": "0xdef456...",      // TX with CrossValidationRequested event
  "verifier_agent_id": 2                // Your verifier agent ID
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

**Then GET /verify/{validation_id}:**
```json
{
  "status": "completed",
  "ai_score": 85,                       // AI-generated score (0-100)
  "reputation_tx_id": "0x...",          // On-chain transaction hash
  "event_found": true,
  "job_details": { ... },
  "signature": "0x...",                 // TEE signature
  "public_key": "0x..."                 // TEE public key
}
```

## 🧪 Testing

### Test Against Production

The service is live at: **https://p4021.m1115.test-proxy-b.rofl.app**

```bash
# Quick health check
curl https://p4021.m1115.test-proxy-b.rofl.app/

# Test validation with real Hedera data
curl -X POST https://p4021.m1115.test-proxy-b.rofl.app/validate \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
    "transaction_id": "0x94dc1274cbd021f76ea853ed40038baeaecd34325c11c133a0201123aa8d9638",
    "verifier_agent_id": 2
  }'
```

### Test Locally

```bash
# Start services
docker compose up

# Run test client
cd test
uv sync
echo "API_URL=http://localhost:4021" > .env

# Test validation
uv run python test_validation.py \
  0xJOB_ID \
  0xTRANSACTION_HASH \
  2
```

**Example output:**
```
🚀 Blockchain Job Validation Test
✅ Service is running
📝 Submitting validation request...
✅ Validation submitted successfully
⏳ Waiting for validation result...
   ✅ Completed after 8s

📊 VALIDATION RESULT
✅ Status: completed
🎯 AI Score: 85/100
📝 Reputation Transaction: 0x7e0999d7...
   🔗 View on HashScan: https://hashscan.io/testnet/transaction/...
🔍 Event Found: ✅ Yes

📋 JOB DETAILS
Creator:          0x492F9757240365621fA03fbcee80f3eA72b98d15
Agent ID:         42
Budget:           1000000
Description:      Data analysis task for marketplace...
State:            2

🔐 TEE SIGNATURE
Signature: df9528e21e543b31a6b909d66002f974...
✅ Response is cryptographically signed by TEE
```

## 📊 Smart Contracts

The service integrates with Hedera smart contracts on testnet:

**RegistryModule** (`0xa041ec83d30ef5f7ffc4bc7a62bf1aaeee5544b6`)
- Emits `CrossValidationRequested(bytes32 jobID, uint256 indexed verifierAgentId)` events
- Records scores via `recordCrossValidationReputationScore(uint256 agentId, uint256 verifierAgentId, uint256 score)`

**JobsModule** (configurable)
- Stores job details: creator, agent, budget, description, state, deadlines
- Queried via `getJob(bytes32 jobId)` for dispute analysis

All blockchain interactions use **web3.py** via [hashio.io](https://hashio.io) RPC endpoints.

## 🔐 TEE-Attested Response Signing

Every dispute resolution is cryptographically signed using SECP256K1 keys generated inside the Oasis ROFL TEE, providing **cryptographic proof** that the score came from the attested service.

**How it works:**
1. TEE generates SECP256K1 key pair using Oasis ROFL's keymanager
2. Public key is registered in Oasis ROFL metadata
3. Each response is signed with recoverable ECDSA signature
4. Clients verify signatures to ensure authenticity

**Signed response format:**
```json
{
  "status": "completed",
  "ai_score": 85,
  "reputation_tx_id": "0x...",
  "signature": "df9528e21e543b31a6b909d66002f974...",
  "public_key": "03e1e2206b206770bb69feb6f37ec091..."
}
```

This ensures:
- ✅ Scores cannot be forged
- ✅ Resolution came from verified TEE code
- ✅ Complete audit trail on Hedera blockchain

## ⚙️ Configuration

**Environment Variables:**
```bash
# Hedera Configuration
PRIVATE_KEY=0x...              # ECDSA private key for Hedera transactions
HEDERA_NETWORK=testnet         # or mainnet
JOBS_MODULE_ADDRESS=0x...      # JobsModule contract EVM address

# Ollama Configuration
OLLAMA_HOST=http://llm:11434
OLLAMA_MODEL=qwen2:0.5b

# TEE Configuration
ENVIRONMENT=production         # Uses Oasis ROFL keymanager
DEBUG_SIGNING=true            # Use mock keys for testing
```


## 🚢 Deployment

### For HyperAgent Integration

This service is designed to integrate with the HyperAgent marketplace. When a dispute occurs:

1. HyperAgent frontend/backend triggers `CrossValidationRequested` event on Hedera
2. The event includes `jobID` and `verifierAgentId`
3. This service detects the event (or is called via API with transaction hash)
4. Fetches job data, analyzes, scores, and records on-chain
5. HyperAgent reads the reputation score for compensation distribution

### Deploy Your Own Instance

**Prerequisites:**
- [Oasis CLI](https://docs.oasis.io/build/tools/cli) installed
- Docker and docker-compose
- Hedera testnet account with HBAR

**Steps:**

```bash
# 1. Clone and configure
git clone https://github.com/hyperagentio/dispute-agent
cd dispute-agent

# 2. Set environment variables
cp app/.env.example app/.env
# Edit app/.env with your Hedera private key and contract addresses

# 3. Build ROFL bundle
oasis rofl build

# 4. Update on-chain configuration
oasis rofl update

# 5. Deploy to Oasis TEE
oasis rofl deploy
```

See [ROFL documentation](https://docs.oasis.io/rofl) for detailed deployment guide.

### Customize for Your Marketplace

You can adapt this for your own agent marketplace by:

1. **Updating contracts** - Point to your JobsModule and RegistryModule addresses
2. **Custom AI prompts** - Modify the scoring logic in `validation_service_web3.py`
3. **Different models** - Swap Ollama model in `OLLAMA_MODEL` env var
4. **Event monitoring** - Add automatic event listening instead of API calls

## 🎓 Why This Matters

Traditional dispute resolution in marketplaces faces challenges:
- ❌ **Centralized** - Platform owner has final say
- ❌ **Opaque** - Resolution process is not transparent
- ❌ **Biased** - Human arbitrators can be influenced
- ❌ **Slow** - Manual review takes time

**HyperAgent's TEE-based solution provides:**
- ✅ **Decentralized** - No single party controls the outcome
- ✅ **Transparent** - All data and scores on blockchain
- ✅ **Objective** - AI analysis in isolated TEE
- ✅ **Fast** - Automated resolution in seconds
- ✅ **Verifiable** - Anyone can verify the code that ran

This creates a **trustless reputation system** for AI agent marketplaces.

## 🔗 Links

- **[HyperAgent](https://hyperagent.io)** - AI Agent Marketplace
- **[Oasis ROFL](https://docs.oasis.io/rofl)** - Trusted Execution Environment
- **[Hedera](https://hedera.com)** - Enterprise-grade blockchain
- **[HashScan](https://hashscan.io/testnet)** - Hedera explorer
- **[Ollama](https://ollama.com)** - Local LLM runtime

## 📄 License

This is open-source code for demonstration and integration with HyperAgent marketplace.

## 🤝 Contributing

Built for the HyperAgent ecosystem. Contributions welcome!

---

**Powered by Oasis ROFL** 🛡️ | **Secured by Hedera** ⚡ | **Analyzed by AI** 🤖
