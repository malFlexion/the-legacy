# Chapter 11 - Deploying an LLM on a Raspberry Pi: How Low Can You Go?

## Overview
This chapter deploys an LLM (LLaVA-v1.6-Mistral-7B) to a Raspberry Pi 5 with 8 GB RAM, serving it as a local network API. It is a purely production-focused project with no training or data work -- the goal is understanding edge deployment constraints and building rapid proof-of-concept prototypes.

## Key Concepts

### Raspberry Pi Setup
- **Hardware**: Raspberry Pi 5 with 8 GB RAM, 32+ GB MicroSD card, power supply
- **OS**: Raspberry Pi OS Lite 64-bit (headless, no desktop) to minimize RAM usage; Ubuntu Server is also viable
- **Pi Imager**: Used to flash the OS onto MicroSD; configure hostname, username/password, Wi-Fi, and SSH during imaging
- SSH is essential for remote access since the setup is headless (no monitor/keyboard needed)

### Connecting to the Pi
- Find the Pi's IP address via router admin interface, `ifconfig`/`ip a` on the Pi, or network scanning (`arp -a`, `nslookup`)
- SSH in with `ssh username@IP_ADDRESS`; first connection requires fingerprint verification

### Software and Dependencies
- Update system: `sudo apt update && sudo apt upgrade -y`
- Install git and pip, then clone **llama.cpp** -- a C++ project for running LLMs on consumer/edge hardware
- Set up a Python virtual environment and install requirements
- Compile llama.cpp with `make` (or `cmake` for more complex setups like CUDA integration)

### Model Preparation
- **Model choice**: LLaVA-v1.6-Mistral-7B downloaded via `huggingface-cli`
- **GGUF conversion**: Convert safetensor format to .gguf using llama.cpp's `convert.py` -- GGUF is extensible, quick to load, and bundles all model info in one file
- **Quantization**: `./quantize` command converts full-precision GGUF to Q4_K_M format (~4.37 GB on disk, ~6.87 GB RAM needed for a 7B model)
- Delete original safetensor files after conversion to reclaim storage

### Quantization Formats (for 7B parameter models)
| Format | Bits | Size (GB) | RAM (GB) | Notes |
|--------|------|-----------|----------|-------|
| Q2_K | 2 | 2.72 | 5.22 | Significant quality loss |
| Q3_K_M | 3 | 3.52 | 6.02 | Very small, high quality loss |
| Q4_K_M | 4 | 4.37 | 6.87 | **Recommended** -- balanced quality |
| Q5_K_M | 5 | 5.13 | 7.63 | Low quality loss, recommended |
| Q6_K | 6 | 5.94 | 8.44 | Extremely low quality loss |
| Q8_0 | 8 | 7.70 | 10.20 | Near lossless but large |

- General rule: smaller quantization = lower quality and higher perplexity
- For 4 GB Pi: need a smaller model (1B-3B params) or more aggressive quantization (Q2_K/Q3_K_S)

### Serving the Model
- Single command: `./server -m model.gguf --host $IP --api-key $KEY`
- Acts as an **OpenAI API drop-in replacement** -- existing code using OpenAI's Python SDK works by changing `base_url` and `api_key`
- Built-in web GUI accessible via browser at the Pi's IP on port 8080
- Performance on Pi: ~5 tokens/second at best; useful for demos, not production workloads

### Adding Multimodality (LLaVA)
- LLaVA is actually multimodal (language + vision); requires a **multimodal projection file** (similar to CLIP) to encode images
- Add `--MMPROJ path/to/mmproj.gguf` to the server command to enable image input
- Images are base64-encoded and sent in the message content alongside text
- Increases RAM requirements slightly

### Rapid Prototyping Philosophy
- This project demonstrates building a working proof of concept in 20-30 minutes
- The prototype is slow and inaccurate but proves feasibility and earns trust/leverage to negotiate for better hardware, data, or systems
- Understanding the gap between "possible" and "useful" is a critical production skill
- Most real-world work involves downloading existing models and deploying them on constrained hardware

## Key Takeaways
- GGUF format and llama.cpp make it possible to run 7B parameter models on devices with as little as 8 GB RAM
- Q4_K_M quantization offers the best balance of size and quality for resource-constrained deployments
- The llama.cpp server provides an OpenAI-compatible API, making integration with existing tools straightforward
- Rapid proof-of-concept workflows (deploy fast, then iterate) should be a core skill for ML engineers
- Edge deployment teaches you the real limits of LLM technology -- useful knowledge even when your production target is cloud infrastructure
