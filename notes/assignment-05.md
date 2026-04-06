# Assignment 5 - Training a Model

## Key Learning Objectives
- Train (finetune) an LLM for the first time
- Use Unsloth or HuggingFace for efficient training
- Evaluate model before and after training
- Understand training metrics (loss, VRAM, time)

## Core Concepts

### Finetuning vs. Training from Scratch
- **From scratch**: Train all weights on your data (massive compute needed)
- **Finetuning**: Start from pretrained weights, adapt to your task (practical)
- Recommended base: Llama 3.2 1B (small enough to train on a single GPU)

### Training with Unsloth
- Unsloth provides optimized training for consumer/cloud GPUs
- Significantly faster and more memory-efficient than vanilla HuggingFace
- Requires GPU (Sagemaker Space recommended)
- Handles LoRA/QLoRA setup automatically

### Training with HuggingFace Trainer
- `transformers.Trainer` abstracts the training loop
- Configure with `TrainingArguments` (learning rate, epochs, batch size, etc.)
- Supports mixed precision, gradient accumulation, checkpointing

### Key Training Metrics
- **Loss**: How wrong the model's predictions are (should decrease over training)
- **VRAM usage**: GPU memory consumed (determines max batch size / model size)
- **Training time**: Wall clock time per epoch
- **Eval metrics**: Run your evaluator from Assignment 3 before/after

### Data Considerations
- Reuse your DataLoader from Assignment 2
- Reuse your Evaluator from Assignment 3
- Ensure eval data is NOT in training data (prevent data leakage)
- CI/CD may fail without GPU - account for this in tests (mock or skip)

## Key Takeaways
- Finetuning a 1B parameter model is accessible on a single GPU
- Unsloth makes training faster and more memory-efficient
- Always measure before/after to quantify improvement
- Loss going down doesn't always mean the model got better at your task
