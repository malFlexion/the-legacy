# Assignment 9 - Structured Output

## Key Learning Objectives
- Get an LLM to return structured HTML output
- Use constrained generation libraries (Outlines, Guidance)
- Understand how structured output improves reliability

## Core Concepts

### The Problem with Unstructured Output
- LLMs generate free-form text by default
- Hard to parse programmatically (regex is fragile)
- No guarantee the output follows a specific format
- Structured output makes LLMs usable in software pipelines

### Constrained Generation Libraries

#### Outlines (dottxt)
- Constrains token sampling to match a regex, JSON schema, or grammar
- Works by masking invalid tokens during generation
- Guarantees output matches the specified format
- Supports: regex, JSON schema, CFG (context-free grammar)

#### Guidance (Microsoft)
- Template-based approach to structured generation
- Mix fixed text with LLM-generated portions
- `select` and `gen` primitives for constrained output
- Supports token healing and caching

### HTML Structured Output
- Define the expected HTML structure
- Use grammar or regex constraints to ensure valid HTML
- Model fills in content while respecting structure
- Result is always parseable HTML

### Approaches
- **Regex constraints**: Force output to match a pattern
- **Grammar constraints**: Use a formal grammar (e.g., HTML grammar)
- **JSON schema**: Define expected structure as JSON, convert to HTML
- **Template filling**: Fix the HTML skeleton, let the model fill content

## Key Takeaways
- Structured output transforms LLMs from chat tools to software components
- Constrained decoding guarantees format compliance at the token level
- Larger models tend to follow structure better even without constraints
- Outlines and Guidance are the two leading libraries in this space
