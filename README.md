# PharmAI 💊

A demo pharmacy assistant built with OpenAI’s Responses API, structured tool-calling, and true server-side streaming.

## Table of Contents

- [About the Project](#about-the-project)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Design Decisions](#design-decisions)
- [Deliverables](#deliverables)
- [Resources & References](#resources--references)

## About the Project

PharmAI is a **demo AI-powered pharmacy assistant** that answers factual questions about medications and prescriptions using a controlled, tool-driven approach.

To use the app, select a **demo user** from the dropdown and interact with the assistant as that user.

Users can:
- Look up medication label information (ingredients, warnings, dosage text, prescription requirement, stock)
- View a selected demo user’s prescriptions
- List medications available in the pharmacy database
- Ask follow-up questions in a conversational flow

The assistant is intentionally **limited**: it does not provide medical advice, make recommendations, refill prescriptions, or perform real-world actions. All medication data comes from a fixed demo database, and the assistant only responds using information returned by explicit tools. Additionally the assistant knows when a request is out-of-scope and directs the user to speak with a medical professional.

This project serves as a reference example of how to build a **predictable, auditable, and safe** conversational assistant for pharmacy-style use cases.

> ⚠️ **Disclaimer**  
> This is a demo system only. It does not provide medical advice and cannot perform real-world pharmacy actions.
> All medication data and user profiles in this project are **synthetic** and created solely for demonstration purposes.


## Getting Started

1. Prerequisites

      - Docker
      - An OpenAI API key

2. Environment Variables

      Create a `.env` file and add this variable to it:

      ```sh
      OPENAI_API_KEY=your_api_key_here
      ```

3. Run with Docker

      - Build the image:

         ```sh
         docker build -t pharmai .
         ```

      - Run the container:

         ```sh
         docker run --name pharmai-container \
            -p 8080:8080 \
            -v "$(pwd)":/app \
            --env-file .env \
            pharmai
         ```

4. Access the Application

      - API: http://localhost:8080
      - UI:  http://localhost:8080/ui
      - FastAPI Docs: http://localhost:8080/docs



## Architecture

The project intentionally avoids heavy abstractions and frameworks in favor of explicit, readable code that shows exactly how the agent works end-to-end.

Project structure:

```
app/
├── agent.py        # Core agent logic (LLM + tools + streaming loop)
├── tools.py        # Tool implementations + JSON schemas
├── prompt.py       # System prompt construction
├── ui.py           # Gradio UI (streaming)
├── main.py         # FastAPI entrypoint
├── db.py           # Demo in-memory database
```

### High-Level Flow

1. UI (Gradio)
   - Collects the user message
   - Maintains chat history
   - Streams assistant output in real time

2. Agent (agent.py)
   - Converts UI chat history into the Responses API message format
   - Streams model output token-by-token
   - Detects tool calls
   - Executes tools locally
   - Appends tool outputs back into the conversation
   - Repeats until a final response is produced

3. Tools (tools.py)
   - Act as the only source of truth for medication and user data
   - Return deterministic, structured JSON responses

4. Prompt (prompt.py)
   - Enforces strict behavioral rules
   - Prevents hallucinated medical information
   - Defines explicit error-handling behavior
   - Forces tool usage when facts are required



## Design Decisions

<details>
<summary><strong>Agent</strong></summary>

- Implemented as a small, explicit loop
- No hidden planners or retries
- No framework abstractions (e.g., LangChain)
- Tool calls are executed deterministically
- Streaming is handled directly via the Responses API

</details>

<details>
<summary><strong>UI</strong></summary>

- Built with Gradio and mounted inside FastAPI
- Maintains all conversational state
- Uses Python generators for real-time streaming
- Agent remains stateless

</details>

<details>
<summary><strong>Tools</strong></summary>

- Tools are the only source of factual data
- The model is forbidden (by prompt) from inventing facts
- Tool outputs are treated as authoritative
- Errors are handled explicitly via error codes
- Number of tools is kept minimal and highly focused as descried as best practice in OpenAI documentation

</details>

<details>
<summary><strong>Database</strong></summary>

- In-memory demo database
- Deterministic and inspectable
- Designed for testing and demonstration only
- No persistence or real-world integration

</details>

<details>
<summary><strong>Streaming</strong></summary>

- Uses true server-side streaming via `client.responses.stream`
- Tokens are yielded as soon as they are generated
- Tool calls interrupt streaming naturally and resume afterward
- No fake chunking or post-processing

</details>

<details>
<summary><strong>Statelessness</strong></summary>

- The agent backend is completely stateless
- No chat history, user context, or session data is stored on the server
- All conversational context is sent from the UI with each request
- Every request is self-contained and independently reproducible
- **Why this matters:**
   - Predictable behavior with no hidden memory
   - Easier debugging and replay of conversations
   - Horizontal scalability without coordination
   - Reduced risk of state leakage or corruption

</details>
<br>

> Note:
> During early development, I initially misunderstood what is commonly meant by an “agent” and workflows and implemented **deterministic AI workflows** instead of a model-driven agent loop.
>
> These workflows worked well but differed from agent-loop design.
>
> The deterministic implementation is preserved in the **`deterministic` branch**.

## Deliverables

This repository fulfills all required deliverables for the assignment:

- **README.md**  
  This document. It explains the project, architecture, design decisions, and how to run the system using Docker.

- **Flow Evaluation (`flow-evaluation.md`)**  
  The remaining deliverables — **multi-step flows**, **evidence**, and **evaluation plan** — are intentionally combined into a single document:
  - Each section defines a concrete multi-step user workflow
  - Screenshots provide evidence of correct behavior
  - Evaluation criteria explain how each flow is assessed

Combining these into one file keeps the evaluation cohesive and easy to follow, while still clearly addressing each required component. The agent itself supports many additional workflows beyond those documented; the selected flows represent clear, high-signal examples aligned with the assignment requirements.

## Resources & References

This project was designed and planned using the following resources and documentation:

**OpenAI Responses API**https://platform.openai.com/docs/guides/responsesUsed for unified text generation, tool-calling, and streaming.

**OpenAI Function / Tool Calling**https://platform.openai.com/docs/guides/function-callingReference for structured tool schemas and deterministic tool execution.

**GPT-5 Prompting Guide**
https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide
Used to design strict, policy-driven system prompts.

**Gradio ChatInterface**
https://www.gradio.app/docs/gradio/chatinterface
Used for building the streaming chat UI.

**Building Effective Agents - Anthropic**
https://www.anthropic.com/engineering/building-effective-agents
Provided insights into agent loop design and safety considerations.

These references guided the architectural decisions, agent loop design, prompt structure, and streaming behavior used in PharmAI.