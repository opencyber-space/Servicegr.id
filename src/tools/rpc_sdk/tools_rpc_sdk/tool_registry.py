from typing import Callable, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Tool:
    name: str
    func: Callable[[bytes], bytes]
    input_spec: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found.")
        return self._tools[name]

    def list_tools(self) -> Dict[str, Tool]:
        return self._tools

    def has_tool(self, name: str) -> bool:
        return name in self._tools

# Singleton instance
global_tool_registry = ToolRegistry()
