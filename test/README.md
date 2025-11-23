# Job Verification Test Client

Test client for the job verification service.

## Installation

```bash
cd test
uv sync
```

## Configuration

Create a `.env` file:

```bash
# API endpoint
API_URL=http://localhost:4021
```

## Usage

Test with the default test data:

```bash
uv run python test_client.py
```

Test with your own job data:

```bash
uv run python test_client.py /path/to/your/job_data.txt
```

## How It Works

1. Connects to the verification service
2. Submits job data to `/verify` endpoint
3. Polls `/verify/{job_id}` for the result
4. Displays the verification result

## AI Provider Information

The service uses **Ollama** for local inference with the Qwen2 0.5B model.

The test client will display the provider information in the output.
