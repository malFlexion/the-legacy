# Assignment 8 - Vector Database & RAG

## Key Learning Objectives
- Create a vector database and load it with embeddings
- Query the database for semantic search
- (Extra credit) Build a full RAG system to improve model answers

## Core Concepts

### Vector Databases
- Store high-dimensional vectors (embeddings) alongside metadata
- Enable similarity search: find the most relevant documents for a query
- Popular options: Pinecone, Chroma, Weaviate, FAISS, Qdrant, Milvus

### Embeddings
- Convert text into dense numerical vectors that capture meaning
- Similar texts have similar vectors (close in vector space)
- Use embedding models: `sentence-transformers`, OpenAI embeddings, etc.
- Typical dimensions: 384, 768, 1024, 1536

### Building a Vector DB Pipeline
1. **Chunk**: Split documents into manageable pieces
2. **Embed**: Convert each chunk to a vector using an embedding model
3. **Store**: Insert vectors + metadata into the vector database
4. **Query**: Embed the query, find nearest neighbors, return results

### Retrieval-Augmented Generation (RAG) - Extra Credit
- Combine retrieval (vector DB) with generation (LLM)
- Pipeline: Query -> Retrieve relevant docs -> Inject into prompt -> Generate answer
- Lets the model use external knowledge without retraining
- Can fix wrong answers from Assignment 6 by providing correct context

### RAG Architecture
```
User Query -> Embed Query -> Vector DB Search -> Top-K Documents
    -> Construct Prompt (query + retrieved docs) -> LLM -> Answer
```

### Key Design Decisions
- **Chunk size**: Too small = no context, too large = noise
- **Top-K**: How many documents to retrieve (usually 3-5)
- **Overlap**: Overlapping chunks prevent cutting context mid-sentence
- **Distance metric**: Cosine similarity is most common for text

## Key Takeaways
- Vector databases enable semantic search (meaning-based, not keyword-based)
- Embedding quality directly affects retrieval quality
- RAG is the most practical way to give LLMs access to external knowledge
- Chunking strategy is critical and task-dependent
