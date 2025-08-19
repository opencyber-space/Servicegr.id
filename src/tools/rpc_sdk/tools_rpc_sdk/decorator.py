from typing import Callable, Dict, Any, Tuple
import traceback

from .tool_registry import Tool, global_tool_registry


def register_tool(name: str, input_spec: Dict[str, Any] = None, metadata: Dict[str, Any] = None, description: str = ""):
    def decorator(func: Callable[[bytes], bytes]):
        tool = Tool(
            name=name,
            func=func,
            input_spec=input_spec or {},
            metadata=metadata or {},
            description=description
        )
        global_tool_registry.register(tool)
        return func
    return decorator


class ToolExecutor:
    def __init__(self):
        self.registry = global_tool_registry

    def execute(self, tool_name: str, input_bytes: bytes) -> Tuple[bool, bytes, str, dict]:

        try:
            tool: Tool = self.registry.get(tool_name)
            output = tool.func(input_bytes)
            if not isinstance(output, bytes):
                raise TypeError(
                    f"Tool '{tool_name}' must return bytes, got {type(output).__name__}")
            return True, output, "", tool.metadata
        except Exception as e:
            error_trace = traceback.format_exc()
            return False, b"", f"{str(e)}\n{error_trace}", {}
