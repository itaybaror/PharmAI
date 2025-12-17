# PharmAI 💊

A demo pharmacy assistant built with OpenAI’s Responses API, structured tool-calling, and true server-side streaming.

## Table of Contents

- [About the Project](#about-the-project)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Design Decisions](#design-decisions)
- [Final Notes](#final-notes)

## About the Project

PharmAI is a demo AI-powered pharmacy assistant designed to demonstrate how to build a clean, reliable, and debuggable LLM agent using modern OpenAI primitives.

The project prioritizes correctness, transparency, and explicit control over agent behavior, rather than abstraction-heavy frameworks.

Core concepts demonstrated:
- OpenAI Responses API
- Structured tool-calling
- True server-side streaming
- Strict separation between model reasoning and authoritative data

The assistant allows users to:
- Query medication label information (ingredients, warnings, dosage, prescription requirement, stock)
- View a demo user’s prescriptions
- List medications available in the pharmacy database
- Ask follow-up questions with conversational context

Disclaimer:
This is a demo system only. It does not provide medical advice and cannot perform real-world actions.



## Getting Started

1. Prerequisites

      - Docker
      - An OpenAI API key

2. Environment Variables

      Create a `.env` file or export the variable:

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



## Final Notes

PharmAI is intentionally small, explicit, and opinionated.

The goal of this project is to show how agents actually work, without hiding behavior behind abstractions or frameworks.

If you are reviewing this project, start with `agent.py`. Everything flows from there.