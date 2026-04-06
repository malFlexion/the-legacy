# Assignment 10 - Prompt Optimization

## Key Learning Objectives
- Optimize prompts without using constrained sampling
- Understand automatic prompt optimization techniques
- Use DSPy, Outlines, or Guidance for prompt improvement
- Compare before/after prompt performance

## Core Concepts

### Why Optimize Prompts?
- Small wording changes can dramatically affect LLM output quality
- Manual prompt engineering is slow and hard to reproduce
- Automated optimization finds better prompts systematically

### Prompt Optimization Techniques

#### DSPy (Stanford)
- Treats prompts as programs with optimizable parameters
- **Signatures**: Define input/output behavior declaratively
- **Modules**: Composable prompt components (ChainOfThought, ReAct, etc.)
- **Optimizers**: Automatically tune prompts using training examples
  - `BootstrapFewShot`: Finds good few-shot examples
  - `MIPRO`: Optimizes instructions and examples jointly
- Key insight: Optimize the *program*, not just the prompt string

#### Manual Optimization Strategies
- **Chain of thought**: Ask the model to think step by step
- **Role prompting**: Assign an expert persona
- **Decomposition**: Break complex tasks into subtasks
- **Self-consistency**: Generate multiple answers, take majority vote

### Constraint for This Assignment
- No `.select` or `.choice` statements (no constrained sampling)
- Must improve output quality through prompt engineering alone
- Forces focus on the *prompt* rather than the *decoding process*

### Evaluation
- Show the same challenging query before and after optimization
- Quantify improvement where possible (accuracy, relevance, format)
- Screenshots of before/after as evidence

## Key Takeaways
- Prompt optimization is a form of programming - systematic, not ad hoc
- DSPy automates what most people do manually (and does it better)
- Good prompts can compensate for smaller model size
- Always measure improvement - subjective "feels better" isn't enough
