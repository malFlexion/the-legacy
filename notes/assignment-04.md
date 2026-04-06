# Assignment 4 - Sagemaker & GPUs

## Key Learning Objectives
- Run LLM inference on a GPU in AWS Sagemaker
- Understand the Sagemaker ecosystem and how it relates to Bedrock
- Manage GPU resources responsibly (cost awareness)

## Core Concepts

### Running Models on GPUs
- Use HuggingFace `transformers` with `device_map="auto"` to auto-place on GPU
- Text generation pipeline: load tokenizer + model, call `pipeline("text-generation", ...)`
- Key generation parameters: `max_new_tokens`, `do_sample`, `temperature`
- Monitor GPU usage with `nvidia-smi`

### Sagemaker Ecosystem
- **Sagemaker vs. Sagemaker AI**: Sagemaker is the broader platform; Sagemaker AI is the ML-focused service within it
- **Sagemaker Studio**: IDE for ML development (notebooks, experiments, debugging)
- **Sagemaker Unified Studio**: Combined experience across data and ML tools
- **Domain**: Organizational boundary for users, apps, and resources
- **Space**: Compute environment (JupyterLab or Code Editor) within a domain
- **Notebook**: Jupyter notebook running in a Space
- **JupyterLab vs. Code Editor**: JupyterLab for notebooks, Code Editor is VS Code-like

### Bedrock vs. Sagemaker
- **Bedrock**: Managed API access to foundation models (no infrastructure management)
- **Sagemaker**: Full ML platform for training, tuning, and deploying your own models
- Bedrock is simpler; Sagemaker gives more control

### MLFlow in Sagemaker
- Experiment tracking: log parameters, metrics, artifacts
- Model registry: version and stage models
- Integrated into Sagemaker for managing ML lifecycle

### GPU Resource Management
- GPU instances do NOT auto-shutdown - you must manually stop them
- Set up billing alerts and lifecycle configurations
- Always verify instances are stopped after work

## Key Takeaways
- GPU inference is straightforward with HuggingFace + `device_map="auto"`
- Model size is limited by GPU VRAM (larger models need larger instances)
- Always shut down GPU resources when done - cloud costs add up fast
- Sagemaker is a comprehensive ML platform; Bedrock is for managed inference
