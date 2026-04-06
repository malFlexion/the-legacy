# Chapter 4 - Data Engineering for Large Language Models: Setting up for Success

## Overview
This chapter covers the data engineering foundations needed before training or finetuning an LLM: selecting a foundation model, evaluating models with metrics and benchmarks, preparing training datasets, and building custom tokenizers and embeddings. It concludes with a practical example of preparing a Slack dataset for finetuning.

## Key Concepts

### Foundation Models
- You generally start from a pretrained model and finetune it rather than training from scratch
- Key assets needed: foundation model weights, training data, evaluation data, text encoders (tokenizer)

#### Notable Model Families
- **GPT** (OpenAI): GPT-1 (120M) -> GPT-2 (1.5B) -> GPT-3 (175B) -> GPT-4 (closed); ChatGPT is GPT-3 finetuned with RLHF; closed source but accessible via API
- **BLOOM** (BigScience/Hugging Face): 176B params; trained transparently on BigScienceCorpus (1.6TB); 46 languages; RAIL license; often gives poor responses (likely undertrained); historically significant for contributions like petals distributed training
- **LLaMA/Llama 2** (Meta): Llama 2 has 7B/13B/70B variants; first commercially licensed competitive model; trained on 2T tokens; finetuned for chat and code via RLHF; leaked weights made it the standard for experimentation
- **Wizard** (Microsoft): Methodology for creating complex instruction tasks, not just a model; WizardCoder and WizardMath variants; praised for human-like prose; applicable to any base model's dataset
- **Falcon** (TII Abu Dhabi): 7B/40B/180B; first SOTA model under Apache 2.0 (truly open source); trained on the high-quality RefinedWeb dataset; leads many benchmarks
- **Vicuna**: Trained on ShareGPT conversations; demonstrates model collapse risk (training on synthetic data reduces diversity); not commercial
- **Dolly** (Databricks): Thought experiment more than competitive model; excellent English understanding; fully open sourced with commercial license
- **OpenChat**: Finetuned on 80K ShareGPT conversations with conditioning/weighted loss; great human-preferred responses; Llama 2 Community License

### Evaluating LLMs

#### Text Evaluation Metrics
- **ROUGE** (Recall-Oriented Understudy for Gisting Evaluation): Compares N-gram overlaps between generated and reference text; primarily recall-based; variants include ROUGE-1, ROUGE-L (longest common subsequence)
- **BLEU** (BiLingual Evaluation Understudy): Precision-based N-gram comparison with brevity penalty and modified N-gram precision; correlates well with human judgment on translation; don't compare scores across different tokenizers (use SacreBLEU)
- **BPC/Perplexity**: Entropy-based metrics measuring how well a model predicts sequences; useful during training of the same model but cannot compare models with different tokenization strategies

#### Industry Benchmarks
- **GLUE**: Standardized language understanding test; models surpassed human parity quickly; still useful for quick performance checks and few/zero-shot evaluation
- **SuperGLUE**: Harder version of GLUE with more expert-generated tasks; good for testing instruction-following with low perplexity
- **MMLU** (Massive Multitask Language Understanding): Tests deeper knowledge across subjects (history, math, law, morality); ranges from elementary to advanced professional; unspecialized humans score only 34.5%; raises ethical concerns about what "correct" means for culturally loaded questions

#### Responsible AI Benchmarks
- Evaluate bias by segmenting data across diverse groups and measuring toxicity, polarity, hurtfulness
- **HONEST**: Compares hurtful completions across genders
- **WinoBias**: Gender bias dataset with paired prompts
- **Regard**: Measures polarity of generated content across demographic segments
- Tools: Hugging Face's Evaluate library, OpenAI's Evals library

#### Evaluating Code Generators
- Generate code from docstrings, run tests, profile performance, scan for security vulnerabilities, compare against other LLMs
- Requires human-in-the-loop for edge case test coverage

#### Evaluating Model Parameters
- **WeightWatcher**: Analyze model weight distributions without running the model; identifies over/undertrained layers via spectral analysis
- Useful for comparing foundation models before committing to finetuning

### Training Data

