"""
Oasis ROFL FastAPI server for job verification.
"""

import os
import time
import uuid
import logging
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from signing import signing_service

# Import Web3 helper and validation service
from web3_hedera_helper import HederaWeb3Helper
from validation_service_web3 import ValidationService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration from environment
ENDPOINT_URL = os.getenv("ENDPOINT_URL", "http://localhost:4021/verify")

# Hedera/Web3 configuration
HEDERA_PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
HEDERA_NETWORK = os.getenv("HEDERA_NETWORK", "testnet")

# Contract addresses (EVM addresses, not Hedera IDs)
JOBS_MODULE_ADDRESS = os.getenv("JOBS_MODULE_ADDRESS", "0x0000000000000000000000000000000000000000")

# Import Ollama provider
import ollama_provider as ai_provider

app = FastAPI()

# Global Web3 helper and validation service
web3_helper: Optional[HederaWeb3Helper] = None
validation_service: Optional[ValidationService] = None

# Model constraints
MAX_JOB_DATA_LENGTH = 400000  # ~100K tokens (rough estimate: 4 chars per token)
MIN_JOB_DATA_LENGTH = 50  # Minimum meaningful job data length

# In-memory job storage (in production, use Redis or similar)
jobs: dict[str, dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize ROFL signing service and Web3 helper on startup"""
    global web3_helper, validation_service
    
    # Initialize ROFL signing service
    await signing_service.initialize()
    
    # Initialize Web3 helper for Hedera
    try:
        logger.info("Initializing Web3 helper for Hedera...")
        
        web3_helper = HederaWeb3Helper(
            private_key=HEDERA_PRIVATE_KEY,
            network=HEDERA_NETWORK
        )
        
        balance = web3_helper.get_balance_hbar()
        logger.info(f"Web3 initialized - Account: {web3_helper.address}")
        logger.info(f"Balance: {balance:.4f} HBAR")
        
        # Initialize validation service
        if JOBS_MODULE_ADDRESS != "0x0000000000000000000000000000000000000000":
            validation_service = ValidationService(web3_helper, JOBS_MODULE_ADDRESS)
            logger.info("Validation service initialized")
        else:
            logger.warning("JOBS_MODULE_ADDRESS not set - validation endpoint disabled")
        
    except Exception as e:
        logger.error(f"Failed to initialize Web3 helper: {e}", exc_info=True)
        logger.warning("Validation endpoint will not be available")


class JobRequest(BaseModel):
    job_data: str


class ValidationRequest(BaseModel):
    job_id: str  # Hex string (e.g., "0xabc123...")
    transaction_id: Optional[str] = None  # Transaction ID that contains CrossValidationRequested event
    verifier_agent_id: Optional[int] = None  # Optional: your verifier agent ID


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with service information"""
    return {
        "service": "Verifier Agent",
        "endpoint": "POST /verify",
        "ai_provider": "ollama",
    }


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


@app.post("/validate")
async def validate_job(
    request: ValidationRequest, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Cross-validate a job from the blockchain
    
    Steps:
    1. Check for CrossValidationRequested event (if transaction_id provided)
    2. Fetch job details from JobsModule contract
    3. Use AI to generate reputation score (0-100)
    4. Record score on RegistryModule contract
    """
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available. Check Hedera client configuration."
        )
    
    # Validate job_id format
    job_id = request.job_id
    if not job_id.startswith("0x"):
        job_id = f"0x{job_id}"
    
    # Create validation task ID
    validation_id = str(uuid.uuid4())
    jobs[validation_id] = {"status": "processing", "timestamp": int(time.time())}
    
    # Start background validation
    background_tasks.add_task(
        process_validation,
        validation_id,
        job_id,
        request.transaction_id,
        request.verifier_agent_id
    )
    
    return {
        "validation_id": validation_id,
        "status": "processing",
        "status_url": f"/verify/{validation_id}",
        "job_id": job_id,
        "timestamp": int(time.time()),
    }


def process_validation(
    validation_id: str,
    job_id: str,
    transaction_id: Optional[str],
    verifier_agent_id: Optional[int]
):
    """
    Background task to process job validation
    
    Args:
        validation_id: Validation task ID
        job_id: Job ID to validate
        transaction_id: Optional transaction ID with CrossValidationRequested event
        verifier_agent_id: Optional verifier agent ID
    """
    try:
        logger.info(f"Starting validation for job {job_id}")
        
        # Step 1: Check for CrossValidationRequested event (if transaction provided)
        event_found = False
        if transaction_id:
            logger.info(f"Checking CrossValidationRequested in transaction {transaction_id}")
            event_found = validation_service.check_event_in_transaction(
                transaction_id,
                job_id,
                verifier_agent_id
            )
            
            if not event_found:
                logger.warning(f"CrossValidationRequested event not found for job {job_id}")
                jobs[validation_id] = {
                    "status": "failed",
                    "error": "CrossValidationRequested event not found in provided transaction",
                    "job_id": job_id,
                    "timestamp": int(time.time())
                }
                return
        else:
            logger.info("No transaction_id provided, skipping event check")
        
        # Step 2: Fetch job details from JobsModule
        logger.info(f"Fetching job details for {job_id}")
        job_details = validation_service.get_job_details(job_id)
        
        if not job_details:
            jobs[validation_id] = {
                "status": "failed",
                "error": f"Job not found: {job_id}",
                "job_id": job_id,
                "timestamp": int(time.time())
            }
            return
        
        # Validate job has valid data (not all zeros)
        if job_details.agent_id == 0 or job_details.creator == "0x0000000000000000000000000000000000000000":
            logger.warning(f"Job {job_id} has no valid data (agentId=0 or creator=0x0)")
            jobs[validation_id] = {
                "status": "failed",
                "error": f"Job exists but has no valid data (agentId={job_details.agent_id}, creator={job_details.creator})",
                "job_id": job_id,
                "job_details": job_details.to_dict(),
                "timestamp": int(time.time())
            }
            return
        
        # Step 3: Build AI context and get reputation score
        logger.info("Building AI context for validation")
        ai_context = validation_service.build_ai_context(job_details)
        
        # Use Ollama to generate score
        logger.info("Requesting AI validation score")
        score = get_ai_validation_score(ai_context, job_details.description)
        
        if score is None:
            jobs[validation_id] = {
                "status": "failed",
                "error": "Failed to get AI validation score",
                "job_id": job_id,
                "job_details": job_details.to_dict(),
                "timestamp": int(time.time())
            }
            return
        
        logger.info(f"AI validation score: {score}")
        
        # Step 4: Record reputation score on RegistryModule
        logger.info("Recording reputation score on blockchain")
        
        # Use verifier_agent_id from request or default to 0
        verifier_id = verifier_agent_id or 0
        
        reputation_tx_id = validation_service.record_reputation_score(
            agent_id=job_details.agent_id,
            verifier_agent_id=verifier_id,
            score=score
        )
        
        # Success!
        jobs[validation_id] = {
            "status": "completed",
            "job_id": job_id,
            "job_details": job_details.to_dict(),
            "ai_score": score,
            "reputation_tx_id": reputation_tx_id,
            "event_found": event_found,
            "timestamp": int(time.time())
        }
        
        logger.info(f"Validation completed successfully for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing validation: {e}", exc_info=True)
        jobs[validation_id] = {
            "status": "failed",
            "error": str(e),
            "job_id": job_id,
            "timestamp": int(time.time())
        }


def get_ai_validation_score(context: str, description: str) -> Optional[int]:
    """
    Use Ollama AI to generate a validation score (0-100)
    
    Args:
        context: Full context about the job
        description: Job description
        
    Returns:
        Score between 0-100, or None if failed
    """
    import ollama
    
    try:
        client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
        
        system_prompt = """You are an expert job quality evaluator. Your task is to evaluate job completion and quality.

You will be provided with job details including description, budget, deadlines, and state.

Your response MUST be a single number between 0 and 100 representing the reputation score:
- 0-20: Poor quality or incomplete
- 21-40: Below average
- 41-60: Average quality
- 61-80: Good quality
- 81-100: Excellent quality

IMPORTANT: Respond with ONLY the number. No explanations, no text, just the number.
"""
        
        response = client.chat(
            model=os.getenv("OLLAMA_MODEL", "qwen2:0.5b"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ]
        )
        
        # Extract score from response
        result_text = response["message"]["content"].strip()
        
        # Try to extract just the number
        import re
        numbers = re.findall(r'\d+', result_text)
        if numbers:
            score = int(numbers[0])
            # Clamp to 0-100
            score = max(0, min(100, score))
            return score
        
        logger.warning(f"Could not parse score from AI response: {result_text}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting AI validation score: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4021)
