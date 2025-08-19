import logging
import os
from typing import List, Dict, Any, Optional

from .local_table import (
    AgentAllowedFunction,
    AgentAllowedFunctionAction,
    AgentAllowedFunctionStore,
    AgentAllowedFunctionActionStore,
    AgentAllowedWorkflowStore,
    FunctionsDSLSearch
)
from .executors import FunctionsExecutorManager
from .db_client import FunctionsRegistryDB

logger = logging.getLogger("FunctionsManager")
logger.setLevel(logging.INFO)


class FunctionsManager:
    def __init__(self, functions_db_url: str, workflows_base_uri: str):
        self.functions_db_url = functions_db_url
        self.workflow_uri = workflows_base_uri
        self.func_store = AgentAllowedFunctionStore()
        self.action_store = AgentAllowedFunctionActionStore()
        self.workflow_store = AgentAllowedWorkflowStore()
        self.dsl_search = FunctionsDSLSearch(
            func_store=self.func_store,
            action_store=self.action_store,
            workflow_store=self.workflow_store,
            workflows_base_uri=workflows_base_uri
        )
        self.executor = FunctionsExecutorManager()
        self.workflow_executor = FunctionWorkflowExecutor(self)

    def add_function(self, function_id: str, derived_from: str, mapping_org_id: str) -> bool:
        try:
            logger.info(f"Adding function from DB: {function_id}")
            response = FunctionsRegistryDB(
                os.getenv("FUNCTIONS_DB_URL")).get_function_by_id(function_id)
            if not response:
                logger.warning(f"Function '{function_id}' not found in DB.")
                return False

            function = AgentAllowedFunction.from_dict(response)
            function.derived_from = derived_from
            function.mapping_org_id = mapping_org_id
            return self.func_store.create(function)
        except Exception as e:
            logger.error(f"Failed to add function '{function_id}': {e}")
            return False

    def create_action(self,
                      action_type: str,
                      function_ids: List[str],
                      action_tags: List[str],
                      action_metadata: Dict[str, Any],
                      action_search_description: str,
                      action_dsl: Dict[str, Any],
                      derived_from: str,
                      mapping_org_id: str) -> bool:
        try:
            missing = [
                fid for fid in function_ids if not self.func_store.get(fid)]
            if missing:
                logger.warning(
                    f"Cannot create action. Missing functions: {missing}")
                return False

            action = AgentAllowedFunctionAction(
                action_type=action_type,
                mapped_function_ids=function_ids,
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

    def search_function(self, workflow_id: str, user_input: Dict[str, Any],
                        global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedFunction]:
        return self.dsl_search.select_function_by_input(workflow_id, user_input, global_settings)

    def search_action(self, workflow_id: str, user_input: Dict[str, Any],
                      global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedFunctionAction]:
        return self.dsl_search.select_action_by_input(workflow_id, user_input, global_settings)

    def search_function_from_action(self, action_type: str, mapping_org_id: str,
                                    user_input: Dict[str, Any], global_settings: Optional[Dict[str, Any]] = None
                                    ) -> Optional[AgentAllowedFunction]:
        return self.dsl_search.dsl_select_function_from_action(
            action_type=action_type,
            mapping_org_id=mapping_org_id,
            user_input=user_input,
            global_settings=global_settings
        )

    def execute_function_by_id(self, function_id: str, input_data: Dict[str, Any]) -> Any:
        try:
            instance_name = f"instance:{function_id}"
            if instance_name not in self.executor.function_instances:
                logger.info(
                    f"Function '{function_id}' not registered. Registering now...")
                self.executor.register(instance_name, function_id)
            return self.executor.execute(instance_name, input_data)
        except Exception as e:
            logger.error(f"Failed to execute function '{function_id}': {e}")
            raise

    def execute_by_function_search(self,
                                   workflow_id: str,
                                   input_data: Dict[str, Any],
                                   search_parameters: Dict[str, Any],
                                   global_settings: Optional[Dict[str, Any]] = None) -> Any:
        try:
            func = self.search_function(
                workflow_id, search_parameters, global_settings)
            if not func:
                raise ValueError("No function matched via DSL.")
            return self.execute_function_by_id(func.function_id, input_data)
        except Exception as e:
            logger.error(f"Failed in function search + execution: {e}")
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
            return self.search_and_execute_function_from_action(
                action_type=action.action_type,
                mapping_org_id=action.mapping_org_id,
                input_data=input_data,
                search_parameters=search_parameters,
                global_settings=global_settings
            )
        except Exception as e:
            logger.error(f"Failed in action search + function execution: {e}")
            raise

    def search_and_execute_function_from_action(self,
                                                action_type: str,
                                                mapping_org_id: str,
                                                input_data: Dict[str, Any],
                                                search_parameters: Dict[str, Any],
                                                global_settings: Optional[Dict[str, Any]] = None) -> Any:
        try:
            func = self.search_function_from_action(
                action_type=action_type,
                mapping_org_id=mapping_org_id,
                user_input=search_parameters,
                global_settings=global_settings
            )
            if not func:
                raise ValueError("No function matched inside action DSL.")
            return self.execute_function_by_id(func.function_id, input_data)
        except Exception as e:
            logger.error(
                f"Failed in function selection from action + execution: {e}")
            raise
    

    def execute_workflow_dag(self,
                              workflow_id: str,
                              mapping_org_id: str,
                              user_input: Dict[str, Any],
                              initial_payload: Dict[str, Any],
                              global_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        return self.workflow_executor.execute_workflow(
            workflow_id=workflow_id,
            mapping_org_id=mapping_org_id,
            user_input=user_input,
            initial_payload=initial_payload,
            global_settings=global_settings
        )


class FunctionWorkflowExecutor:
    def __init__(self, functions_manager: FunctionsManager):
        self.functions_manager = functions_manager

    def execute_workflow(self,
                         workflow_id: str,
                         mapping_org_id: str,
                         user_input: Dict[str, Any],
                         initial_payload: Dict[str, Any],
                         global_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        try:
            logger.info(
                f"Executing function workflow '{workflow_id}' for org '{mapping_org_id}'")

            dsl_search = self.functions_manager.dsl_search
            function_graph = dsl_search.workflow_to_functions_graph(
                workflow_id=workflow_id,
                mapping_org_id=mapping_org_id,
                user_input=user_input
            )

            if not function_graph:
                raise ValueError("Empty or invalid function graph.")

            # Reverse dependency mapping: function_id -> list of predecessors
            reverse_deps = {node: [] for node in function_graph}
            for src, targets in function_graph.items():
                for dst in targets:
                    reverse_deps[dst].append(src)

            results = {}  # function_id -> output

            def execute_node(fid: str):
                # Prepare input: combine results from predecessors
                input_data = {}
                for pred in reverse_deps[fid]:
                    input_data.update(results.get(pred, {}))
                if not reverse_deps[fid]:
                    input_data.update(initial_payload)

                logger.info(
                    f"Executing function '{fid}' with input: {input_data}")
                output = self.functions_manager.execute_function_by_id(
                    fid, input_data)
                logger.info(f"Function '{fid}' executed successfully.")
                results[fid] = output

            # Topological execution
            visited = set()
            # Start with roots
            stack = [fid for fid in function_graph if not reverse_deps[fid]]

            while stack:
                node = stack.pop(0)
                if node in visited:
                    continue
                preds = reverse_deps[node]
                if all(pred in results for pred in preds):
                    execute_node(node)
                    visited.add(node)
                    stack.extend(
                        [succ for succ in function_graph[node] if succ not in visited])
                else:
                    # Defer execution until dependencies are met
                    stack.append(node)

            return results

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise
