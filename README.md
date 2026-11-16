# agent-smith — agent-smith

agent-smith is a self-hosted, conversational AI agent that talks to you in plain
text (no markdown) and takes real actions on your local machine by calling
Python tools. It is powered by any OpenAI-compatible LLM API; we are currently
using Groq + Qwen via the OpenAI Python SDK.

## What we have done so far

1. Core agent loop (`agent.py`)
   - A chat loop that keeps a running history of the conversation and feeds
     it back to the model as context.
   - The model is asked to answer in plain text or invoke one of the
     registered tools.
   - If the model returns a tool call, we execute it locally, print the
     result, send the tool result back to the model, and repeat until the
     model gives a final text answer.
   - The loop is interactive: it prints "agent-smith: How can i help you today?"
     and reads user input until Ctrl+C.

2. Tool set the agent can use
   - schedule(event) – simulate scheduling an event (returns a confirmation).
   - calculate(x, y) – add two integers.
   - create_code(code, path) – write a Python file to disk.
   - read_file(path) – read a text file and return it line by line.
   - check_files(directory) – list files and directories using `ls -la`.

3. LLM configuration (`.env`)
   - LLM_BASE_URL – OpenAI-compatible API endpoint (Groq).
   - LLM_MODEL – model name (Qwen3.8-27B).
   - LLM_API_KEY – API key used by the OpenAI SDK.

4. Example of the agent working (`test.py`)
   - `test.py` contains a small program with `add` and `fatorial` functions.
   - The agent was asked to generate code and saved this file, demonstrating
     that `create_code` works and that the agent can write runnable Python.

## How to run

1. Install dependencies:
   pip install openai python-dotenv

2. Make sure `.env` is filled in (API key, model, base URL).

3. Start the agent:
   python agent.py

4. Talk to agent-smith in the terminal.

## Current limitations / next steps

- No persistence between sessions (history is in memory only).
- No authentication or multi-user support.
- Tools are hardcoded; a plugin/registration system would be nice.
- No streaming responses.
- No unit tests; only a manual `test.py` file.
- Secrets are in `.env` in the repo; a real deployment should keep them out.
- The agent answers in English but was written with Portuguese friendly
  defaults ("agent-smith terminou o trabalho.", "Thank you for using agent-smith!").

## License

TBD