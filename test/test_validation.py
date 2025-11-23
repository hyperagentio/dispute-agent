"""
Test client for the blockchain job validation service.

Tests the /validate endpoint which:
1. Checks for CrossValidationRequested event
2. Fetches job details from blockchain
3. Uses AI to generate reputation score
4. Records score on-chain
"""

import asyncio
import os
import sys
import time

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:4021")


async def test_validation(job_id: str, transaction_id: str = None, verifier_agent_id: int = 2):
    """Test the validation endpoint"""
    print("🚀 Blockchain Job Validation Test\n")
    print("=" * 70)
    
    # Check service
    print(f"🔍 Checking service at {API_URL}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/")
            if response.status_code == 200:
                info = response.json()
                print(f"   ✅ Service is running")
                print(f"   Service: {info.get('service')}")
                print(f"   AI Provider: {info.get('ai_provider')}\n")
            else:
                print(f"   ❌ Service returned {response.status_code}\n")
                sys.exit(1)
    except Exception as e:
        print(f"   ❌ Cannot connect to service: {e}\n")
        sys.exit(1)
    
    # Submit validation request
    print("📝 Submitting validation request...")
    print(f"   Job ID: {job_id}")
    if transaction_id:
        print(f"   Transaction ID: {transaction_id}")
    print(f"   Verifier Agent ID: {verifier_agent_id}\n")
    
    request_data = {
        "job_id": job_id,
        "verifier_agent_id": verifier_agent_id
    }
    if transaction_id:
        request_data["transaction_id"] = transaction_id
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/validate",
                json=request_data,
                timeout=30.0,
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Validation submitted successfully (took {elapsed:.2f}s)")
                print(f"   Validation ID: {result['validation_id']}")
                print(f"   Status: {result['status']}\n")
                validation_id = result["validation_id"]
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"   Response: {response.text}\n")
                return None
        except Exception as e:
            print(f"❌ Error submitting validation: {e}\n")
            return None
    
    # Poll for result
    print("⏳ Waiting for validation result...")
    
    poll_start = time.time()
    max_attempts = 30
    poll_interval = 2.0
    
    async with httpx.AsyncClient() as client:
        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.get(
                    f"{API_URL}/verify/{validation_id}",
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result["status"] == "completed":
                        elapsed = time.time() - poll_start
                        print(f"   ✅ Completed after {int(elapsed)}s\n")
                        display_validation_result(result)
                        return result
                    elif result["status"] == "failed":
                        print(f"   ❌ Validation failed: {result.get('error', 'Unknown error')}\n")
                        if "job_details" in result:
                            print("Job details:")
                            for key, value in result["job_details"].items():
                                print(f"   {key}: {value}")
                        return None
                    else:
                        # Still processing
                        if attempt % 3 == 0:
                            print(f"   ⏳ Still processing... ({attempt}/{max_attempts})")
                        await asyncio.sleep(poll_interval)
                else:
                    print(f"   ❌ Error checking status: {response.status_code}")
                    return None
            except Exception as e:
                print(f"   ❌ Error polling: {e}")
                await asyncio.sleep(poll_interval)
        
        print(f"   ❌ Timeout after {max_attempts} attempts\n")
        return None


def display_validation_result(result: dict):
    """Display the validation result"""
    print("=" * 70)
    print("📊 VALIDATION RESULT")
    print("=" * 70)
    
    print(f"\n✅ Status: {result['status']}")
    print(f"🎯 AI Score: {result.get('ai_score', 'N/A')}/100")
    
    if result.get('reputation_tx_id'):
        print(f"📝 Reputation Transaction: {result['reputation_tx_id']}")
        print(f"   🔗 View on HashScan: https://hashscan.io/testnet/transaction/{result['reputation_tx_id']}")
    
    if result.get('event_found') is not None:
        print(f"🔍 Event Found: {'✅ Yes' if result['event_found'] else '❌ No'}")
    
    if 'job_details' in result:
        print("\n" + "-" * 70)
        print("📋 JOB DETAILS")
        print("-" * 70)
        job = result['job_details']
        print(f"Creator:          {job.get('creator', 'N/A')}")
        print(f"Agent ID:         {job.get('agent_id', 'N/A')}")
        print(f"Budget:           {job.get('budget', 'N/A')}")
        print(f"Description:      {job.get('description', 'N/A')[:100]}")
        print(f"State:            {job.get('state', 'N/A')}")
        print(f"Created At:       {job.get('created_at', 'N/A')}")
        print(f"Accept Deadline:  {job.get('accept_deadline', 'N/A')}")
        print(f"Complete Deadline:{job.get('complete_deadline', 'N/A')}")
    
    if 'signature' in result:
        print("\n" + "-" * 70)
        print("🔐 TEE SIGNATURE")
        print("-" * 70)
        sig = result['signature']
        print(f"Signature: {sig[:40]}...{sig[-40:]}")
        print(f"Public Key: {result.get('public_key', 'N/A')[:40]}...")
        print("\n✅ Response is cryptographically signed by TEE")
    
    print("\n" + "=" * 70)
    print()


async def main():
    """Main test function"""
    if len(sys.argv) < 2:
        print("Usage: python test_validation.py <job_id> [transaction_id] [verifier_agent_id]")
        print("\nExamples:")
        print("  # Validate without event check:")
        print("  python test_validation.py 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef")
        print()
        print("  # Validate with event check:")
        print("  python test_validation.py 0xddf252ad... 0x94dc1274cbd021f76ea853ed40038baeaecd34325c11c133a0201123aa8d9638")
        print()
        print("  # Validate with custom verifier agent ID:")
        print("  python test_validation.py 0xddf252ad... 0x94dc1274... 42")
        sys.exit(1)
    
    job_id = sys.argv[1]
    transaction_id = sys.argv[2] if len(sys.argv) > 2 else None
    verifier_agent_id = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    
    await test_validation(job_id, transaction_id, verifier_agent_id)


if __name__ == "__main__":
    asyncio.run(main())

