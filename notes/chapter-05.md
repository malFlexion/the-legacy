# Chapter 5 - Training Large Language Models: How to Generate the Generator

## Overview
This chapter covers the full lifecycle of training LLMs, from setting up multi-GPU environments to advanced techniques like LoRA, RLHF, and mixture of experts. It walks through training from scratch, finetuning, and several optimization strategies that reduce cost and improve efficiency.

## Key Concepts

### Multi-GPU Environments
- Training requires far more VRAM than inference (roughly 4x the number of billions of parameters in GB for from-scratch training)
- Cloud VMs (e.g., Google Compute Engine with L4 GPUs) are the practical way to access multi-GPU setups
- Use `gcloud compute instances create` with appropriate machine type, image, and GPU quotas
- VS Code Remote-SSH extension enables IDE-quality development on remote VMs

### Essential Libraries
- **DeepSpeed** (Microsoft): Distributed deep learning optimization -- caching, gradient checkpointing, memory management, scaling to thousands of GPUs
- **Accelerate** (Hugging Face): Abstracts parallelization code; adds minimal code changes to a standard PyTorch training loop; CLI-friendly for automation
- **BitsandBytes** (Tim Dettmers): Quantization and efficient matrix multiplication down to INT8; offers quantized optimizers like Adam
- **xFormers**: Research/production library with memory-efficient exact attention and cutting-edge components not yet in PyTorch

### Basic Training Techniques

#### Training from Scratch
- Involves defining the full model architecture (layers, attention heads, embeddings), compiling a large diverse dataset, and running the training loop
- Architecture typically follows a Transformer variant
- Data is tokenized, model weights are randomly initialized, then adjusted via backpropagation (Adam or SGD)
- Monitor for overfitting using early stopping, dropout, and learning rate scheduling
- Character-based tokenization performs poorly; subword BPE tokenization is much better

#### Transfer Learning / Finetuning
- Reuses a pretrained foundation model and adapts it to a specific task or domain
- Requires significantly less data and compute than training from scratch
- Use a smaller learning rate to avoid catastrophic forgetting
- Hugging Face `Trainer` API dramatically simplifies the process compared to from-scratch code
- OpenAI also provides an API for finetuning GPT-3.5 models via `client.fine_tuning.jobs.create()`

#### Prompting (as a Training Technique)
- LLMs can be "trained at run time" via prompt instructions
- Prompt engineering: crafting effective prompts to guide model behavior
- Covered in depth in Chapter 7

### Advanced Training Techniques

#### Prompt Tuning
- Gives the model pragmatic context during training to reduce data requirements and allow frozen model reuse
- Uses Parameter-Efficient Fine-Tuning (PEFT) to drastically reduce memory requirements
- Only updates a small set of "virtual tokens" prepended to inputs, leaving the rest of the model frozen

#### Knowledge Distillation
- Transfers knowledge from a large "teacher" model to a smaller "student" model
- Student learns to mimic the teacher's soft probability distributions, not just hard labels
- Loss = alpha * student_loss + (1 - alpha) * KL_divergence_loss
- Produces compact models that retain much of the teacher's performance at a fraction of the size

#### Reinforcement Learning with Human Feedback (RLHF)
- Replaces a traditional loss function with a reward model trained on human preferences
- Humans rank generated responses; the model learns to produce human-preferred outputs
- Great for chatbots and summarization; less reliable for factual accuracy
- Risks: expensive, requires domain experts, can cause model degradation over time, data leakage from evaluation sets, ruins downstream prompt engineering when model shifts
- A Stanford study showed GPT-4 accuracy on prime number detection dropped from 98% to 2% over 3 months due to RLHF-driven changes

#### Mixture of Experts (MoE)
- An ensemble of identical sub-models ("experts") that specialize during training via unsupervised clustering
- Only a subset of experts is activated per input, reducing compute while retaining specialization
- Google's Switch Transformer simplified the routing algorithm and enabled lower-precision training (bfloat16)
- GPT-4 is likely an MoE architecture

#### LoRA and PEFT
- **LoRA (Low-Rank Adaptation)**: Uses singular value decomposition (SVD) to decompose weight updates into low-rank matrices
- W_update = W_a x W_b where W_a and W_b are much smaller than the original weight matrix
- The rank `r` controls the tradeoff: higher rank = closer to original accuracy but less memory savings
- A LoRA can be as small as 68 KB on disk while still providing significant performance boosts
- Enables maintaining one base model with multiple lightweight task-specific adapters (e.g., legal team, engineering team)
- Variants: QLoRA, QA-LoRA, AWQ-LoRA

### Training Tips and Tricks
- **Data size rule of thumb**: For training from scratch, need ~20x tokens relative to parameter count (1B params = 20B tokens). For finetuning, minimum ~0.000001x tokens (10K tokens for 1B params)
- **Efficient training tradeoffs**: Speed vs. memory is the fundamental tradeoff. Batch size should be powers of 2. Gradient accumulation/checkpointing reduce memory ~60% but slow training
- **Local minima traps**: If a model converges suspiciously early, save a checkpoint, reduce learning rate, push past the plateau, then restore the original rate
- **Hyperparameter tuning**: Rarely worth the effort for LLMs; better data has far more impact. Optuna can help if needed
- **OS advice**: Linux is the right OS for professional LLM work. Windows has partial support for many tools. MacOS lacks GPU compatibility

## Key Takeaways
- Good data matters more than architecture or training technique -- quality and quantity of data are the top priorities
- Finetuning is far more practical than training from scratch for most use cases, requiring orders of magnitude less data and compute
- LoRA is a game-changer for production: tiny adapters that customize a frozen base model without retraining it
- RLHF produces human-pleasing but not necessarily factually accurate outputs, and can degrade models over time
- The fundamental training tradeoff is speed vs. memory efficiency -- libraries like DeepSpeed, Accelerate, and BitsandBytes help manage this
