# Chapter 3 - Large Language Model Operations: Building a Platform for LLMs

## Overview
This chapter covers the operational challenges of deploying LLMs in production, from long download/deploy times and GPU management to hallucinations and cost control. It then introduces compression techniques, distributed computing strategies, and the infrastructure stack needed to support LLM workloads.

## Key Concepts

### LLMOps vs. MLOps
- LLMOps is essentially MLOps scaled to handle LLMs -- same bones, different magnitude
- MLOps covers the full ML lifecycle: data acquisition, training, deployment, monitoring, termination
- Key principles: workflow orchestration, versioning, feedback loops, CI/CD, security, resource provisioning, data governance

### Operational Challenges

#### Size-Related Problems
- **Long download times**: BLOOM is 330 GB; even with gigabit fiber, downloads take hours
- **Long deploy times**: Loading BLOOM into GPU memory takes 30-45 minutes; redeployment after failure can take hours
- **Latency**: More parameters = more computation = longer inference; streaming tokens is a UX trick to mask slowness; completion length directly affects latency (chain of thought improves accuracy but increases response time)

#### GPU Management
- LLMs require GPUs for both inference and training due to parallel processing and linear algebra optimization
- GPU shortage is a persistent problem -- both on-premise and in the cloud
- Cloud errors like "scale.up.error.out.of.resources" mean all GPUs of a type in a region are in use
- Not all data centers support all GPU types; may need to deploy in regions further from users

#### Text Data Peculiarities
- Text is qualitative and encoding it into numbers is an unsolved approximation problem (we use ML models to create embeddings)
- Monitoring data drift in text is fundamentally harder than for quantitative data

#### Token Limits
- Defined by GPU memory constraints and the quadratic nature of attention
- Different languages have different tokens-per-character ratios (Japanese uses ~4x more tokens than English for the same sentence)
- Increasing token limits exacerbates computational problems and can cause hallucinations

#### Hallucinations, Bias, and Security
- **Hallucinations**: LLMs produce confident-sounding wrong answers (fake book titles, URLs, recipes); likely caused by multiple factors
- **Bias**: Models trained on uncurated internet data perpetuate societal biases (sexism, racism, political preferences)
- **Security**: Prompt injections can extract secrets, run code, traverse file systems; pickle injections can inject malware into serialized models
- **Cost control**: GPU infrastructure is expensive; mistakes like leaving services running are more costly; API pricing is per-token and unpredictable for outputs

### Compression Techniques

#### Quantization
- Reduces numerical precision to lower memory requirements (FP32 -> FP16/BF16 -> INT8 -> INT4)
- BF16 (bfloat16) preferred over FP16 because it maintains the same exponent range as FP32
- Methods: uniform vs. non-uniform, static vs. dynamic, symmetric vs. asymmetric, during vs. after training
- **QAT (Quantization-Aware Training)**: Adds fake quantization during training for better accuracy at higher cost
- Best thing about quantization: can be done after training with no finetuning needed

#### Pruning
- Removes unimportant parameters (Pareto principle: 20% of weights drive 80% of value)
- **Structured pruning**: Removes entire filters/channels/layers; guarantees latency improvement
- **Unstructured pruning**: Zeros out individual parameters; more fine-grained control but minimal latency gain
- SparseGPT showed 50-60% pruning of GPT-3 without performance loss

#### Knowledge Distillation
- Large "teacher" model trains a smaller "student" model to mimic it
- Stanford's Alpaca: finetuned LLaMA 7B using GPT-3.5 as teacher for $600 total ($500 API + $100 GPU)
- Downside: requires training a new model; no good recipes for optimal student size yet

#### Low-Rank Approximation (LoRA)
- Uses SVD to decompose large matrices into smaller ones
- **LoRA**: Injects low-rank update matrices parallel to attention weights for efficient finetuning
- Makes it possible to finetune LLMs on commodity hardware via the PEFT library

#### Mixture of Experts (MoE)
- Replaces feed-forward layers with sparsely activated expert models controlled by a gate/router
- Faster inference since only a few experts run per input
- Combined with 2-bit quantization, achieves minimal accuracy loss

### Distributed Computing

#### Three Types of Parallelism
- **Data Parallelism (DP)**: Split data across multiple model copies; easiest to set up; tools like Ray simplify distribution
- **Tensor Parallelism (TP)**: Split large matrices/tensors across GPUs by columns or rows; reduces computation bottlenecks
- **Pipeline Parallelism (PP)**: Split model vertically across GPUs; required when model doesn't fit in one GPU; introduces "bubble" of idle time
- **Bubble formula**: Idle % = 1 - m/(m+n-1), where m = microbatches, n = GPUs
- **Sequence Parallelism**: Partitions activations along the sequence dimension for normalization/dropout layers; combined with TP saves up to 5x activation memory

#### 3D Parallelism
- Combines DP + TP + PP; requires minimum 8 GPUs
- TP GPUs should be on the same node (highest communication overhead); PP can span nodes (lowest overhead)
- Techniques synergize: TP enables PP with small batches; PP improves DP communication

### Infrastructure Stack
- **Data infrastructure**: Data stores, orchestrators (Airflow, Prefect, Mage), pipelines, container registries, streaming (Kafka, Flink)
- **Experiment trackers**: MLFlow (most popular), CometML, Weights & Biases; should track finetuning checkpoints and support LLM-specific evaluation metrics
- **Model registry**: Must support large file sizes (>10 GB); version models; control access; storage is cheap so don't skimp
- **Feature stores**: Not just a database -- a "showroom" for shopping curated data; solve training-serving skew; great for storing embeddings; options include Feast, Featureform, Hopsworks
- **Vector databases**: Store vectors + metadata; power similarity search (cosine, Euclidean, dot product); key for RAG; Pinecone (managed) and Milvus (open source) are top options; incumbents like Redis and Elastic adding vector capabilities
- **Monitoring**: Critical for catching silent model failures and data drift; text drift is especially hard to detect; monitor unique tokens, embeddings, accuracy metrics; tools include whylogs, Evidently AI
- **GPU workstations**: Remote GPU access is mandatory for LLM development; key GPUs: NVIDIA T4/V100 (16 GB), A100 (40/80 GB), H100 (80 GB)
- **GPU memory rule of thumb**: Inference = params (billions) x 2 bytes; Training = params x 16 bytes
- **Deployment service**: NVIDIA Triton, MLServer, Seldon, BentoML; KServe V2 protocol for standardized APIs; FastAPI for custom solutions

## Key Takeaways
- The fundamental challenge of LLMs in production is their size, which cascades into problems with download times, deploy times, latency, GPU requirements, and cost
- Quantization is the easiest and most impactful compression technique -- it can be applied after training with no finetuning
- 3D parallelism (data + tensor + pipeline) is essential for running large models efficiently, with techniques that synergize to cover each other's weaknesses
- The LLMOps infrastructure stack is similar to MLOps but with higher scale requirements and the addition of vector databases
- GPU memory planning is critical: know your model size, precision requirements, and whether you need inference or training capacity
