import logging
import os
from typing import List, Dict, Any, Optional

from .local_table import AgentAllowedTool
from .local_table import AgentAllowedToolAction
from .local_table import AgentAllowedToolStore
from .local_table import AgentAllowedToolActionStore
from .local_table import ToolsDSLSearch
from .tools_manager import ToolsExecutionManager
from .db_client import ToolsRegistrySDK

logger = logging.getLogger("ToolsManager")
logger.setLevel(logging.INFO)


class ToolsManager:
    def __init__(self, tools_db_url: str, workflows_base_uri: str):
        self.tools_db_url = tools_db_url
        self.workflow_uri = workflows_base_uri
        self.tool_store = AgentAllowedToolStore()
        self.action_store = AgentAllowedToolActionStore()
        self.dsl_search = ToolsDSLSearch(
            self.tool_store, self.action_store, workflows_base_uri)
        self.executor = ToolsManager(ToolsRegistrySDK(
            os.getenv("TOOLS_REGISTRY_API_URL")
        ))

    def add_tool(self, tool_id: str, derived_from: str, mapping_org_id: str) -> bool:
        try:
            logger.info(f"Adding tool from DB: {tool_id}")
            response = ToolsRegistrySDK().get_tool_by_id(tool_id)
            if not response:
                logger.warning(f"Tool '{tool_id}' not found in DB.")
                return False

            tool = AgentAllowedTool.from_dict(response)
            tool.derived_from = derived_from
            tool.mapping_org_id = mapping_org_id
            return self.tool_store.create(tool)
        except Exception as e:
            logger.error(f"Failed to add tool '{tool_id}': {e}")
            return False

    def create_action(self,
                      action_type: str,
                      tool_ids: List[str],
                      action_tags: List[str],
                      action_metadata: Dict[str, Any],
                      action_search_description: str,
                      action_dsl: Dict[str, Any],
                      derived_from: str,
                      mapping_org_id: str) -> bool:
        try:
            missing = [tid for tid in tool_ids if not self.tool_store.get(tid)]
            if missing:
                logger.warning(
                    f"Cannot create action. Missing tools: {missing}")
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
            logger.error(f"Failed to create action '{action_type}': {e}")
            return False

    def search_tool(self, workflow_id: str, user_input: Dict[str, Any],
                    global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedTool]:
        return self.dsl_search.select_tool_by_input(workflow_id, user_input, global_settings)

    def search_action(self, workflow_id: str, user_input: Dict[str, Any],
                      global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedToolAction]:
        return self.dsl_search.select_action_by_input(workflow_id, user_input, global_settings)

    def search_tool_from_action(self, action_type: str, mapping_org_id: str,
                                user_input: Dict[str, Any], global_settings: Optional[Dict[str, Any]] = None
                                ) -> Optional[AgentAllowedTool]:
        return self.dsl_search.dsl_select_tool_from_action(action_type, mapping_org_id, user_input, global_settings)

    def execute_tool_by_id(self, tool_id: str, input_data: Dict[str, Any]) -> Any:
        try:
            instance_name = f"instance:{tool_id}"
            if instance_name not in self.executor.tool_instances:
                logger.info(
                    f"Tool '{tool_id}' not registered, registering now...")
                self.executor.register(instance_name, tool_id)
            return self.executor.execute(instance_name, input_data)
        except Exception as e:
            logger.error(f"Failed to execute tool '{tool_id}': {e}")
            raise

    def execute_by_tool_search(self,
                               workflow_id: str,
                               input_data: Dict[str, Any],
                               search_parameters: Dict[str, Any],
                               global_settings: Optional[Dict[str, Any]] = None) -> Any:

        try:
            tool = self.search_tool(
                workflow_id, search_parameters, global_settings)
            if not tool:
                raise ValueError("No tool matched via DSL.")
            return self.execute_tool_by_id(tool.tool_id, input_data)
        except Exception as e:
            logger.error(f"Failed in tool search + execution: {e}")
            raise

    def execute_by_action_search(self,
                                 workflow_id: str,
                                 input_data: Dict[str, Any],
                                 search_parameters: Dict[str, Any],
                                 global_settings: Optional[Dict[str, Any]] = None) -> Any:

        try:
            action = self.search_action(
                workflow_id, search_parameters, global_settings)
            if not action:
                raise ValueError("No action matched via DSL.")

            return self.search_and_execute_tool_from_action(
                action_type=action.action_type,
                mapping_org_id=action.mapping_org_id,
                input_data=input_data,
                search_parameters=search_parameters,
                global_settings=global_settings
            )
        except Exception as e:
            logger.error(f"Failed in action search + tool execution: {e}")
            raise

    def search_and_execute_tool_from_action(self,
                                            action_type: str,
                                            mapping_org_id: str,
                                            input_data: Dict[str, Any],
                                            search_parameters: Dict[str, Any],
                                            global_settings: Optional[Dict[str, Any]] = None) -> Any:

        try:
            tool = self.search_tool_from_action(
                action_type=action_type,
                mapping_org_id=mapping_org_id,
                user_input=search_parameters,
                global_settings=global_settings
            )
            if not tool:
                raise ValueError("No tool matched inside action DSL.")
            return self.execute_tool_by_id(tool.tool_id, input_data)
        except Exception as e:
            logger.error(
                f"Failed in tool selection from action + execution: {e}")
            raise
