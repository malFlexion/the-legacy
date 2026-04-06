# Assignment 0 - Getting Started

## Key Learning Objectives
- Git workflow basics: clone, branch, commit, push, create PR
- Setting up tooling: git, uv, pre-commit hooks
- Basic text preprocessing with regex
- Building a simple vocabulary-based tokenizer from scratch

## Core Concepts

### Git & Collaboration
- Clone a shared class repo, create feature branches, submit PRs
- Use `.gitignore` to keep large datasets out of version control
- Install pre-commit hooks to run tests/linters automatically before commits

### Basic Tokenizer
- **Preprocessing**: Split text on punctuation and whitespace using regex
- **Vocabulary building**: Extract unique tokens from corpus, add special tokens (`<|endoftext|>`, `<|unk|>`)
- **Encoding**: Map text -> token IDs using a string-to-int dictionary
- **Decoding**: Map token IDs -> text using an int-to-string dictionary
- **Unknown token handling**: Replace out-of-vocabulary words with `<|unk|>`

### Testing
- Write pytest tests to verify tokenizer encode/decode behavior
- Achieve 80% test coverage (enforced by CI pipeline)
- Format code with `ruff`

## Key Takeaways
- A simple tokenizer is just a lookup table: word -> integer ID
- Special tokens handle edge cases (unknown words, end of text)
- Regex splitting is a crude but effective first approach to tokenization
- Testing and CI discipline starts from day one
