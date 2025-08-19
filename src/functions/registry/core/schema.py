from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class FunctionEntry:
    function_id: str = ''
    function_metadata: Dict[str, Any] = field(default_factory=dict)
    function_search_description: str = ''
    function_tags: List[str] = field(default_factory=list)
    function_type: str = ''
    function_man_page_doc: str = ''
    function_api_spec: Dict[str, Any] = field(default_factory=dict)
    func_custom_actions_dsl_map: Dict[str, Any] = field(default_factory=dict)
    default_func_usage_credentials: Dict[str, Any] = field(default_factory=dict)
    open_api_spec: Dict[str, Any] = field(default_factory=dict)
    api_parameters_to_cost_relation_data: Dict[str, Any] = field(default_factory=dict)
    is_system_action: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FunctionEntry":
        return cls(
            function_id=data.get("function_id", ""),
            function_metadata=data.get("function_metadata", {}),
            function_search_description=data.get("function_search_description", ""),
            function_tags=data.get("function_tags", []),
            function_type=data.get("function_type", ""),
            function_man_page_doc=data.get("function_man_page_doc", ""),
            function_api_spec=data.get("function_api_spec", {}),
            func_custom_actions_dsl_map=data.get("func_custom_actions_dsl_map", {}),
            default_func_usage_credentials=data.get("default_func_usage_credentials", {}),
            open_api_spec=data.get("open_api_spec", {}),
            api_parameters_to_cost_relation_data=data.get("api_parameters_to_cost_relation_data", {}),
            is_system_action=data.get("is_system_action", False)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "function_id": self.function_id,
            "function_metadata": self.function_metadata,
            "function_search_description": self.function_search_description,
            "function_tags": self.function_tags,
            "function_type": self.function_type,
            "function_man_page_doc": self.function_man_page_doc,
            "function_api_spec": self.function_api_spec,
            "func_custom_actions_dsl_map": self.func_custom_actions_dsl_map,
            "default_func_usage_credentials": self.default_func_usage_credentials,
            "open_api_spec": self.open_api_spec,
            "api_parameters_to_cost_relation_data": self.api_parameters_to_cost_relation_data,
            "is_system_action": self.is_system_action
        }
