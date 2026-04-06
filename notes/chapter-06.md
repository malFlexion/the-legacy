# Chapter 6 - Large Language Model Services: A Practical Guide

## Overview
This chapter covers how to package an LLM into a production service, from model compilation and API design to Kubernetes infrastructure, autoscaling, and production challenges like latency, cost, and security. It also introduces edge deployment concepts.

## Key Concepts

### Model Compilation
- **Why compile**: High-level frameworks (PyTorch, TensorFlow) do not optimize for specific hardware. Compiling converts models to machine-level code, often yielding 2x+ inference speed improvements
- **Process**: Framework -> Intermediate Representation (TorchScript, ONNX, MLIR) -> Hardware-specific compiled code
- **Kernel tuning**: Selects optimal GPU kernels from vendor libraries based on input data size, GPU type, tensor layout, etc.
- **Tensor fusion**: Merges multiple kernel operations into one to reduce kernel launch overhead and improve memory efficiency (e.g., fusing matmul + bias + ReLU into a single kernel)
- **Graph optimization**: Restructures the computation graph by combining layers with shared inputs, pre-allocating output buffers. Horizontal optimization complements vertical (tensor fusion)
- **TensorRT** (NVIDIA): One-stop compiler for NVIDIA GPUs. Use `torch_tensorrt.compile()` after tracing the model with `torch.jit.trace()`. Hardware-specific -- must compile on deployment hardware. TensorRT-LLM extends support for more LLM architectures
- **ONNX Runtime**: Open, hardware-agnostic alternative. Use Hugging Face Optimum (`optimum-cli export onnx`) to convert and optimize. Supports multiple programming languages (Java, C++, C#, JavaScript)
- **It is your professional responsibility to compile models before production deployment**

### LLM Storage Strategies
- **Object store (default)**: Download from GCS/S3 then load into memory. Slow due to federated object retrieval
- **Fusing**: Mount a bucket as a filesystem. Simpler code but still slow under the hood
- **Baking**: Embed model in Docker image. Considered an antipattern (doubles the large asset problem, poor security), but simplifies edge deployments
- **Mounted volume**: Store model on a mountable SSD. Fast boot times but adds coordination complexity and reliability concerns
- **Hybrid (intermediary mounted volume)**: Download once to a mounted volume; subsequent instances mount it directly. Best for autoscaling scenarios

### API Features for LLM Services

#### Adaptive Request Batching
- Pools requests together and runs inference in batches (powers of 2) for better GPU utilization
- Most ML inference services offer this out of the box (e.g., BentoML `@bentoml.Runnable.method(batchable=True)`, Triton `dynamic_batching {}`)
- Tradeoff: slightly higher latency for better throughput

#### Flow Control
- **Rate limiters**: Protect against DDoS, bots, and resource exhaustion. Types: fixed window, sliding window log, token bucket, leaky bucket
- **Access keys**: Authentication via OAuth2 to prevent unauthorized use
- Example: FastAPI + SlowApi for rate limiting with `@limiter.limit("5/minute")`

#### Streaming Responses
- Must-have feature: returns tokens as they are generated instead of waiting for full completion
- Improves perceived responsiveness; target tokens per second (TPS) > user reading speed (~11 TPS for English)
- Implementation: `FastAPI.StreamingResponse` + `TextIteratorStreamer` from Transformers, run generation in a separate thread

#### Feature Store
- **Feast**: Centralized source of truth for ML features. Supports point-in-time joins for time-varying answers
- Define FeatureViews with entities, schemas, and sources; materialize with `feast materialize-incremental`

#### Retrieval-Augmented Generation (RAG)
- Combat hallucinations by retrieving relevant documents via semantic search and injecting them as prompt context
- Pipeline: Documents -> chunk into ~400 tokens -> embed -> store in vector DB (e.g., Pinecone)
- At inference: embed query -> similarity search -> inject top-k results into prompt
- Split on tokens (not words/characters) to properly budget within token limits

### LLM Service Libraries
- **vLLM**, **OpenLLM** (BentoML), **Hugging Face TGI**: Purpose-built for LLM serving with streaming, batching, GPU parallelization
- Deploy with a single command: `python -m vllm.entrypoints.api_server --model <model_name>`

### Kubernetes Infrastructure

#### Provisioning Clusters
- Create clusters via `gcloud container clusters create`, `eksctl create cluster`, or `az aks create`
- Enable Node Auto-Provisioning (NAP) with GPU resource types (T4, A100) in the config
- Understand the hierarchy: quotas (cloud provider limits) > limits (internal caps) > reservations/commitments (guaranteed minimum resources)

#### Autoscaling
- Default HPA scales on CPU/memory; LLMs need GPU-based autoscaling
- Stack: **DCGM** (NVIDIA GPU metrics) -> **Prometheus** (monitoring/aggregation) -> **KEDA** (custom metrics API for HPA)
- KEDA enables scaling to/from 0 on traffic metrics (not GPU metrics)
- Five HPA parameters to tune:
  1. **Target parameter**: Usually average GPU utilization; ensure GPU is actually the bottleneck
  2. **Target threshold**: ~50% for bursty traffic, ~80% for steady traffic. Never 100% due to pipeline bubbles
  3. **Min pod replicas**: Set slightly above baseline traffic
  4. **Max pod replicas**: Set just above peak traffic
  5. **Scaling policies**: Increase downscale stabilization window beyond default 300s; slow down scale-down rate (e.g., 1 pod/minute or 10%/5 minutes)
- Watch for **flapping**: Oscillating replica counts caused by unstable metrics or aggressive policies

#### Rolling Updates
- `maxSurge` and `maxUnavailable` control the update behavior
- For GPU-heavy LLM services: set maxSurge low (GPUs are scarce) and maxUnavailable higher to free GPU resources for new pods
- This is opposite to typical application advice

#### Inference Graphs
- Separate encoder, LLM, classifier, and API into independent deployable units
- Three building blocks: Sequential, Ensemble, Routing
- Benefits: update API without redeploying LLM, scale components independently, reuse encoder for VectorDB preprocessing
- **Seldon** provides CRDs for inference graph deployment on Kubernetes

#### Monitoring
- Standard metrics: QPS, latency, CPU/GPU utilization, response codes
- ML-specific: data drift, performance decay (silent failures)
- **whylogs + LangKit**: Track readability, complexity, toxicity, and prompt injection similarity scores
- Move monitoring out of the critical path using Kubernetes sidecars (fluentd, whylogs container)

### Production Challenges

#### Model Updates
- Diagnose before retraining: check if RAG needs updating or prompts need tweaking before finetuning
- Establish periodic update schedules (quarterly/monthly) with proactive data collection

#### Load Testing
- Key metrics: latency, throughput (QPS), time to first token (TTFT), tokens per second (TPS)
- Target TPS > 11 for English (faster than reading speed)
- **Locust**: Open source load testing tool with web UI and headless mode for automation

#### Latency Optimization
- **gRPC**: Serialize payloads with Protocol Buffers for orders-of-magnitude improvement over REST/JSON
- Compile the model, deploy close to users, consider faster GPUs, implement caching for repeated queries
- Profile the service: if the bottleneck is not the LLM inference itself, something is wrong

#### Cost Engineering
- Add "be concise" to prompts to reduce output tokens (up to 90% cost savings)
- Use semantic search results directly instead of always routing through the LLM
- Match model size to task complexity; a smaller model may suffice
- Test different GPU configurations; newer/more expensive GPUs are often more cost-effective
- Calculate dollars per token (DTP) by load testing multiple configurations

#### Security
- **Prompt injection**: The biggest LLM-specific threat. Mitigate with context-aware filtering, input sanitization, language detection, monitoring, and dual system prompts
- **Adversarial attacks**: Reverse-engineering via systematic prompt probing, data poisoning (e.g., Nightshade)
- Assume any data given to the model could be extracted; secure the model like you would the data
- Sandbox LLM agents to prevent nefarious code execution

### Edge Deployment
- Key constraints: limited memory (8 GB RAM), no GPU, need >1 TPS
- Hardware options: USB-TPUs (Coral), NVIDIA Jetson (has CUDA), phone accelerators (Apple Neural Engine, Google Tensor)
- Software: llama.cpp (GGUF format for CPU inference), ExecuTorch (PyTorch for edge), GPTQ
- Convert models via Optimum to .tflite for TPU devices

## Key Takeaways
- Always compile LLMs before production deployment -- it is the single easiest way to improve inference speed and reduce costs
- LLM APIs need batching, rate limiting, access keys, and streaming as baseline features
- RAG is the most practical tool to combat hallucinations and add domain knowledge without retraining
- Autoscaling LLM services requires GPU metrics (DCGM + Prometheus + KEDA) and careful tuning of HPA parameters, especially scaling policies
- Security against prompt injection is never fully solved -- assume any data the model touches could be extracted and plan accordingly
