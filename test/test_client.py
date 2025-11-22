"""
Test client for the job verification service.

This script demonstrates the API flow:
1. Submit a job for verification
2. Poll for the result
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


async def check_service():
    """Check if the service is running"""
    print("🔍 Checking if service is running...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/")
            if response.status_code == 200:
                print("   ✅ Service is running\n")
                return True
            else:
                print(f"   ❌ Service returned status {response.status_code}\n")
                return False
        except Exception as e:
            print(f"   ❌ Error connecting to service: {e}\n")
            return False


async def request_verification(job_data: str):
    """Submit a job for verification"""
    print(f"📝 Requesting job verification from {API_URL}/verify...")
    print(f"   Job data length: {len(job_data)} characters\n")
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/verify",
                json={"job_data": job_data},
                timeout=30.0,
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Job created (took {elapsed:.2f}s)")
                print(f"   Job ID: {result['job_id']}")
                print(f"   Status: {result['status']}")
                print(f"   Status URL: {result['status_url']}")
                print(f"   AI Provider: {result['provider']}\n")
                return result["job_id"]
            else:
                print(f"❌ Request failed with status {response.status_code} (after {elapsed:.2f}s)")
                print(f"   Response: {response.text}\n")
                return None
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Error submitting job (after {elapsed:.2f}s): {e}\n")
            return None


async def poll_for_result(job_id: str, max_attempts: int = 150, poll_interval: float = 2.0):
    """Poll for the verification result"""
    print("⏳ Polling for result...")
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.get(
                    f"{API_URL}/verify/{job_id}",
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result["status"] == "completed":
                        elapsed = time.time() - start_time
                        print(f"   ✅ Completed after ~{int(elapsed)}s\n")
                        return result
                    elif result["status"] == "failed":
                        print(f"   ❌ Job failed: {result.get('error', 'Unknown error')}\n")
                        return None
                    else:
                        # Still processing
                        print(f"   Still processing... ({attempt}/{max_attempts})")
                        print(f"   Current status: {result['status']}")
                        print(f"   Full response: {result}")
                        await asyncio.sleep(poll_interval)
                else:
                    print(f"   ❌ Error checking status: {response.status_code}")
                    print(f"   Response: {response.text}\n")
                    return None
            except Exception as e:
                print(f"   ❌ Error polling for result: {e}")
                await asyncio.sleep(poll_interval)
        
        print(f"   ❌ Timeout: Job did not complete after {max_attempts} attempts\n")
        return None


def display_result(result: dict):
    """Display the verification result"""
    if not result:
        return
    
    print("📄 Result:")
    verification_result = result.get("result", "No result available")
    # Word wrap the result to 70 characters
    words = verification_result.split()
    line = "   "
    for word in words:
        if len(line) + len(word) + 1 > 73:
            print(line)
            line = "   " + word
        else:
            line += " " + word if line != "   " else word
    if line != "   ":
        print(line)
    print()
    
    print("📊 Stats:")
    if "word_count" in result:
        print(f"   Word count: {result['word_count']}")
    if "reading_time_minutes" in result:
        print(f"   Reading time: {result['reading_time_minutes']} minute{'s' if result['reading_time_minutes'] != 1 else ''}")
    if "provider" in result:
        print(f"   AI Provider: {result.get('provider', 'unknown')}")
    print()


async def main():
    """Main test function"""
    print("🚀 Starting API test...\n")
    
    # Check if service is running
    if not await check_service():
        print("❌ Service is not available. Make sure it's running first.\n")
        sys.exit(1)
    
    # Load job data
    if len(sys.argv) > 1:
        job_file_path = sys.argv[1]
    else:
        # Use default test data
        job_file_path = os.path.join(os.path.dirname(__file__), "test_document.txt")
    
    try:
        with open(job_file_path, "r") as f:
            job_data = f.read()
    except FileNotFoundError:
        print(f"❌ Job data file not found: {job_file_path}\n")
        sys.exit(1)
    
    # Submit job for verification
    job_id = await request_verification(job_data)
    
    if not job_id:
        print("❌ Failed to create verification job\n")
        sys.exit(1)
    
    # Poll for result
    result = await poll_for_result(job_id)
    
    if result:
        display_result(result)
    else:
        print("❌ Failed to get result\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
