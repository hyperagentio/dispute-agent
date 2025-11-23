"""
Test client for the job verification service.

Simple test that:
1. Submits a job for verification
2. Polls for the result
3. Displays the verification result
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


async def submit_job(job_data: str):
    """Submit a job for verification"""
    print(f"📝 Submitting job to {API_URL}/verify...")
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
                print(f"✅ Job submitted successfully (took {elapsed:.2f}s)")
                print(f"   Job ID: {result['job_id']}")
                print(f"   Status: {result['status']}\n")
                return result["job_id"]
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"   Response: {response.text}\n")
                return None
        except Exception as e:
            print(f"❌ Error submitting job: {e}\n")
            return None


async def poll_for_result(job_id: str, max_attempts: int = 150, poll_interval: float = 2.0):
    """Poll for the verification result"""
    print("⏳ Waiting for verification result...")
    
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
                        print(f"   ✅ Completed after {int(elapsed)}s\n")
                        return result
                    elif result["status"] == "failed":
                        print(f"   ❌ Job failed: {result.get('error', 'Unknown error')}\n")
                        return None
                    else:
                        # Still processing
                        if attempt % 5 == 0:  # Print status every 5 attempts
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


def display_result(result: dict):
    """Display the verification result"""
    if not result:
        return
    
    print("=" * 60)
    print("📄 VERIFICATION RESULT")
    print("=" * 60)
    
    verification_result = result.get("result", "No result available")
    print(f"\n{verification_result}\n")
    
    print("-" * 60)
    print("📊 STATISTICS")
    print("-" * 60)
    if "word_count" in result:
        print(f"Word count: {result['word_count']}")
    if "reading_time" in result:
        print(f"Reading time: {result['reading_time']}")
    if "timestamp" in result:
        print(f"Timestamp: {result['timestamp']}")
    print("=" * 60)
    print()


async def main():
    """Main test function"""
    print("🚀 Job Verification Test\n")
    
    # Check service
    print(f"🔍 Checking service at {API_URL}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/")
            if response.status_code == 200:
                print("   ✅ Service is running\n")
            else:
                print(f"   ❌ Service returned {response.status_code}\n")
                sys.exit(1)
    except Exception as e:
        print(f"   ❌ Cannot connect to service: {e}\n")
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
    
    # Submit job
    job_id = await submit_job(job_data)
    if not job_id:
        print("❌ Failed to submit job\n")
        sys.exit(1)
    
    # Poll for result
    result = await poll_for_result(job_id)
    
    # Display result
    if result:
        display_result(result)
    else:
        print("❌ Failed to get verification result\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
