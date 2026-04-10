"""
Lightweight tool registry — replaces LangChain's @tool decorator.
Each tool is a plain function with attached metadata (name, description, schema).
"""
import inspect
import json
from typing import Any, Callable, Dict, List, Optional, get_type_hints


class Tool:
    """Wrapper around a plain function with OpenAI-compatible metadata."""

    def __init__(self, func: Callable, name: str, description: str, schema: Dict):
        self.func = func
        self.name = name
        self.description = description
        self.parameters_schema = schema

    def invoke(self, args: Dict[str, Any]) -> str:
        """Call the function and return the result as a string."""
        return self.func(**args)

    def to_openai_tool(self) -> Dict:
        """Return the OpenAI function-calling tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }


# Python type → JSON Schema type
_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def tool(func: Callable) -> Tool:
    """
    Decorator that converts a function into a Tool with auto-generated
    OpenAI function-calling schema from the function signature + docstring.
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func)
    doc = inspect.getdoc(func) or ""

    # Parse the docstring for arg descriptions
    arg_descs = {}
    in_args = False
    for line in doc.split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if stripped.lower().startswith("returns"):
            in_args = False
            continue
        if in_args and ":" in stripped:
            arg_name, arg_desc = stripped.split(":", 1)
            arg_descs[arg_name.strip()] = arg_desc.strip()

    # Build JSON schema for parameters
    properties = {}
    required = []
    for param_name, param in sig.parameters.items():
        json_type = _TYPE_MAP.get(hints.get(param_name, str), "string")
        prop: Dict[str, Any] = {"type": json_type}
        if param_name in arg_descs:
            prop["description"] = arg_descs[param_name]
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        else:
            prop["default"] = param.default
        properties[param_name] = prop

    schema = {
        "type": "object",
        "properties": properties,
        "required": required,
    }

    # Use first line of docstring as description
    description = doc.split("\n")[0].strip() if doc else func.__name__

    return Tool(func=func, name=func.__name__, description=description, schema=schema)
