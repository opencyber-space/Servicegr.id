from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import logging
import requests
import networkx as nx

from dsl_executor import new_dsl_workflow_executor, parse_dsl_output

logger = logging.getLogger("AgentAllowedFunctionSystem")
logger.setLevel(logging.INFO)


@dataclass
class AgentAllowedFunction:
    function_id: str = ''
    function_metadata: Dict[str, Any] = field(default_factory=dict)
    function_search_description: str = ''
    function_tags: List[str] = field(default_factory=list)
    function_type: str = ''
    function_man_page_doc: str = ''
    function_api_spec: Dict[str, Any] = field(default_factory=dict)
    func_custom_actions_dsl_map: Dict[str, Any] = field(default_factory=dict)
    default_func_usage_credentials: Dict[str, Any] = field(
        default_factory=dict)
    open_api_spec: Dict[str, Any] = field(default_factory=dict)
    api_parameters_to_cost_relation_data: Dict[str, Any] = field(
        default_factory=dict)
    is_system_action: bool = False
    derived_from: str = ''
    mapping_org_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentAllowedFunction":
        return cls(
            function_id=data.get("function_id", ""),
            function_metadata=data.get("function_metadata", {}),
            function_search_description=data.get(
                "function_search_description", ""),
            function_tags=data.get("function_tags", []),
            function_type=data.get("function_type", ""),
            function_man_page_doc=data.get("function_man_page_doc", ""),
            function_api_spec=data.get("function_api_spec", {}),
            func_custom_actions_dsl_map=data.get(
                "func_custom_actions_dsl_map", {}),
            default_func_usage_credentials=data.get(
                "default_func_usage_credentials", {}),
            open_api_spec=data.get("open_api_spec", {}),
            api_parameters_to_cost_relation_data=data.get(
                "api_parameters_to_cost_relation_data", {}),
            is_system_action=data.get("is_system_action", False),
            derived_from=data.get("derived_from", ""),
            mapping_org_id=data.get("mapping_org_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


@dataclass
class AgentAllowedFunctionAction:
    action_type: str = ''
    mapped_function_ids: List[str] = field(default_factory=list)
    action_tags: List[str] = field(default_factory=list)
    action_metadata: Dict[str, Any] = field(default_factory=dict)
    action_search_description: str = ''
    action_dsl: Dict[str, Any] = field(default_factory=dict)
    derived_from: str = ''
    mapping_org_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentAllowedFunctionAction":
        return cls(
            action_type=data.get("action_type", ""),
            mapped_function_ids=data.get("mapped_function_ids", []),
            action_tags=data.get("action_tags", []),
            action_metadata=data.get("action_metadata", {}),
            action_search_description=data.get(
                "action_search_description", ""),
            action_dsl=data.get("action_dsl", {}),
            derived_from=data.get("derived_from", ""),
            mapping_org_id=data.get("mapping_org_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


@dataclass
class AgentAllowedWorkflow:
    workflow_type: str = ''
    workflow_actions: List[str] = field(default_factory=list)
    workflow_tags: List[str] = field(default_factory=list)
    workflow_metadata: Dict[str, Any] = field(default_factory=dict)
    workflow_search_description: str = ''
    derived_from: str = ''
    mapping_org_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentAllowedWorkflow":
        return cls(
            workflow_type=data.get("workflow_type", ""),
            workflow_actions=data.get("workflow_actions", []),
            workflow_tags=data.get("workflow_tags", []),
            workflow_metadata=data.get("workflow_metadata", {}),
            workflow_search_description=data.get(
                "workflow_search_description", ""),
            derived_from=data.get("derived_from", ""),
            mapping_org_id=data.get("mapping_org_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


class AgentAllowedFunctionStore:
    def __init__(self):
        self._store: Dict[str, AgentAllowedFunction] = {}

    def create(self, func: AgentAllowedFunction) -> bool:
        if func.function_id in self._store:
            logger.warning(f"Function '{func.function_id}' already exists.")
            return False
        self._store[func.function_id] = func
        logger.info(f"Function '{func.function_id}' added.")
        return True

    def get(self, function_id: str) -> Optional[AgentAllowedFunction]:
        return self._store.get(function_id)

    def update(self, function_id: str, updates: Dict) -> bool:
        func = self._store.get(function_id)
        if not func:
            logger.warning(f"Function '{function_id}' not found.")
            return False
        for k, v in updates.items():
            if hasattr(func, k):
                setattr(func, k, v)
        logger.info(f"Function '{function_id}' updated.")
        return True

    def delete(self, function_id: str) -> bool:
        if function_id in self._store:
            del self._store[function_id]
            logger.info(f"Function '{function_id}' deleted.")
            return True
        return False

    def list_all(self) -> List[AgentAllowedFunction]:
        return list(self._store.values())


class AgentAllowedFunctionActionStore:
    def __init__(self):
        self._store: Dict[str, AgentAllowedFunctionAction] = {}

    def _get_key(self, action: AgentAllowedFunctionAction) -> str:
        return f"{action.action_type}:{action.mapping_org_id}"

    def create(self, action: AgentAllowedFunctionAction) -> bool:
        key = self._get_key(action)
        if key in self._store:
            logger.warning(f"Action '{key}' already exists.")
            return False
        self._store[key] = action
        logger.info(f"Action '{key}' added.")
        return True

    def get(self, action_type: str, mapping_org_id: str) -> Optional[AgentAllowedFunctionAction]:
        return self._store.get(f"{action_type}:{mapping_org_id}")

    def update(self, action_type: str, mapping_org_id: str, updates: Dict) -> bool:
        key = f"{action_type}:{mapping_org_id}"
        action = self._store.get(key)
        if not action:
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
            return True
        return False

    def list_all(self) -> List[AgentAllowedFunctionAction]:
        return list(self._store.values())


class AgentAllowedWorkflowStore:
    def __init__(self):
        self._store: Dict[str, AgentAllowedWorkflow] = {}

    def _get_key(self, workflow_type: str, mapping_org_id: str) -> str:
        return f"{workflow_type}:{mapping_org_id}"

    def create(self, workflow: AgentAllowedWorkflow) -> bool:
        key = self._get_key(workflow.workflow_type, workflow.mapping_org_id)
        if key in self._store:
            logger.warning(f"Workflow '{key}' already exists.")
            return False
        self._store[key] = workflow
        logger.info(f"Workflow '{key}' added.")
        return True

    def get(self, workflow_type: str, mapping_org_id: str) -> Optional[AgentAllowedWorkflow]:
        return self._store.get(self._get_key(workflow_type, mapping_org_id))

    def update(self, workflow_type: str, mapping_org_id: str, updates: Dict[str, Any]) -> bool:
        key = self._get_key(workflow_type, mapping_org_id)
        workflow = self._store.get(key)
        if not workflow:
            logger.warning(f"Workflow '{key}' not found.")
            return False
        for k, v in updates.items():
            if hasattr(workflow, k):
                setattr(workflow, k, v)
        logger.info(f"Workflow '{key}' updated.")
        return True

    def delete(self, workflow_type: str, mapping_org_id: str) -> bool:
        key = self._get_key(workflow_type, mapping_org_id)
        if key in self._store:
            del self._store[key]
            logger.info(f"Workflow '{key}' deleted.")
            return True
        logger.warning(f"Workflow '{key}' not found for deletion.")
        return False

    def list_all(self) -> List[AgentAllowedWorkflow]:
        return list(self._store.values())


class FunctionsManagement:
    def __init__(self, functions_db_url: str):
        self.functions_db_url = functions_db_url.rstrip("/")
        self.func_store = AgentAllowedFunctionStore()
        self.action_store = AgentAllowedFunctionActionStore()

    def add_function_for_agent(self, function_id: str, derived_from: str, mapping_org_id: str) -> bool:
        try:
            url = f"{self.functions_db_url}/functions/{function_id}"
            response = requests.get(url)
            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch function '{function_id}': {response.status_code}")
                return False

            func_data = response.json()
            func = AgentAllowedFunction.from_dict(func_data)
            func.derived_from = derived_from
            func.mapping_org_id = mapping_org_id

            return self.func_store.create(func)
        except Exception as e:
            logger.error(
                f"Exception while adding function '{function_id}': {e}")
            return False

    def create_action(self, action_type: str, function_ids: List[str], action_tags: List[str],
                      action_metadata: Dict[str, Any], action_search_description: str,
                      action_dsl: Dict[str, Any], derived_from: str, mapping_org_id: str) -> bool:
        try:
            missing = [
                fid for fid in function_ids if self.func_store.get(fid) is None]
            if missing:
                logger.warning(f"Missing functions: {missing}")
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
            logger.error(
                f"Exception while creating action '{action_type}': {e}")
            return False

    def list_agent_functions(self) -> List[AgentAllowedFunction]:
        return self.func_store.list_all()

    def list_agent_actions(self) -> List[AgentAllowedFunctionAction]:
        return self.action_store.list_all()

    def get_function(self, function_id: str) -> Optional[AgentAllowedFunction]:
        return self.func_store.get(function_id)

    def get_action(self, action_type: str, mapping_org_id: str) -> Optional[AgentAllowedFunctionAction]:
        return self.action_store.get(action_type, mapping_org_id)


class FunctionsDSLSearch:
    def __init__(self, func_store: AgentAllowedFunctionStore, action_store: AgentAllowedFunctionActionStore,
                 workflow_store: AgentAllowedWorkflowStore,
                 workflows_base_uri: str):
        self.func_store = func_store
        self.action_store = action_store
        self.workflow_store = workflow_store
        self.workflows_base_uri = workflows_base_uri.rstrip("/")

    def select_function_by_input(self, workflow_id: str, user_input: Dict[str, Any],
                                 global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedFunction]:
        try:
            func_list = [func.to_dict() for func in self.func_store.list_all()]
            if not func_list:
                return None

            executor = new_dsl_workflow_executor(
                workflow_id=workflow_id,
                workflows_base_uri=self.workflows_base_uri,
                is_remote=False,
                addons=global_settings or {}
            )
            output = executor.execute({
                "user_input": user_input,
                "list_input": func_list
            })

            selected_function_id = parse_dsl_output(output)
            return self.func_store.get(selected_function_id)
        except Exception as e:
            logger.error(f"Function selection DSL failed: {e}")
            return None

    def select_action_by_input(self, workflow_id: str, user_input: Dict[str, Any],
                               global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedFunctionAction]:
        try:
            action_list = [a.to_dict() for a in self.action_store.list_all()]
            if not action_list:
                return None

            executor = new_dsl_workflow_executor(
                workflow_id=workflow_id,
                workflows_base_uri=self.workflows_base_uri,
                is_remote=False,
                addons=global_settings or {}
            )
            output = executor.execute({
                "user_input": user_input,
                "list_input": action_list
            })
            selected_action_type = parse_dsl_output(output)

            for action in self.action_store.list_all():
                if action.action_type == selected_action_type:
                    return action
            return None
        except Exception as e:
            logger.error(f"Action selection DSL failed: {e}")
            return None

    def dsl_select_function_from_action(self, action_type: str, mapping_org_id: str,
                                        user_input: Dict[str, Any],
                                        global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedFunction]:
        try:
            action = self.action_store.get(action_type, mapping_org_id)
            if not action:
                return None

            candidates = [self.func_store.get(fid).to_dict()
                          for fid in action.mapped_function_ids if self.func_store.get(fid)]

            executor = new_dsl_workflow_executor(
                workflow_id=action_type,
                workflows_base_uri=self.workflows_base_uri,
                is_remote=False,
                addons=global_settings or {}
            )
            output = executor.execute({
                "user_input": user_input,
                "list_input": candidates
            })

            selected_function_id = parse_dsl_output(output)
            return self.func_store.get(selected_function_id)
        except Exception as e:
            logger.error(f"Function-from-action DSL failed: {e}")
            return None

    def select_workflow_by_input(self,
                                 workflow_id: str,
                                 user_input: Dict[str, Any],
                                 global_settings: Optional[Dict[str, Any]] = None) -> Optional[AgentAllowedWorkflow]:
        try:
            workflow_list = [w.to_dict()
                             for w in self.workflow_store.list_all()]
            if not workflow_list:
                logger.warning("Workflow list is empty.")
                return None

            executor = new_dsl_workflow_executor(
                workflow_id=workflow_id,
                workflows_base_uri=self.workflows_base_uri,
                is_remote=False,
                addons=global_settings or {}
            )

            dsl_input = {
                "user_input": user_input,
                "list_input": workflow_list
            }

            output = executor.execute(dsl_input)
            selected_workflow_type = parse_dsl_output(output)

            for workflow in self.workflow_store.list_all():
                if workflow.workflow_type == selected_workflow_type:
                    logger.info(
                        f"Workflow '{selected_workflow_type}' selected via DSL.")
                    return workflow

            logger.warning(f"Workflow '{selected_workflow_type}' not found.")
            return None
        except Exception as e:
            logger.error(f"Exception in DSL workflow selection: {e}")
            return None

    def workflow_to_functions_graph(self, workflow_id: str, mapping_org_id: str, user_input: Dict[str, Any]) -> Dict[str, List[str]]:

        try:
            # Step 1: Load workflow and validate it
            workflow = self.workflow_store.get(workflow_id, mapping_org_id)
            if not workflow:
                logger.error(
                    f"Workflow '{workflow_id}' for org '{mapping_org_id}' not found.")
                return {}

            graph_data = workflow.workflow_actions  # expected as adjacency dict
            if not isinstance(graph_data, dict):
                logger.error(
                    f"Invalid workflow_actions format in workflow '{workflow_id}'")
                return {}

            G = nx.DiGraph()
            for src, targets in graph_data.items():
                for dst in targets:
                    G.add_edge(src, dst)

            if not nx.is_directed_acyclic_graph(G):
                raise ValueError(f"Workflow '{workflow_id}' contains cycles.")

            logger.info(f"Workflow '{workflow_id}' validated as DAG.")

            selected_functions = {} 
            function_graph = {}  

            for action_node in nx.topological_sort(G):
                predecessors = list(G.predecessors(action_node))

                prev_func_data = {
                    prev: selected_functions[prev].to_dict()
                    for prev in predecessors if prev in selected_functions
                }

                # Step 3: Get action and run DSL to select function
                action = self.action_store.get(action_node, mapping_org_id)
                if not action:
                    logger.warning(
                        f"No action '{action_node}' found for workflow.")
                    continue

                candidates = [self.func_store.get(fid).to_dict()
                            for fid in action.mapped_function_ids if self.func_store.get(fid)]

                if not candidates:
                    logger.warning(
                        f"No valid function candidates for action '{action_node}'")
                    continue

                executor = new_dsl_workflow_executor(
                    workflow_id=action_node,
                    workflows_base_uri=self.workflows_base_uri,
                    is_remote=False,
                    addons=user_input.get("global_settings", {})
                )

                dsl_input = {
                    "user_input": user_input,
                    "list_input": candidates,
                    "previous_nodes": prev_func_data
                }

                output = executor.execute(dsl_input)
                selected_function_id = parse_dsl_output(output)

                selected_func = self.func_store.get(selected_function_id)
                if not selected_func:
                    logger.warning(
                        f"Selected function '{selected_function_id}' not found.")
                    continue

                selected_functions[action_node] = selected_func
                function_graph[selected_func.function_id] = []

                for prev in predecessors:
                    if prev in selected_functions:
                        prev_func_id = selected_functions[prev].function_id
                        function_graph.setdefault(prev_func_id, []).append(
                            selected_func.function_id)

            return function_graph

        except Exception as e:
            logger.error(
                f"Error building function graph for workflow '{workflow_id}': {e}")
            return {}
