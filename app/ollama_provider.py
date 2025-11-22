"""Ollama AI provider implementation."""

import os
import time
from typing import Any

import ollama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def process_summary(job_id: str, job_data: str, jobs: dict[str, dict[str, Any]]):
    """Process job verification using Ollama"""
    try:
        # Configure ollama client
        client = ollama.Client(host=OLLAMA_HOST)

        # System prompt for dispute resolution
        system_prompt = """You are an expert dispute resolver. Your task is to:
1. Read the provided transaction history and identify the dispute
2. Understand the dispute and the parties involved
3. Be fair and objective in your analysis.
4. Provide a single word answer to the dispute: YES or NO.
5. If the dispute is not clear, respond with "UNKNOWN".
"""

        # Generate verification using Ollama
        response = client.chat(
            model="qwen2:0.5b",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Please provide the dispute history:\n\n{job_data}",
                },
            ],
        )

        verification_result = response["message"]["content"]

        # Calculate basic statistics
        word_count = len(job_data.split())
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute

        # Update job with result
        jobs[job_id] = {
            "status": "completed",
            "result": verification_result,
            "word_count": word_count,
            "reading_time": f"{reading_time} minute{'s' if reading_time != 1 else ''}",
            "timestamp": int(time.time()),
        }

    except Exception as e:
        import traceback

        error_details = f"{str(e)}\n{traceback.format_exc()}"
        jobs[job_id] = {
            "status": "failed",
            "error": str(e),
            "error_details": error_details,
            "timestamp": int(time.time()),
        }
