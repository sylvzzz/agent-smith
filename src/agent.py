import os
import json
import re
import subprocess
from collections.abc import Callable

from openai import OpenAI
from dotenv import load_dotenv

from .log import Logger

load_dotenv()


def create_code(code: str, path: str):
    with open(path, "w") as file:
        file.write(code)

    Logger.success(f"Code saved at {path}")
    Logger.code(code, path.split(".")[-1])

    return f"Code saved at {path}"


def read_file(path: str):
    if ".env" in path:
        return "Access denied."

    with open(path, "r") as file:
        return file.read()


def check_files(directory: str = "."):
    return subprocess.check_output(
        ["ls", "-la", directory],
        text=True
    )


tools: dict[str, Callable] = {
    "create_code": create_code,
    "read_file": read_file,
    "check_files": check_files,
}


schemas = [
    {
        "type": "function",
        "function": {
            "name": "create_code",
            "description": "Create and save a code file.",
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
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string"}
                },
                "required": ["directory"]
            }
        }
    }
]


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

    while True:

        response = client.chat.completions.create(
            model=os.environ["LLM_MODEL"],
            messages=messages,
            tools=schemas,
            tool_choice="auto"
        )

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
                args = json.loads(call.function.arguments)
                result = execute(call.function.name, **args)

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

    print("agent-smith terminou o trabalho.")

    return [
        msg.model_dump(exclude_none=True)
        if hasattr(msg, "model_dump")
        else msg
        for msg in messages[1:]
    ]