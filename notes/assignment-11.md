# Assignment 11 - Frontend

## Key Learning Objectives
- Build a user-facing frontend for your LLM application
- Use Gradio or Streamlit for rapid prototyping
- Create a complete end-to-end interactive experience

## Core Concepts

### Frontend Options

#### Gradio
- `gr.ChatInterface`: Purpose-built chat UI component
- Handles streaming, message history, and user input automatically
- Easy to add custom parameters (sliders for temperature, etc.)
- Can be shared via public URL with `share=True`
- Integrates directly with HuggingFace Spaces for deployment

#### Streamlit
- `st.chat_message` and `st.chat_input` for conversational UIs
- Session state for maintaining conversation history
- More flexible layout options than Gradio
- Better for complex dashboards alongside chat

### Building a Chat Frontend
1. **Connect to your model**: Import inference code from Assignment 7
2. **Handle conversation history**: Store messages in session/state
3. **Stream responses**: Display tokens as they arrive
4. **Add controls**: Temperature, max tokens, system prompt, etc.

### Design Considerations
- **Streaming**: Essential for LLM UIs - users need feedback during generation
- **Error handling**: Graceful failures when model is unavailable
- **Loading states**: Show spinner/indicator during generation
- **Context window**: Manage conversation length to stay within token limits

### Testing Frontend Code
- Test the backend logic separately from the UI
- Mock LLM responses for fast, deterministic tests
- Test edge cases: empty input, very long input, special characters
- Gradio has built-in testing utilities

## Key Takeaways
- Gradio is the fastest path to a working chat UI (often < 20 lines)
- Streamlit offers more customization for complex applications
- The frontend ties together all previous work into a usable product
- Streaming support is non-negotiable for LLM user interfaces
