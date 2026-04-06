# Assignment 2 - Data Loader

## Key Learning Objectives
- Build a PyTorch DataLoader for text data
- Understand how data flows from raw text into model training
- Learn PyTorch Dataset and DataLoader abstractions

## Core Concepts

### PyTorch Dataset
- Subclass `torch.utils.data.Dataset`
- Implement `__len__()` and `__getitem__()` methods
- `__getitem__` should return tokenized, tensorized samples
- Handle text preprocessing and tokenization inside the dataset

### PyTorch DataLoader
- Wraps a Dataset to provide batching, shuffling, and parallel loading
- Key parameters:
  - `batch_size`: Number of samples per batch
  - `shuffle`: Randomize order each epoch (True for training)
  - `num_workers`: Parallel data loading processes
  - `collate_fn`: Custom function to combine samples into a batch
  - `drop_last`: Drop incomplete final batch

### Text-Specific Considerations
- **Padding/truncation**: Sequences must be same length within a batch
- **Attention masks**: Track which tokens are real vs. padding
- **Sliding window**: For long documents, create overlapping chunks
- **Train/val/test splits**: Ensure no data leakage between splits

### Data Pipeline Flow
```
Raw Text -> Tokenizer -> Token IDs -> Dataset -> DataLoader -> Model
```

## Key Takeaways
- DataLoaders abstract away batching, shuffling, and parallel loading
- The Dataset class is where preprocessing logic lives
- Proper padding and attention masking are critical for text data
- Data loading is often the bottleneck - `num_workers` helps
