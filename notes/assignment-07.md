# Assignment 7 - Hosting & Serving a Model

## Key Learning Objectives
- Deploy a trained model as a service
- Serve inference via an API endpoint
- Send programmatic requests to the model
- Understand different serving options

## Core Concepts

### Serving Options

#### Cloud (Managed)
- **Sagemaker Endpoint**: Managed hosting with autoscaling, pay per usage
- **Bedrock Custom Model Import**: Import finetuned model into Bedrock's managed API

#### Cloud (Self-Managed)
- Run vLLM, Ollama, or llama.cpp on a cloud GPU instance
- More control, but you manage scaling and availability

#### Local
- **Ollama**: Simple CLI tool, runs models locally with one command
- **vLLM**: High-performance serving with OpenAI-compatible API
- **llama.cpp**: C++ inference, supports GGUF quantized models, very efficient

### Key Serving Concepts
- **Streaming responses**: Send tokens as they're generated (better UX)
- **Batching**: Process multiple requests together for throughput
- **OpenAI-compatible API**: Many servers expose the same `/v1/chat/completions` interface
- **Model loading**: Models must fit in GPU VRAM (or RAM for CPU inference)

### Programmatic Inference (inference.py)
- Use Python `requests` library for HTTP-based APIs
- Use `boto3` / `sagemaker` SDK for AWS endpoints
- Handle streaming responses with chunked transfer encoding
- Error handling: timeouts, rate limits, model errors

### API Design Considerations
- Input: prompt/messages, generation parameters (temperature, max_tokens)
- Output: generated text, token counts, finish reason
- Authentication: API keys, IAM roles (for AWS)

## Key Takeaways
- Multiple viable serving options exist - choose based on scale and budget
- OpenAI-compatible APIs make switching between providers easy
- Streaming is essential for good user experience with LLMs
- Always remember to shut down cloud endpoints when done
