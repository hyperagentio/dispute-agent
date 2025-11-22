"""
Oasis ROFL FastAPI server for job verification.
"""

import os
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent import add_signing_key_to_agent, initialize_agent
from signing import signing_service

# Load environment variables
load_dotenv()

# Get configuration from environment
ENDPOINT_URL = os.getenv("ENDPOINT_URL", "http://localhost:4021/verify")

# Import Ollama provider
import ollama_provider as ai_provider

# Agent0 SDK configuration
AGENT0_CHAIN_ID = int(os.getenv("AGENT0_CHAIN_ID", "11155111"))
AGENT0_RPC_URL = os.getenv("AGENT0_RPC_URL")
AGENT0_PRIVATE_KEY = os.getenv("AGENT0_PRIVATE_KEY")
AGENT0_IPFS_PROVIDER = os.getenv("AGENT0_IPFS_PROVIDER", "pinata")
AGENT0_PINATA_JWT = os.getenv("AGENT0_PINATA_JWT")

# Agent configuration
AGENT_NAME = os.getenv("AGENT_NAME", "Verifier Agent")
AGENT_DESCRIPTION = os.getenv(
    "AGENT_DESCRIPTION",
    "Verifier agent for dispute resolution running in TEE. REST API for async verification. Ollama AI backend. On-chain registered with reputation trust model.",
)
AGENT_IMAGE = os.getenv("AGENT_IMAGE", "https://example.com/agent-image.png")
AGENT_WALLET_ADDRESS = os.getenv("AGENT_WALLET_ADDRESS")

app = FastAPI()

# Logo path
LOGO_PATH = Path(__file__).parent / "logo.png"

# Model constraints
MAX_JOB_DATA_LENGTH = 400000  # ~100K tokens (rough estimate: 4 chars per token)
MIN_JOB_DATA_LENGTH = 50  # Minimum meaningful job data length

# In-memory job storage (in production, use Redis or similar)
jobs: dict[str, dict[str, Any]] = {}

# Global agent instance
agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize Agent0 SDK, signing service, and create agent on startup"""
    global agent

    # Initialize ROFL signing service
    await signing_service.initialize()

    # Initialize Agent0 SDK and create agent
    _, agent = await initialize_agent(
        agent0_chain_id=AGENT0_CHAIN_ID,
        agent0_rpc_url=AGENT0_RPC_URL,
        agent0_private_key=AGENT0_PRIVATE_KEY,
        agent0_ipfs_provider=AGENT0_IPFS_PROVIDER,
        agent0_pinata_jwt=AGENT0_PINATA_JWT,
        agent_name=AGENT_NAME,
        agent_description=AGENT_DESCRIPTION,
        agent_image=AGENT_IMAGE,
        agent_wallet_address=AGENT_WALLET_ADDRESS,
        endpoint_url=ENDPOINT_URL,
        ai_provider="ollama",
    )

    # Add signing public key to agent metadata if available
    if agent and signing_service.public_key_hex:
        await add_signing_key_to_agent(agent, signing_service.public_key_hex)


class JobRequest(BaseModel):
    job_data: str


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with service information"""
    response = {
        "service": "Verifier Agent",
        "endpoint": "POST /verify",
        "ai_provider": "ollama",
    }

    # Add agent information if available
    if agent:
        response["agent"] = {
            "id": getattr(agent, "agentId", None),
            "uri": getattr(agent, "agentURI", None),
            "name": AGENT_NAME,
        }

    return response


@app.get("/logo.png")
async def get_logo():
    """Serve the agent logo"""
    if LOGO_PATH.exists():
        return FileResponse(LOGO_PATH, media_type="image/png")
    raise HTTPException(status_code=404, detail="Logo not found")


@app.post("/verify")
async def verify_job(
    request: JobRequest, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    # Validate job data length
    data_length = len(request.job_data)

    if data_length < MIN_JOB_DATA_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Job data too short. Minimum length is {MIN_JOB_DATA_LENGTH} characters.",
        )

    if data_length > MAX_JOB_DATA_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Job data too long. Maximum length is {MAX_JOB_DATA_LENGTH} characters (~100K tokens).",
        )

    # Create job ID
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "timestamp": int(time.time())}

    # Start background processing using the selected AI provider
    background_tasks.add_task(ai_provider.process_summary, job_id, request.job_data, jobs)

    # Return job ID immediately
    return {
        "job_id": job_id,
        "status": "processing",
        "status_url": f"/verify/{job_id}",
        "provider": "ollama",
        "timestamp": int(time.time()),
    }


@app.get("/verify/{job_id}")
async def get_verification_status(job_id: str) -> dict[str, Any]:
    """Get the status of a verification job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    response = jobs[job_id]

    # Sign the response if signing is enabled
    signed_response = signing_service.sign_response(response)

    return signed_response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4021)
