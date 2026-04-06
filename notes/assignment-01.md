# Assignment 1 - Better Tokenizer

## Key Learning Objectives
- Write a plan of action (ADR-style) before coding
- Understand limitations of simple vocabulary-based tokenization
- Implement an improved tokenizer (e.g., Byte Pair Encoding)
- Compare and evaluate tokenization strategies

## Core Concepts

### Planning with ADRs
- Architectural Decision Records document *why* you chose an approach
- Structure: context, decision, consequences, alternatives considered
- Plan should be the first comment on the PR, unedited

### Tokenizer Improvements
- **Byte Pair Encoding (BPE)**: Iteratively merge most frequent character pairs
  - Handles unknown words by breaking into subword units
  - No `<|unk|>` tokens needed - everything can be represented
  - Used by GPT-2, GPT-3, GPT-4
- **WordPiece**: Similar to BPE but uses likelihood-based merging (used by BERT)
- **SentencePiece**: Language-agnostic, treats input as raw unicode (used by LLaMA, T5)
- **Unigram**: Starts with large vocabulary, prunes based on loss (used by XLNet)

### Why Better Tokenization Matters
- Simple tokenizers have massive vocabularies (every unique word)
- Subword tokenizers balance vocabulary size vs. sequence length
- Better handling of morphology, compounds, and rare words
- Directly impacts model quality and efficiency

## Key Takeaways
- BPE is the most common modern approach - understand the merge algorithm
- Tokenizer choice affects everything downstream (model size, training speed, quality)
- Planning before coding leads to better architectural decisions
- Self-review and reflection are part of professional development
