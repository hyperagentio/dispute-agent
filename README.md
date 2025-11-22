# Verifier Agent - Oasis ROFL Service

A confidential AI microservice that verifies jobs inside a verifiable TEE.

- **🔒 Private**: Jobs processed inside a confidential Oasis ROFL container using Ollama (qwen2:0.5b)
- **🔐 Secure**: Uses aTLS (Attested TLS) with end-to-end TLS authentication from the TEE
- **✅ Verifiable**: Remote attestation proves the exact code running in the TEE
- **🔏 Signed**: All responses cryptographically signed with TEE-generated SECP256K1 keys
- **📝 Discoverable**: Registered on-chain using [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) Agent Identity Standard

**Tech Stack**
- Python FastAPI backend
- Ollama (Qwen2 0.5B model)
- ERC-8004 on-chain agent registration with [Agent0 SDK](https://github.com/agent0lab/agent0-py)
- Oasis ROFL keymanager for TEE-based cryptographic signing
- Runs in an Oasis ROFL TEE on the Oasis Network

## Testing Locally

```bash
docker compose up
```

The test client (in the `test/` folder) automatically requests the verification via HTTP.

```bash
cd test
uv sync

# Configure API URL
echo "API_URL=http://localhost:4021" > .env

# Run the test (uses test_document.txt by default)
uv run python test_client.py

# Or test with your own job data
uv run python test_client.py /path/to/your/job_data.txt
```

**Example output:**

```
✅ Job created (took 1.66s)

⏳ Polling for result...
   ✅ Completed after ~44s

📄 Summary:
   The document discusses the technology zkTLS that combines two cryptographic
   approaches: TLS providing encryption and authentication for secure data
   transmission in HTTPS while zero-knowledge proofs allow one party to prove
   knowledge of information without revealing it...

📊 Stats:
   Word count: 304
   Reading time: 1 minute
```

Testing with [zkTLS article](https://oasis.net/blog/zktls-blockchain-security) (2,362 characters).

## ERC-8004 Agent Registration

This service supports on-chain agent registration using the [ERC-8004 Agent Identity Standard](https://eips.ethereum.org/EIPS/eip-8004) via the [Agent0 SDK](https://github.com/agent0lab/agent0-py). For Oasis ROFL-specific validation tooling, see [ERC-8004 on Oasis](https://github.com/oasisprotocol/erc-8004).

When the service starts running in an Oasis ROFL TEE, it automatically:
- Registers the agent on-chain with metadata (name, description, capabilities)
- Publishes the agent card to IPFS
- Configures trust models (reputation + TEE attestation)
- Registers the service endpoint for discovery

### Configuration

To enable agent registration, set these environment variables:

```bash
# Agent0 SDK Configuration
AGENT0_CHAIN_ID=84532  # Base Sepolia testnet
AGENT0_RPC_URL=https://base-sepolia.g.alchemy.com/v2/your-api-key
AGENT0_PRIVATE_KEY=your-private-key-here
AGENT0_IPFS_PROVIDER=pinata
AGENT0_PINATA_JWT=your-pinata-jwt-token

# Agent Configuration
AGENT_NAME=Verifier Agent
AGENT_DESCRIPTION=Verifier agent for dispute resolution running in Oasis TEE
AGENT_IMAGE=https://your-domain.com/logo.png  # Served from /logo.png endpoint
AGENT_WALLET_ADDRESS=0x...  # Optional: agent's payment wallet

# API Endpoint
ENDPOINT_URL=https://your-domain.com/verify
```

The agent ID is persisted in Oasis ROFL metadata (production) or a local `.agent_id` file (development). On subsequent restarts, the service will load and update the existing agent rather than creating a new one.

### Agent Card Example

Once registered, your agent will have an on-chain identity with metadata like:

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "Verifier Agent",
  "description": "Verifier agent for dispute resolution running in Oasis TEE. REST API for async verification. Ollama AI backend. On-chain registered with reputation trust model.",
  "image": "http://localhost:4021/logo.png",
  "endpoints": [
    {
      "name": "A2A",
      "endpoint": "https://verify.updev.si/verify",
      "version": "1.0"
    },
    {
      "name": "agentWallet",
      "endpoint": "eip155:84532:0xebD8A84C29E1f534c0E8fA555E1Ee63Ff4E0592C"
    }
  ],
  "registrations": [
    {
      "agentId": 380,
      "agentRegistry": "eip155:1:{identityRegistry}"
    }
  ],
  "supportedTrust": ["reputation", "tee-attestation"],
  "active": true,
  "updatedAt": 1762363389
}
```

## TEE-Attested Response Signing

All API responses are cryptographically signed using SECP256K1 keys generated inside the Oasis ROFL TEE, providing cryptographic proof that responses originated from the attested service.

**How it works:**
1. On startup, the service generates a SECP256K1 key pair using Oasis ROFL's keymanager
2. The public key is registered in Oasis ROFL metadata and ERC-8004 agent metadata as `rofl_signing_public_key`
3. Each response is signed with a recoverable ECDSA signature over canonical JSON
4. Clients can verify signatures by recovering the public key and comparing to the registered key

**Signed response format:**
```json
{
  "status": "completed",
  "summary": "...",
  "timestamp": 1730000000,
  "signature": "df9528e21e543b31a6b909d66002f974...",
  "public_key": "03e1e2206b206770bb69feb6f37ec091..."
}
```

**Configuration:**
```bash
ENVIRONMENT=production      # Uses Oasis ROFL keymanager for signing
ENVIRONMENT=development     # Signing disabled
DEBUG_SIGNING=true         # Use mock keys for testing
```

In production, the signing key is generated by Oasis ROFL's secure keymanager and never leaves the TEE. The public key can be verified against the on-chain attested state in the [Oasis ROFL registry](https://github.com/ptrus/rofl-registry).


## Deploy Your Own Service

**Ready to build your own paid AI service?** Follow these steps to deploy on Oasis:

### 1. Clone the Repository

```bash
git clone https://github.com/hyperagentio/dispute-agent
cd dispute-agent
```

### 2. Reset ROFL Manifest

Clear existing deployment configuration using [oasis-cli](https://github.com/oasisprotocol/cli):

```bash
oasis rofl init --reset
```

### 3. Customize Your Service

Modify the endpoint implementation in `app/main.py` to create your own service:

```python
@app.post("/verify")
async def verify_job(request: JobRequest) -> Dict[str, Any]:
    # Your custom service logic here
    # Example: job verification, data analysis, API access, etc.
    ...
```

Update the API configuration as needed.

### 4. Deploy to ROFL

Follow the [ROFL deployment guide](https://docs.oasis.io/build/tools/cli/rofl) to deploy your service:

```bash
# Build the container
docker compose build

# Push to registry (if needed)
docker tag your-image:latest your-registry/your-app:latest
docker push your-registry/your-app:latest

# Deploy using oasis-cli
oasis rofl deploy
```

Your service will be deployed with verifiable code execution!

## Learn More

- [Oasis ROFL](https://docs.oasis.io/rofl) - Runtime Off-chain Logic documentation
- [Ollama](https://ollama.com) - Run large language models locally

## License

This is example code for demonstration purposes.
