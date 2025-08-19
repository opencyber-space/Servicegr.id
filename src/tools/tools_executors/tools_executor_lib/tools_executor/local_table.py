from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import requests

import logging

from dsl_executor import new_dsl_workflow_executor, parse_dsl_output

logger = logging.getLogger("AgentAllowedToolActionStore")
logger.setLevel(logging.INFO)


@dataclass
class AgentAllowedTool:
    tool_id: str = ''
    tool_metadata: Dict[str, Any] = field(default_factory=dict)
    tool_search_description: str = ''
    tool_tags: List[str] = field(default_factory=list)
    tool_type: str = ''
    tool_man_page_doc: str = ''
    tool_api_spec: Dict[str, Any] = field(default_factory=dict)
    tool_custom_actions_dsl_map: Dict[str, Any] = field(default_factory=dict)
    default_tool_usage_credentials: Dict[str, Any] = field(
        default_factory=dict)
    derived_from: str = ''
    mapping_org_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentAllowedTool":
        return cls(
            tool_id=data.get("tool_id", ""),
            tool_metadata=data.get("tool_metadata", {}),
            tool_search_description=data.get("tool_search_description", ""),
            tool_tags=data.get("tool_tags", []),
            tool_type=data.get("tool_type", ""),
            tool_man_page_doc=data.get("tool_man_page_doc", ""),
            tool_api_spec=data.get("tool_api_spec", {}),
            tool_custom_actions_dsl_map=data.get(
                "tool_custom_actions_dsl_map", {}),
            default_tool_usage_credentials=data.get(
                "default_tool_usage_credentials", {}),
            derived_from=data.get("derived_from", ""),
            mapping_org_id=data.get("mapping_org_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "tool_metadata": self.tool_metadata,
            "tool_search_description": self.tool_search_description,
            "tool_tags": self.tool_tags,
            "tool_type": self.tool_type,
            "tool_man_page_doc": self.tool_man_page_doc,
            "tool_api_spec": self.tool_api_spec,
            "tool_custom_actions_dsl_map": self.tool_custom_actions_dsl_map,
            "default_tool_usage_credentials": self.default_tool_usage_credentials,
            "derived_from": self.derived_from,
            "mapping_org_id": self.mapping_org_id
        }


@dataclass
class AgentAllowedToolAction:
    action_type: str = ''
    mapped_tool_ids: List[str] = field(default_factory=list)
    action_tags: List[str] = field(default_factory=list)
    action_metadata: Dict[str, Any] = field(default_factory=dict)
    action_search_description: str = ''
    action_dsl: Dict[str, Any] = field(default_factory=dict)
    derived_from: str = ''
    mapping_org_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentAllowedToolAction":
        return cls(
            action_type=data.get("action_type", ""),
            mapped_tool_ids=data.get("mapped_tool_ids", []),
            action_tags=data.get("action_tags", []),
            action_metadata=data.get("action_metadata", {}),
            action_search_description=data.get(
                "action_search_description", ""),
            action_dsl=data.get("action_dsl", {}),
            derived_from=data.get("derived_from", ""),
            mapping_org_id=data.get("mapping_org_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "mapped_tool_ids": self.mapped_tool_ids,
            "action_tags": self.action_tags,
            "action_metadata": self.action_metadata,
            "action_search_description": self.action_search_description,
            "action_dsl": self.action_dsl,
            "derived_from": self.derived_from,
            "mapping_org_id": self.mapping_org_id
        }


class AgentAllowedToolStore:
    def __init__(self):
        self._store: Dict[str, AgentAllowedTool] = {}

    def create(self, tool: AgentAllowedTool) -> bool:
        if tool.tool_id in self._store:
            logger.warning(f"Tool '{tool.tool_id}' already exists.")
            return False
        self._store[tool.tool_id] = tool
        logger.info(f"Tool '{tool.tool_id}' added.")
        return True

    def get(self, tool_id: str) -> Optional[AgentAllowedTool]:
        return self._store.get(tool_id)

    def update(self, tool_id: str, updates: Dict) -> bool:
        tool = self._store.get(tool_id)
        if not tool:
            logger.warning(f"Tool '{tool_id}' not found for update.")
            return False
        for key, value in updates.items():
            if hasattr(tool, key):
                setattr(tool, key, value)
        logger.info(f"Tool '{tool_id}' updated.")
        return True

    def delete(self, tool_id: str) -> bool:
        if tool_id in self._store:
            del self._store[tool_id]
            logger.info(f"Tool '{tool_id}' deleted.")
            return True
        logger.warning(f"Tool '{tool_id}' not found for deletion.")
        return False

    def list_all(self) -> List[AgentAllowedTool]:
        return list(self._store.values())


class AgentAllowedToolActionStore:
    def __init__(self):
        self._store: Dict[str, AgentAllowedToolAction] = {}

    def _get_key(self, action: AgentAllowedToolAction) -> str:
        return f"{action.action_type}:{action.mapping_org_id}"

    def create(self, action: AgentAllowedToolAction) -> bool:
        key = self._get_key(action)
        if key in self._store:
            logger.warning(f"Action '{key}' already exists.")
            return False
        self._store[key] = action
        logger.info(f"Action '{key}' added.")
        return True

    def get(self, action_type: str, mapping_org_id: str) -> Optional[AgentAllowedToolAction]:
        return self._store.get(f"{action_type}:{mapping_org_id}")

    def update(self, action_type: str, mapping_org_id: str, updates: Dict) -> bool:
        key = f"{action_type}:{mapping_org_id}"
        action = self._store.get(key)
        if not action:
            logger.warning(f"Action '{key}' not found for update.")
            return False
        for k, v in updates.items():
            if hasattr(action, k):
                setattr(action, k, v)
        logger.info(f"Action '{key}' updated.")
        return True

    def delete(self, action_type: str, mapping_org_id: str) -> bool:
        key = f"{action_type}:{mapping_org_id}"
        if key in self._store:
            del self._store[key]
            logger.info(f"Action '{key}' deleted.")
            return True
        logger.warning(f"Action '{key}' not found for deletion.")
        return False

    def list_all(self) -> List[AgentAllowedToolAction]:
        return list(self._store.values())


class ToolsManagement:
    def __init__(self, tools_db_url: str):
        self.tools_db_url = tools_db_url.rstrip("/")
        self.tool_store = AgentAllowedToolStore()
        self.action_store = AgentAllowedToolActionStore()

    def add_tool_for_agent(self, tool_id: str, derived_from: str, mapping_org_id: str) -> bool:
        try:
            url = f"{self.tools_db_url}/tools/{tool_id}"
            response = requests.get(url)
            if response.status_code != 200:
                logger.error(f"Failed to fetch tool '{tool_id}' from DB: {response.status_code}")
                return False

            tool_data = response.json()
            tool = AgentAllowedTool.from_dict(tool_data)
            tool.derived_from = derived_from
            tool.mapping_org_id = mapping_org_id

            return self.tool_store.create(tool)
        except Exception as e:
            logger.error(f"Exception while adding tool '{tool_id}': {e}")
            return False

    def create_action(self,
                      action_type: str,
                      tool_ids: List[str],
                      action_tags: List[str],
                      action_metadata: Dict[str, any],
                      action_search_description: str,
                      action_dsl: Dict[str, any],
                      derived_from: str,
                      mapping_org_id: str) -> bool:
        try:
            missing = [tid for tid in tool_ids if self.tool_store.get(tid) is None]
            if missing:
                logger.warning(f"Cannot create action. Missing tools: {missing}")
                return False

            action = AgentAllowedToolAction(
                action_type=action_type,
                mapped_tool_ids=tool_ids,
                action_tags=action_tags,
                action_metadata=action_metadata,
                action_search_description=action_search_description,
                action_dsl=action_dsl,
                derived_from=derived_from,
                mapping_org_id=mapping_org_id
            )

            return self.action_store.create(action)
        except Exception as e:
            logger.error(f"Exception while creating action '{action_type}': {e}")
            return False

    def list_agent_tools(self) -> List[AgentAllowedTool]:
        return self.tool_store.list_all()

    def list_agent_actions(self) -> List[AgentAllowedToolAction]:
        return self.action_store.list_all()

    def get_tool(self, tool_id: str) -> Optional[AgentAllowedTool]:
        return self.tool_store.get(tool_id)

    def get_action(self, action_type: str, mapping_org_id: str) -> Optional[AgentAllowedToolAction]:
        return self.action_store.get(action_type, mapping_org_id)



class ToolsDSLSearch:
    def __init__(self,
                 tool_store: AgentAllowedToolStore,
                 action_store: AgentAllowedToolActionStore,
                 workflows_base_uri: str):
        self.tool_store = tool_store
        self.action_store = action_store
        self.workflows_base_uri = workflows_base_uri.rstrip("/")

    def select_tool_by_input(self,
                             workflow_id: str,
                             user_input: Dict[str, Any],
                             global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedTool]:
        
        try:
            tool_list = [tool.to_dict() for tool in self.tool_store.list_all()]

            if not tool_list:
                logger.warning("Tool list is empty.")
                return None

            executor = new_dsl_workflow_executor(
                workflow_id=workflow_id,
                workflows_base_uri=self.workflows_base_uri,
                is_remote=False,
                addons=global_settings or {}
            )

            dsl_input = {
                "user_input": user_input,
                "list_input": tool_list
            }

            output = executor.execute(dsl_input)
            selected_tool_id = parse_dsl_output(output)
            if not selected_tool_id:
                logger.warning("DSL returned no selected tool.")
                return None

            tool = self.tool_store.get(selected_tool_id)
            if tool:
                logger.info(f"Tool '{selected_tool_id}' selected via DSL.")
                return tool
            else:
                logger.warning(f"Selected tool '{selected_tool_id}' not found.")
                return None
        except Exception as e:
            logger.error(f"Exception in DSL tool selection: {e}")
            return None

    def select_action_by_input(self,
                               workflow_id: str,
                               user_input: Dict[str, Any],
                               global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedToolAction]:
        
        try:
            action_list = [action.to_dict() for action in self.action_store.list_all()]

            if not action_list:
                logger.warning("Action list is empty.")
                return None

            executor = new_dsl_workflow_executor(
                workflow_id=workflow_id,
                workflows_base_uri=self.workflows_base_uri,
                is_remote=False,
                addons=global_settings or {}
            )

            dsl_input = {
                "user_input": user_input,
                "list_input": action_list
            }

            output = executor.execute(dsl_input)
            selected_action_type = parse_dsl_output(output)
            if not selected_action_type:
                logger.warning("DSL returned no selected action.")
                return None

            for action in self.action_store.list_all():
                if action.action_type == selected_action_type:
                    logger.info(f"Action '{selected_action_type}' selected via DSL.")
                    return action

            logger.warning(f"Selected action '{selected_action_type}' not found.")
            return None
        except Exception as e:
            logger.error(f"Exception in DSL action selection: {e}")
            return None

    def dsl_select_tool_from_action(self,
                                    action_type: str,
                                    mapping_org_id: str,
                                    user_input: Dict[str, Any],
                                    global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedTool]:
       
        try:
            action = self.action_store.get(action_type, mapping_org_id)
            if not action:
                logger.warning(f"No action found for '{action_type}' and org '{mapping_org_id}'")
                return None

            tool_candidates = [self.tool_store.get(tid).to_dict()
                               for tid in action.mapped_tool_ids if self.tool_store.get(tid)]

            if not tool_candidates:
                logger.warning("No valid tool candidates found for the action.")
                return None

            executor = new_dsl_workflow_executor(
                workflow_id=action_type,
                workflows_base_uri=self.workflows_base_uri,
                is_remote=False,
                addons=global_settings or {}
            )

            dsl_input = {
                "user_input": user_input,
                "list_input": tool_candidates
            }

            output = executor.execute(dsl_input)
            selected_tool_id = parse_dsl_output(output)

            if not selected_tool_id:
                logger.warning("DSL returned no selected tool.")
                return None

            tool = self.tool_store.get(selected_tool_id)
            if tool:
                logger.info(f"Tool '{selected_tool_id}' selected via DSL from action.")
                return tool
            else:
                logger.warning(f"Selected tool '{selected_tool_id}' not found in store.")
                return None
        except Exception as e:
            logger.error(f"Exception during DSL-based tool selection from action: {e}")
            return None