#### Key Datasets
| Dataset | Contents | Size | Notes |
|---|---|---|---|
| Wikitext | English Wikipedia | <1 GB | Clean but outdated (2016), English-only |
| Wiki-40B | Multilingual Wikipedia | 10 GB | 40 languages, good for multilingual prototyping |
| Europarl | EU Parliament proceedings | 1.5 GB | 21 languages, great toy dataset |
| Common Crawl (C4) | The internet | ~300 GB | Most common for pretraining; contains bias |
| OpenWebText | Reddit-curated internet | 55 GB | Selection bias from Reddit users |
| The Pile | Conglomerate of 22 datasets | 825 GB | Includes books, code, specialty data |
| RedPajama | Mimics LLaMA training data | 5 TB | GitHub, arXiv, Books, Wikipedia, StackExchange, Common Crawl |
| OSCAR | Curated multilingual | 9.4 TB | 166 languages, actively maintained |

- **Corpora** are like datasets but include metadata, frequency analysis, and collocates; examples include COHA and COCA; think of them as pre-curated vector databases
- Knowing what a model was trained on (and not trained on) is critical for understanding its capabilities

### Data Cleaning and Preparation
- High-quality data matters more than Big Data -- models like LIMA and Alpaca proved this
- Basic pipeline: define schema -> normalize distributions -> check for bias/anomalies -> tokenize/embed -> train

#### Instruct Schema
- Format: `###Instruction / ###Input / ###Response`
- Provides pragmatic guardrails and syntactic landmarks that help with long-term memory
- Variants: evol-instruct (WizardLM), self-instruct (Alpaca)

#### Speech Acts
- Categories: expressives, commissives, directives, declarations, verdictives, questions, representatives
- Ensure your training data covers the speech acts your model will encounter in production
- Form doesn't always match function (e.g., "You're fired" said to a friend is expressive, not declarative)
- Insufficient coverage leads to unpredictable behavior at edge cases

#### Data Annotation
- Focus on macro metadata (speech acts, language) rather than micro annotations (POS tagging)
- Tools: Prodigy, doccano, TagEditor (spaCy), Praat (phonetics), Galileo
- Goal is not to annotate everything -- just a large enough sample to ensure representativeness
- LLM training is two-step: (1) self-supervised pretraining for general representations, (2) finetuning/RLHF to teach when/how to use them

### Text Processors

#### Tokenization
- Tokenization strategy is vitally important -- it determines what the model sees
- **GOAT 7B vs. GPT-4 in math**: GOAT outperforms because Llama tokenizes each digit individually, while GPT groups digits by frequency, losing information
- **Word-based**: Split on whitespace/punctuation; requires huge dictionary; poor at code and entities
- **Character-based**: Tiny dictionary, no unknown tokens; major loss of semantic/syntactic information
- **Subword-based**: Best option (Goldilocks); smaller dictionary than word-based with better semantics; includes morphological information
- Main algorithms: **BPE** (used by GPT), **SentencePiece** (used by Llama), WordPiece, Unigram
- Key parameters when training: `vocab_size`, `min_frequency`, `special_tokens`
- Multilingual models outperform monolinguals because they learn deeper representations without easy tokenization shortcuts

#### Embeddings
- Provide meaning to tokenized vectors via positional and semantic encodings
- Embeddings are imperfect approximations but enable distance-based comparisons
- **RAG (Retrieval-Augmented Generation)**: Store pertinent data as embeddings, retrieve relevant portions at prompting time to improve results
- Extract embeddings from the final hidden state before decoding layers
- Use the same embedding model for storage and inference
- Many business problems can be solved with embeddings alone, without a full LLM (runs on CPU in milliseconds)

## Key Takeaways
- Selecting the right foundation model and understanding what it was trained on is the first and most consequential decision in your LLM project
- Evaluate models across multiple dimensions: capability benchmarks (GLUE, MMLU), text metrics (ROUGE, BLEU), bias evaluation (HONEST, Regard), and parameter analysis (WeightWatcher)
- Your tokenization strategy directly determines model performance -- training a custom tokenizer for your use case is one of the simplest high-impact optimizations
- Data quality trumps data quantity; instruct schemas and speech act coverage produce better results than raw data volume
- Embeddings and RAG can solve many problems without the overhead of hosting a full LLM
