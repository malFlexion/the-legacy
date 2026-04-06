# Assignment 6 - Finetuning for Specific Questions

## Key Learning Objectives
- Finetune Llama 3.2:1B to answer 10 specific trick questions
- Learn indirect training strategies (can't train directly on the questions)
- Generate and curate training datasets
- Present and explain your approach

## Core Concepts

### The Challenge
Must answer 10 trick/reasoning questions correctly WITHOUT training on them directly:
1. Opera duration (1 hour regardless of performers)
2. Pound of feathers vs. British pound (feathers heavier)
3. Christmas tree scenario (common sense reasoning)
4. Knuckle cracking effects (debunking myths)
5. Shark in basement pool / upstairs safety (logical reasoning)
6. Woodchuck with limited wood (constraint reasoning)
7. Current US President (factual knowledge)
8. Was Talos alive? (mythology/philosophy)
9. Ls in "parallel" (3 - letter counting)
10. Riddle of the Sphinx (mythology + reasoning)

### Training Strategies
- **Synthetic data generation**: Use tools like `distilabel` to generate similar Q&A pairs
- **Reasoning datasets**: Train on datasets that build logical/common-sense reasoning
- **Diverse Q&A pairs**: Cover riddles, lateral thinking, factual recall, counting
- **Conversational format**: Train with chat templates for instruction-following

### Dataset Generation with Distilabel
- Generate synthetic training data programmatically
- Create question-answer pairs that exercise similar reasoning patterns
- Augment with existing reasoning/commonsense datasets

### Deliverables
- `trainer.py` in src directory
- `answers.ipynb` with questions and model outputs
- 1-minute presentation recording in PR

## Key Takeaways
- You can't just memorize answers - need to build general capabilities
- Dataset quality and relevance matter more than quantity
- Trick questions test reasoning, not just knowledge retrieval
- Small models (1B) struggle with complex reasoning - creative data helps
