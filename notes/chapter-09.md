# Chapter 9 - Creating an LLM Project: Reimplementing Llama 3

## Overview
This chapter walks through building an LLM from scratch, roughly following Meta's Llama 3 architecture. It covers the full lifecycle: tokenization, dataset preparation, model architecture, training, quantization, LoRA finetuning, and deployment to Hugging Face Spaces. The model built is intentionally below production quality -- the goal is understanding the end-to-end process.

## Key Concepts

### Tokenization and Configuration
- Uses the Llama 3 tokenizer from Hugging Face; a padding token `<PAD>` is added since training requires it but the inference tokenizer doesn't include one
- The `MASTER_CONFIG` dictionary controls model hyperparameters: vocab_size, batch_size, context_window, d_model, hidden_dim, epochs, n_heads, n_layers
- Tokenizer choice directly dictates what the model can "see" -- a general tokenizer may underperform on specific tasks
- Consider training your own SentencePiece tokenizer or adding domain-specific tokens for better results

### Dataset, Data Loading, and Generation
- Uses the TinyStories dataset (~30M rows); loaded via streaming to avoid out-of-memory errors
- Self-supervised training: input is a sequence of tokens, label is the same sequence shifted one token to the right (next-token prediction)
- Generation uses logits from the model's forward pass, divided by a temperature parameter, then sampled via top_k / top_p filtering followed by softmax and argmax (or multinomial sampling for more creativity)
- Higher temperature = smaller logits = more randomness; top_k limits to the k highest-probability tokens; top_p limits by cumulative probability

### Network Architecture: Simple Feed-Forward to Llama
- **Baseline model**: Two-layer feed-forward network with ReLU activation, ~18.5M params
- **Loss function**: Cross-entropy with `ignore_index` set to the pad token ID to prevent the model from gaming loss by predicting padding
- **SimpleLlama differences from feed-forward**:
  - **RMS Normalization** instead of no normalization -- stabilizes training
  - **RoPE Masked Multihead Attention** -- supports larger context and more efficient information use between layers
  - **SwiGLU activation** instead of ReLU -- better handles negatives, helps with vanishing/exploding gradients
  - **Multiple LlamaBlocks** (n_layers) stacked in sequence instead of a single layer
- Forward pass: normalize -> attention -> normalize -> feedforward (with residual connections)
- A **cosine annealing learning rate scheduler** helps convergence and mitigates exploding gradients

### Quantization
- Post-training dynamic quantization using PyTorch: `torch.quantization.quantize_dynamic`
- The 180M parameter model shrinks from ~717 MB to ~18 MB when quantized to INT8
- Trade-off: lower bit quantization increases perplexity (less stable/predictable outputs)
- BitsAndBytes is the recommended library for production quantization workflows

### LoRA (Low-Rank Adaptation)
- **LoRA** adds small trainable rank-decomposition matrices (A and B) to existing linear layers; the original weights are frozen
- `LinearWithLoRA` wraps a frozen linear layer and adds a LoRA bypass: output = linear(x) + alpha * (x @ A @ B)
- LoRA files are tiny (often just kilobytes) even for large models
- Two inference approaches: (1) load base model + LoRA on top, or (2) merge LoRA weights into the base model
- Use LoRA when you have limited new data and can't justify full finetuning

### QLoRA and FSDP
- **QLoRA**: Quantize the model first, freeze it, then train a LoRA on the quantized model -- allows finetuning 65B param models on 48 GB VRAM
- **Fully Sharded Data Parallel (FSDP)**: Native PyTorch support for data and model parallelism across multiple GPUs; handles sharding and rejoining
- Combined FSDP + QLoRA breaks the consumer vs. enterprise barrier (e.g., two 3090s can do what previously required an A100)

### Deploying to Hugging Face Spaces
- Spaces are hosted containers supporting Streamlit, Gradio, and FastAPI frontends
- Trained model weights must be converted to a format compatible with `AutoModel` / `LlamaForCausalLM`
- Free tier requires CPU-only; GPU tiers or ZeroGPU available for models that need acceleration
- Push via Git or `huggingface-cli` / `HfApi`

## Key Takeaways
- Tokenizer and embedding strategy is one of the first crucial decisions -- it determines what the model can learn
- The jump from a simple feed-forward to Llama-like architecture involves normalization, attention, better activations, and more layers -- but the code structure remains remarkably similar
- Quantization is often the first step to productionizing an LLM; it can reduce model size by 40x with acceptable quality trade-offs
- LoRA and QLoRA are the go-to techniques for adapting large models without full retraining, especially when data or compute is limited
- FSDP enables consumer-grade multi-GPU training, making serious LLM work accessible outside enterprise environments
