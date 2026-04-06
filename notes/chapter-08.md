# Chapter 8 - Applications and Agents: Building an Interactive Experience

## Overview
This chapter covers building user-facing LLM applications, from streaming responses and chat history management to edge deployment with llama.cpp and building LLM agents. The focus is on practical features that turn a basic chatbot into a delightful product.

## Key Concepts

### Building an LLM Application
- **LLM application** = the frontend (web app, phone app, CLI, SDK, VS Code extension) that acts as the user interface and client for the LLM service
- Building a basic chatbot is easy (input field, send button, chat display); building a great one requires careful feature engineering

### Streaming on the Frontend
- Server-side streaming is meaningless without client-side streaming
- Stream tokens to the user as they are generated -- provides instant feedback and a sense that the model is "thinking"
- Users can see where the output is heading and stop/reprompt early
- Implementation: `fetch()` with `ReadableStream` in vanilla JavaScript, or Python `requests.post(stream=True)` with Streamlit/Gradio
- Add a blinking cursor (`"▌"`) to simulate typing

### Keeping a Chat History
- Without history, each message is independent -- the LLM has no context of prior conversation
- Store both user prompts and LLM responses; append history to new prompts as context
- **Problem**: History grows and eventually exceeds token limits or slows generation
- **Solutions**:
  1. Drop older messages in favor of newer ones (simple, works due to human recency bias)
  2. Use the LLM to summarize the chat history and use the summary as context (more robust, but at least doubles latency)
  3. Embed each chat message and perform semantic search to find relevant prior messages
- Streamlit's `st.session_state` provides easy session-based history management

### Chatbot Interaction Features
- **Fallback response**: Return a friendly error message when something goes wrong; maintain 1:1 ratio of user/LLM messages in history
- **Stop button**: Let users interrupt long-winded or incorrect responses mid-stream; saves money on output tokens
- **Retry button**: Resend last query and replace the response; optionally reduce temperature on each retry
- **Delete button**: Remove bad responses from chat history to prevent poisoning future context (soft delete keeps backend data)
- **Feedback form**: Collect user feedback for RLHF training, prompt improvement, and edge case identification. Clean/filter troll responses before using

### Frontend Frameworks
- **Streamlit**: Python framework with automatic UI generation, `st.chat_message`, `st.chat_input`, session state management
- **Gradio**: Open source Python library for quick UI components. `gr.ChatInterface` automatically adds Stop, Retry, and Undo buttons
- **Chainlit**: Purpose-built for LLM apps with themes, CSS customization, authentication, and cloud hosting out of the box
- Vanilla HTML/CSS/JavaScript also works for simple demos

### Token Counting
- Essential for user feedback (don't let users submit prompts that exceed limits) and prompt engineering (dynamically adjust RAG context based on remaining token budget)
- **tiktoken**: Fast BPE tokenizer for OpenAI models. `tiktoken.get_encoding("cl100k_base").encode(text)` returns token IDs
- tiktoken is OpenAI-specific; for other tokenizers (e.g., SentencePiece), build your own counter by encoding and counting
- Counts may be off by 5-10 tokens per 1,000 when using tiktoken with non-OpenAI models

### RAG on the Frontend
- **Backend RAG**: Consistent experience, developer control, better data security (data only accessible through LLM)
- **Frontend RAG**: More common; allows adding business context to any generic LLM without finetuning
- Implementation with LangChain: `RetrievalQA.from_chain_type(llm, retriever=vectorstore.as_retriever())`
- `RetrievalQAWithSourcesChain` adds source citations to responses
- Just define the LLM and vector store connections, and you are ready to make queries

### Edge Applications
- Challenges: models must be small enough to transfer and run without GPU, possibly without Python
- **llama.cpp**: Converts LLMs to GGUF format (quantized binary) for CPU inference. Supports dozens of LLM architectures and all major OS platforms
- Bindings for Python (`llama-cpp-python`), Go, Rust, Node.js, Java, React Native
- Download pre-converted models from Hugging Face (e.g., TheBloke's quantized GGUF models)
- `--include='*Q2_K*gguf'` selects specific quantization level (2-bit = smallest, most degraded quality)
- Performance: ~1 token/second for 7B model on CPU (slow but functional)
- Use `huggingface-cli download` for model acquisition

### LLM Agents
- **Definition**: Full LLM applications designed to accomplish multistep tasks, not just answer questions
- Agents do not differ from other LLMs fundamentally; the difference is the system surrounding them
- Three components of an agent:
  1. **LLM**: The reasoning engine
  2. **Memory**: Reintroduces context at each step
     - Memory buffer: passes all prior text (hits context limits fast, "lost in the middle" problem)
     - Memory summarization: LLM summarizes its own history (doubles latency, loses fine details)
     - Structured memory storage: Best results but hardest to set up; uses chunking and retrieval
  3. **External data retrieval tools**: The core of agent behavior; give the LLM ability to take actions

#### Building Agents with LangChain
- **Search tools**: `DuckDuckGoSearchRun()`, `YouTubeSearchTool()` -- LLM provides a prompt, tools handle search and return results
- **Python agent**: `create_python_agent()` with `PythonREPLTool()` -- generates and executes Python code, attempts to debug errors
- **CSV agent**: `create_csv_agent()` -- reads and analyzes CSV files
- **Custom agents**: Define tools, memory (`ConversationBufferWindowMemory`), system prompt with few-shot examples, and initialize with `initialize_agent()`
- Use instruction-tuned models (e.g., Mistral 7B Instruct in GGUF format)

#### Agent Reality Check
- Agents are "miraculous in that they work at all, but generally underwhelming in the tasks and levels they can perform"
- The Python agent hallucinated a nonexistent function; the CSV agent equated politeness with saying "thank you"
- Getting an LLM to perform well on one task is hard; chaining multiple tasks in an agent is extremely difficult
- LangChain adds significant computation overhead compared to raw llama.cpp
- LLMs are "flaky, just like humans" -- frustrating for software engineers used to deterministic systems

## Key Takeaways
- Streaming, chat history, and interaction features (stop, retry, delete) are what separate a basic chatbot from a polished LLM application
- RAG on the frontend lets you customize any generic LLM with business context without retraining; use LangChain's RetrievalQA for easy implementation
- llama.cpp is the go-to tool for running LLMs on edge devices without GPUs, supporting GGUF format across dozens of architectures and languages
- Agents combine LLMs, memory, and tools to solve multistep problems, but they are still unreliable and require advanced prompt engineering to produce reasonable results
- Token counting is a small but critical feature for both UX (preventing limit violations) and prompt engineering (dynamic context budgeting)
