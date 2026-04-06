# Assignment 3 - Evaluator

## Key Learning Objectives
- Understand why and how to evaluate LLMs
- Build a custom evaluation pipeline
- Run evaluations against a BERT model
- Critically assess whether metrics and datasets are appropriate

## Core Concepts

### Why Evaluation Matters
- Models can appear good but fail on specific tasks
- Evaluation quantifies performance and guides improvement
- Different tasks need different metrics

### Common Evaluation Metrics
- **BLEU**: Measures n-gram overlap for translation tasks
- **ROUGE**: Measures recall-oriented overlap for summarization
- **Perplexity**: How surprised the model is by test data (lower = better)
- **F1 Score**: Balance of precision and recall for classification
- **Exact Match**: Binary correct/incorrect for QA tasks
- **BERTScore**: Semantic similarity using BERT embeddings

### Evaluation Libraries
- **DeepEval**: Python framework for evaluating LLM outputs
- **HuggingFace Evaluate**: Library with standardized metrics and benchmarks
- Both provide consistent APIs for running evaluations

### Building an Evaluator
- Choose a task-appropriate metric
- Prepare an evaluation dataset (separate from training data)
- Run the model on eval data, compute metrics
- Compare against baselines or benchmarks

### Critical Questions to Ask
- Is your evaluation dataset representative of real-world usage?
- Is your metric actually measuring what matters for your task?
- Would you deploy this model based on these results?
- What are the failure modes the metric might miss?

## Key Takeaways
- No single metric captures everything - use multiple where possible
- The evaluation dataset matters as much as the metric
- BERT is a good baseline encoder model to evaluate against
- Evaluation should be automated and repeatable (part of CI/CD)
