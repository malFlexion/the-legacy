# Chapter 7 - Prompt Engineering: Becoming an LLM Whisperer

## Overview
This chapter covers prompt engineering from basic techniques (few-shot, one-shot, zero-shot) through the anatomy of a well-structured prompt, hyperparameter tuning, and advanced techniques like tool use and ReAct. It also surveys key tooling: LangChain, Guidance, and DSPy.

## Key Concepts

### Prompting Fundamentals
- **Prompt**: The input to a language model, crafted with intention to guide a desired output
- **Prompt engineering**: The process of designing, templating, and refining prompts, then implementing them in code
- Prompt engineering is about getting the model to solve every user's problem every time, not just once
- The goal is to activate the right parameters in the model to surface correct information from within its weights

### Shot-Based Prompting

#### Few-Shot Prompting
- Provide multiple examples of the desired input/output format
- Extremely effective; the model infers the task from the pattern of examples
- Downsides: examples consume tokens (expensive, may exceed context limits), follows law of diminishing returns per additional example
- Can specify output format (JSON, XML) by showing examples

#### One-Shot Prompting
- Single example to demonstrate the task
- The first example always does the heaviest lifting
- Risk of biasing the model (e.g., only showing a positive sentiment example biases toward positive)
- Performance improves with model scale

#### Zero-Shot Prompting
- No examples; relies on instruction alone
- Basic template: `"Q: [User's Prompt] A:"`
- **Chain of Thought (CoT)**: "Think step by step" dramatically improves reasoning (Wei et al., 2022)
- **Thread of Thought** (Zhou et al.): "Walk me through this context in manageable parts step by step, summarizing and analyzing as we go" -- tested 30 variations to find optimal phrasing for GPT-4
- Surprising findings that work: offering imaginary tips, threatening the model, saying "take a deep breath," using profanity/jargon
- These strategies work because they match patterns in the training data where humans produced high-quality output

### Anatomy of a Prompt
Four elements of a well-engineered prompt:
1. **Input**: What the user writes; can be anything, often messy with typos
2. **Instruction**: The template wrapping the input with task-specific guidance (e.g., "Answer as if the user were five years old")
3. **Context**: Pragmatic information the model needs -- RAG search results, chat history, database lookups, current time, user profile, static few-shot examples
4. **System prompt**: Consistent instruction given on every request to enforce behavior (e.g., "You are a wise old owl"). Use two system prompts (front and back) to guard against "ignore previous instructions" attacks. Never put sensitive info in the system prompt

### Prompting Hyperparameters
- **Temperature**: Controls randomness in token selection. 0 = deterministic (argmax), higher = more creative. Applied during softmax. Negative = opposite response
- **Beam search (num_beams)**: Explores the probability graph of generated text; more beams = better quality but higher latency
- **Top K**: Filters to the K most probable tokens, eliminating incoherent tail options
- **Top P (nucleus sampling)**: Filters by cumulative probability threshold (e.g., P=0.5 only considers tokens whose cumulative probability reaches 50%)
- **Frequency penalty**: Penalizes recently repeated words to increase vocabulary diversity
- **Presence penalty**: Penalizes any repeated token equally regardless of count, encouraging new topics

### Knowing Your Training Data
- Understanding what words/phrases exist in training data is critical for effective prompting
- Example: A Stable Diffusion model trained on LAION had no captions containing "Asian woman" but did have "Asian beauty" -- using the right phrasing made all the difference
- Finetuning + prompt engineering together is powerful: set seeds with specific phrases during finetuning, then use those phrases in prompts

### Tooling for Structured Outputs

#### LangChain
- Most popular library for building LLM applications
- **LangChain Expression Language (LCEL)**: Chain components together with `|` operator (prompt | model | output_parser)
- Ecosystem includes LangServe (hosting as API) and LangSmith (tracing/logging)
- Chains can be asynchronous and form DAGs, not just linear pipelines
- Many pre-built chains: RetrievalQA, SQL generation, API interaction, synthetic data generation

#### Guidance (Microsoft)
- Enforces **programmatic responses** -- solves the "prompt and pray" problem
- Core features: `gen()` with actual token limits, custom stopping tokens, `select()` for constrained choices, regex-based generation
- **Grammars**: Composable, reusable language rules using the `@guidance` decorator
- Constrains the response space so even small models produce correctly formatted output
- Documentation is sparse but the community is active

#### DSPy (Stanford)
- Treats prompting as a programming problem rather than a string-crafting exercise
- Workflow: Define a signature (task description + I/O fields) -> Create a predictor (generation style) -> Define a module -> Compile
- Compilation optimizes the prompts based on examples, similar to ML training (training set, loss function, optimizer)
- Useful when you want deterministic, programmatic behavior from LLMs

#### Other Tools
- MiniChain, AutoChain (lightweight LangChain alternatives), Promptify, Haystack, Langflow, Llama Index, Outlines (similar to Guidance)
- Many projects started during ChatGPT hype but went dormant; be careful choosing tooling in this space

### Advanced Prompt Engineering

#### Giving LLMs Tools (Toolformers)
- Train/prompt models to emit API calls using tags like `<API></API>` -- essentially teaching string interpolation
- Schick et al. finetuned GPT-J with 5 tools (QA database, calculator, Wikipedia, translator, calendar) and outperformed GPT-3
- With Guidance or LangChain, you can add tools via prompt engineering without finetuning
- Guidance stops generation when it recognizes a tool call, runs the tool, and resumes generation
- Challenges: must instruct the model how/when to use tools, handle malformed inputs, LLMs may hallucinate nonexistent tools or use the wrong tool
- Token budget shrinks as tool descriptions grow

#### OpenAI Plugins (Historical Note)
- Allowed third-party tool integration into ChatGPT via OpenAPI config + ai-plugin.json
- Never left beta; Sam Altman noted users wanted "ChatGPT in their apps" not "apps inside ChatGPT"
- A marketplace/hub for LLM tools is expected to emerge in the future

#### ReAct (Reasoning and Acting)
- Few-shot framework emulating human reasoning: Question -> Thought -> Action -> Observation -> repeat
- Forces the model to think before acting, then take actions (search, calculate) and reason about results
- Implementation with LangChain: `initialize_agent(tools, llm, agent="zero-shot-react-description")`
- Combines tool use with multi-step reasoning for complex queries

## Key Takeaways
- The four parts of a prompt (input, instruction, context, system) provide a framework for consistent prompt engineering
- Few-shot prompting is the most reliable technique; zero-shot CoT ("think step by step") is the most accessible
- Knowing your model's training data is essential for crafting effective prompts -- the right vocabulary matters enormously
- Guidance gives fine-grained control over LLM output format; LangChain excels at building chains/pipelines; DSPy treats prompting as software engineering
- Giving LLMs tools via Toolformers/ReAct patterns enables multi-step reasoning and real-world actions, but tool use is still unreliable and requires careful input validation
