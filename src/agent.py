import os
import json
import re
import subprocess
from collections.abc import Callable
from openai import (
    OpenAI,
    APIStatusError,
    APIConnectionError,
    RateLimitError,
    BadRequestError
)
import time
from dotenv import load_dotenv

from .log import Logger

load_dotenv()


def create_code(code: str, path: str):
    with open(path, "w", encoding="utf-8") as file:
        file.write(code)

    Logger.success(f"Code saved at {path}")

def edit_file(path: str, old: str, new: str):
    try:
        with open(path, "r", encoding="utf-8") as file:
            code = file.read()

        if old not in code:
            return "Text to replace not found."

        code = code.replace(old, new, 1)

        with open(path, "w", encoding="utf-8") as file:
            file.write(code)

        return f"File updated: {path}"

    except Exception:
        return "Something went wrong editing file, try again ..."


def read_file(path: str):
    if ".env" in path:
        return "Access denied."

    with open(path, "r") as file:
        Logger.warning(f"Reading {path} ...")
        return file.read()


def check_files(directory: str = "."):
    output = subprocess.check_output(
        ["ls", "-la", directory],
        text=True
    )

    Logger.warning(f"Checking {directory}/ ...")
    print(output)

    print()
    return output

def execute_code(terminal_command: str):

    Logger.warning(f"$ {terminal_command}")

    output = subprocess.run(
        ["sh", "-c", terminal_command],
        capture_output=True,
        text=True,
        timeout=30
    )

    terminal_output = f"$ {terminal_command}" + "\n" + output.stdout

    print(terminal_output)
    

tools: dict[str, Callable] = {
    "create_code": create_code,
    "read_file": read_file,
    "check_files": check_files,
    "edit_file": edit_file,
    "execute_code": execute_code
}


schemas = [
    {
        "type": "function",
        "function": {
            "name": "create_code",
            "description": "Create or overwrite a code file.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "path": {"type": "string"}
                },
                "required": ["code", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a project file.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_files",
            "description": "List files and directories.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string"}
                },
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Execute a terminal command to execute a program, python file or any executable",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "terminal_command": {"type": "string"}
                },
                "required": ["terminal_command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace specific text in an existing file.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"}
                },
                "required": ["path", "old", "new"]
            }
        }
    }
]

for tool in schemas:
    params = tool["function"]["parameters"]

    params["additionalProperties"] = False
    params["required"] = list(params["properties"].keys())


def execute(function: str, **kwargs):
    if function not in tools:
        return "Unknown tool."

    return tools[function](**kwargs)


def render_response(content: str):
    """
    Detect Markdown code blocks and render them
    using Logger.code().
    """

    pattern = r"```(\w*)\n(.*?)```"

    parts = re.split(pattern, content, flags=re.DOTALL)

    for i in range(0, len(parts), 3):
        text = parts[i]

        if text.strip():
            print()
            print(f"agent-smith: {text.strip()}")

        if i + 1 < len(parts):
            language = parts[i + 1] or "text"
            code = parts[i + 2]

            Logger.code(code, language)


def agent(prompt: str, history: list = None):

    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL")
    )

    system_prompt = """
You are agent-smith, an autonomous AI agent.

- Communicate naturally and clearly.
- Use Markdown code blocks when showing code.
- Always specify the programming language in code blocks.
- Use tools when appropriate.
- Never read .env files or sensitive information.
- Be concise.
- ALWAYS wrap code in Markdown fenced blocks.
- Start code blocks with ```language and end with ```.
- Never output raw source code outside code blocks.
- Before changing files, read them first
"""

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    if history:
        messages.extend(history)

    messages.append({
        "role": "user",
        "content": prompt
    })

    for _ in range(20): # nao ficar preso entre calls

        try:
            response = client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                messages=messages,
                tools=schemas,
                tool_choice="auto",
                max_tokens=800
            )

        except RateLimitError as e:
            wait_time = 60

            if e.response is not None:
                retry = e.response.headers.get("retry-after")
                if retry:
                    wait_time = float(retry)

            print(f"agent-smith: Rate limit. Waiting {wait_time:.0f}s...")
            time.sleep(wait_time)
            continue

        except BadRequestError as e:
            Logger.error(f"agent-smith: Invalid request: {e}")

            messages.append({
                "role": "user",
                "content": (
                    f"Your previous tool call failed: {e}. "
                    "Correct the arguments according to the tool schema "
                    "and continue the original task."
                )
            })

            continue

        except APIConnectionError:
            Logger.error("agent-smith: Connection error.")
            break

        except APIStatusError as e:
            Logger.error(f"agent-smith: API error {e.status_code}: {e}")
            break

        message = response.choices[0].message

        if message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    call.model_dump(exclude_none=True)
                    for call in message.tool_calls
                ]
            })

            for call in message.tool_calls:
                try:
                    args = json.loads(call.function.arguments)
                    result = execute(call.function.name, **args)
                except Exception as e:
                    result = f"Tool execution failed: {type(e).__name__}: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result)
                })
        else:
            if message.content:
                render_response(message.content)

            messages.append({
                "role": "assistant",
                "content": message.content
            })
            break

    Logger.warning("\nagent-smith completed his work.")

    messages = messages[-10:]

    return [
        msg.model_dump(exclude_none=True)
        if hasattr(msg, "model_dump")
        else msg
        for msg in messages[1:]
    ]