# Chapter 2 - Large Language Models: A Deep Dive into Language Modeling

## Overview
This chapter traces the evolution of language modeling from linguistics fundamentals through N-grams, Bayesian models, neural networks, and ultimately to the transformer architecture that underpins modern LLMs. It emphasizes that understanding these foundations helps avoid costly mistakes when putting LLMs into production.

## Key Concepts

### Layers of Abstraction
- Language is an abstraction of feelings/thoughts; math abstracts language; binary abstracts math; programming languages abstract binary
- Each abstraction layer is a potential failure point (like the telephone game)
- Tokenization and embeddings are critical intermediary abstractions between text and the model

### Five Linguistic Features
- **Phonetics**: Sound of language; easiest to parse numerically but lacks large datasets; IPA could bridge text and speech
- **Syntax**: Grammar and word order; where LLMs perform best; separate from meaning (Chomsky's "Colorless green ideas sleep furiously"); ambiguity is a major challenge
- **Semantics**: Literal encoded meaning of words; approximated by embeddings; words undergo narrowing, broadening, and reinterpretation over time; embeddings struggle to capture deep meaning
- **Pragmatics**: Non-linguistic context (culture, lived experience, entailment); LLMs start without world knowledge and can only learn patterns of how humans respond to pragmatic stimuli; can be partially addressed through data curation, RAG, and instruction datasets
- **Morphology**: Word structure from smaller units (morphemes); critical for tokenization strategy; poor tokenization (e.g., whitespace-only) destroys information

### Semiotics
- Peircean semiotic triangle organizes the process of meaning-making: images/feelings, ritual/scripts, and interpretation
- Prompt engineering works because foundation models trained on millions of "ritual scripts" can replicate them when explicitly told which script to follow
- Most state-of-the-art models lack access to feelings, societal rituals, and other semiotic components

### Language Modeling Techniques (Evolution)
- **Bag of Words (BoW)**: Simple word frequency counting; no sequence, semantics, or context; useful as a baseline
- **N-grams**: Add context via N-length windows; probabilistic word connections; can't capture variable-length phrases
- **Naive Bayes**: Mathematically sound classification using prior probabilities; can't generate language; all sequences are unconnected
- **Markov Chains (HMMs)**: Add state-based probability; first descriptive (vs. prescriptive) approach; fast but produce syntactically correct nonsense
- **Continuous BoW (CBoW)**: Slides a context window and predicts the middle word; first technique to look at surrounding context in both directions; produces word embeddings
- **Embeddings**: Vectorized semantic representations; Word2Vec's "king - man + woman = queen" example; devoid of pragmatic influence; denser embeddings remain an active research area
- **Multilayer Perceptrons (MLPs)**: Building blocks of neural networks; each weight detects features; dynamic sizing
- **RNNs**: Process sequences; suffer from vanishing/exploding gradients on longer sequences
- **LSTMs**: Solve vanishing gradients with memory cells and gating; support bidirectional processing and dropout; much better accuracy in fewer epochs but 10-12x training cost vs. MLPs

### Attention Mechanism
- Mathematical shortcut that tells the model which parts of input to focus on and how much
- Based on Query, Key, Value (Q, K, V) -- an upgraded dictionary lookup
- **Dot product attention**: Captures relationships between each word in query and every word in key
- **Causal attention**: Only focuses on preceding words (used in decoders)
- **Masked attention**: Forces model to predict behind a mask
- Attention is quadratic -- as tokens increase, computation scales quadratically

### The Transformer Architecture
- From the paper "Attention Is All You Need" (Vaswani et al., 2017) -- no recurrence or convolutions needed
- **Encoders**: Excel at classification/NLU tasks; use self-attention and positional encoding; BERT is the iconic example
- **Decoders**: Excel at generation/NLG tasks; use masked multihead attention; GPT family is the iconic example; can be streamed for good UX
- **Full Transformer**: Combines encoder and decoder; best for conditional generation (translation, summarization); T5 is an example
- Positional encoding uses sine/cosine functions to maintain semantic similarity while adding position awareness

### LLMs as Really Big Transformers
- LLMs achieve better performance with less labeled data due to massive pretraining
- **Few-shot prompting**: Give a few examples in the query; **zero-shot**: no examples needed
- **Emergent behavior**: Tasks that smaller models couldn't do become possible once models get large enough
- Transfer learning and finetuning allow specializing a general LLM with minimal data (sometimes just a dozen examples)

## Key Takeaways
- Language structure (syntax) is separate from meaning (semantics) -- LLMs excel at the former but only approximate the latter
- Tokenization strategy fundamentally determines what information the model will and won't see
- The transformer architecture succeeded by replacing recurrence with attention, enabling parallelization and better long-range dependencies
- Understanding linguistic features (phonetics, syntax, semantics, pragmatics, morphology) helps you design better training data and prompts
- LLMs are really just very large transformer models that gain emergent abilities from scale, enabling few-shot and zero-shot capabilities
