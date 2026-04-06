# Chapter 1 - Generative AI: Why Large Language Models Have Captured Attention

## Overview
This chapter introduces LLMs and their potential to transform communication across industries. It covers when to use (and avoid) LLMs, walks through the build-versus-buy decision for deploying them, and debunks common myths about barriers to entry.

## Key Concepts

### What LLMs Can and Cannot Do
- LLMs excel at language and communication tasks: content generation, Q&A, chatbots, AI assistants, text-to-X problems, talk-to-your-data applications
- They have passed medical exams, bar exams, coding interviews, and the SAT
- Avoid using LLMs for: latency-sensitive workloads, simple problems (overkill), math/forecasting problems, critical evaluations, and high-risk projects
- LLMs introduce randomness via temperature; turning it down may reduce creativity but increases consistency
- LLMs cannot be held accountable -- they are tools, and the responsibility lies with the user

### The Build vs. Buy Decision
- **Buying (API access)** is best for: rapid prototyping, failing fast, accessing optimized models, leveraging vendor expertise and safety systems
- **Building (self-hosted)** is best for: control, competitive edge, integration flexibility, cost management, security/privacy
- **Control**: The Latitude/AI Dungeon story illustrates the risk of depending on a vendor (OpenAI) who can change terms, enforce content policies, or read your data
- **Competitive edge**: Finetuning an open source model on your domain data can outperform general-purpose models at your specific task (e.g., SlovenBERTcina)
- **Integration**: APIs add latency and require internet; edge deployment needs self-hosted models
- **Costs**: API seems cheap ($20/month) but self-hosting inference can cost ~$250K/year for large models; however, finetuning can cost as little as $100 for a 20B parameter model
- **Security/Privacy**: Sending sensitive data to third-party APIs exposes it to vendors and their subcontractors; Samsung employees leaked code via ChatGPT
- The best strategy is often hybrid: buy for research/prototyping, build for production

### Debunking Myths
- You do not need to train from scratch -- open source foundation models are available to finetune
- There is no technical moat; open source frameworks and models provide building blocks for anyone
- Building a demo is easy; building a working product is very hard (Watson Health is an example of failing to productionize)
- ChatGPT's success was not about a better model -- it was the first to truly productionize an LLM as a consumer product
- The Borders bookstore cautionary tale: failing to build in-house technical expertise leaves you unprepared when the landscape shifts

## Key Takeaways
- LLMs are transformative because they operate within the framework of human language, giving them near-limitless applications
- The more central an LLM is to your business, the more important it is to own and control the technology
- Open source models and frameworks eliminate the myth that only large corporations can work with LLMs
- Turning an LLM from a demo into a reliable product requires understanding the full production lifecycle, not just the model itself
- Investing in LLM expertise now prepares your organization for future technologies built on top of them
