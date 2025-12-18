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
         docker build --no-cache -t pharmai .
         ```

      - Run the container:

         ```sh
         docker run --name pharmai-container -p 8080:8080 --env-file .env pharmai
         ```

4. Access the Application
      - UI:  http://localhost:8080/ui


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

<details>
<summary><strong>Demo vs. Production Considerations</strong></summary>

This project is intentionally designed as a **demonstration system**, optimized for clarity, correctness, and reviewability rather than production readiness. Below are key areas where demo-specific choices were made, along with what would change in a real deployment.

### Data Storage

- **Demo choice:**  
  The medication and user data lives in a **synthetic, in-memory Python database** (`db.py`).

- **Why:**  
  This keeps the focus on agent design, tool-calling correctness, and streaming behavior. Using SQL or NoSQL would not meaningfully improve what this project is meant to demonstrate.

- **Production approach:**  
  Data would live in a real datastore (e.g., PostgreSQL, MySQL, DynamoDB), accessed via a proper data access layer or service.

---

### Language Support

- **Demo choice:**  
  The database content exists primarily in English. The model responds in the user’s language, but factual fields come directly from the database.

- **Trade-offs:**  
  This avoids translating medical data at runtime (which can introduce inaccuracies), but may result in mixed-language responses.

- **Production approaches:**  
  - Store authoritative multilingual data per language (more accurate, more complex), or  
  - Translate tool outputs in the prompt (simpler, but riskier for regulated domains).

---

### Authentication & User Identity

- **Demo choice:**  
  Users are selected from a dropdown of **synthetic demo users**.

- **Production approach:**  
  User identity would come from authentication (JWTs, sessions, OAuth), and tools would derive user context securely from the request.

---

### Error Handling & Observability

- **Demo choice:**  
  Deterministic error handling via structured `error_code`s returned by tools.

- **Production approach:**  
  Add structured logging, metrics, tracing, and alerting while keeping the same tool contracts.

---

### Deployment & Scaling

- **Demo choice:**  
  Single-container Docker deployment.

- **Production approach:**  
  Horizontal scaling, request timeouts, rate limiting, and background workers for long-running tasks.

---

### Summary

These demo choices are intentional. They remove distractions and allow the core ideas to be evaluated clearly:

- strict tool-based data access  
- explicit agent control flow  
- true server-side streaming  
- predictable, auditable outputs  

The same architectural patterns transfer directly to production once the surrounding infrastructure is swapped in.

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
  This document. It explains what PharmAI does, how to run it, and the key architectural and design decisions.

- **Flow Evaluation (`flow-evaluation.md`)**  
  The evaluation deliverables are combined into a single file:
  - Multi-step user workflows
  - Screenshots as evidence
  - Evaluation notes for each flow  

  This keeps the evaluation concise and easy to follow while still covering all required components. The documented flows are representative examples; the agent supports additional workflows beyond those shown.

  → [`flow-evaluation.md`](./docs/flow-evaluation.md)

- **Tool Reference (`tools.md`)**  
  A clear reference for all tools exposed to the agent, including their purpose, inputs, outputs, and constraints. This file exists to make the agent–tool boundary explicit and demonstrate strict separation between the model and authoritative data.

  → [`tools.md`](./docs/tools.md)

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