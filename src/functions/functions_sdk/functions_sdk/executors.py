import requests
import websocket
import json
import os
from typing import Optional

import logging
from .schema import FunctionEntry

logger = logging.getLogger("FunctionsRegistryDB")
logger.setLevel(logging.INFO)


class FunctionsRegistryDB:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        logger.info(
            f"FunctionsRegistryDB client initialized with base URL: {self.base_url}")

    def get_function_by_id(self, function_id: str) -> Optional[FunctionEntry]:
        url = f"{self.base_url}/functions/{function_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved function '{function_id}'")
                return FunctionEntry.from_dict(data)
            elif response.status_code == 404:
                logger.warning(f"Function '{function_id}' not found.")
                return None
            else:
                logger.error(
                    f"Failed to get function '{function_id}', status code: {response.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(
                f"Request error while fetching function '{function_id}': {e}")
            return None


class HTTPExecutor:
    def __init__(self, function: FunctionEntry, input_data: dict):
        self.function = function
        self.input_data = input_data

    def execute(self):
        try:
            if self.function.function_calling_data.get("method", "POST").upper() == "GET":
                response = requests.get(
                    self.function.function_url, params=self.input_data)
            else:  # Default to POST
                response = requests.post(
                    self.function.function_url, json=self.input_data)

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"HTTP Execution failed: {e}")


class WebSocketExecutor:
    def __init__(self, function: FunctionEntry, input_data: dict):
        self.function = function
        self.input_data = input_data

    def execute(self):
        try:
            ws = websocket.create_connection(self.function.function_url)
            ws.send(json.dumps(self.input_data))
            response = ws.recv()
            ws.close()
            return json.loads(response)
        except Exception as e:
            raise Exception(f"WebSocket Execution failed: {e}")


class FunctionsExecutorManager:
    def __init__(self):
        self.db_client = FunctionsRegistryDB(os.getenv("FUNCTIONS_DB_URL"))
        self.function_instances = {}  # Maps instance_name to function data
        # FunctionsRegistry client for fetching function info
        self.sdk = FunctionsRegistryDB("FUNCTIONS_DB_URL")

    def validate_input(self, input_data, api_spec):
        def validate(data, spec, path="root"):
            if not isinstance(spec, dict):
                raise ValueError(
                    f"Invalid API spec at {path}. Must be a dict.")

            for key, constraints in spec.items():
                if key not in data:
                    raise ValueError(
                        f"Missing required field '{key}' at {path}.")

                value = data[key]
                field_type = constraints.get("type", "any")

                # Type validation logic
                if field_type == "number":
                    if not isinstance(value, (int, float)):
                        raise ValueError(
                            f"Field '{key}' at {path} must be a number.")
                    if "min" in constraints and value < constraints["min"]:
                        raise ValueError(
                            f"Field '{key}' at {path} must be >= {constraints['min']}.")
                    if "max" in constraints and value > constraints["max"]:
                        raise ValueError(
                            f"Field '{key}' at {path} must be <= {constraints['max']}.")
                elif field_type == "string":
                    if not isinstance(value, str):
                        raise ValueError(
                            f"Field '{key}' at {path} must be a string.")
                    if "choices" in constraints and value not in constraints["choices"]:
                        raise ValueError(
                            f"Field '{key}' at {path} must be one of {constraints['choices']}.")
                elif field_type == "array":
                    if not isinstance(value, list):
                        raise ValueError(
                            f"Field '{key}' at {path} must be an array.")
                elif field_type == "object":
                    if not isinstance(value, dict):
                        raise ValueError(
                            f"Field '{key}' at {path} must be an object.")
                    nested_spec = constraints.get("properties", {})
                    validate(value, nested_spec, path=f"{path}.{key}")
                elif field_type == "any":
                    pass  # No validation required for "any"
                else:
                    raise ValueError(
                        f"Unsupported type '{field_type}' for field '{key}' at {path}.")

        validate(input_data, api_spec)
        return True

    def register(self, instance_name, function_id):

        try:
            logging.info(
                f"Registering function: instance_name={instance_name}, function_id={function_id}")
            function_data = self.sdk.get_function_by_id(function_id)

            if instance_name in self.function_instances:
                raise ValueError(
                    f"Instance {instance_name} is already registered.")

            # Store the function data, executor will be initialized during execution
            self.function_instances[instance_name] = {
                "function_data": function_data
            }
            logging.info(f"Successfully registered function: {instance_name}")

        except Exception as e:
            logging.error(
                f"Error registering function: instance_name={instance_name}, error={e}")
            raise

    def unregister(self, instance_name):

        try:
            logging.info(
                f"Unregistering function: instance_name={instance_name}")
            if instance_name in self.function_instances:
                del self.function_instances[instance_name]
                logging.info(
                    f"Successfully unregistered function: {instance_name}")
            else:
                raise KeyError(f"Instance {instance_name} not found.")
        except Exception as e:
            logging.error(
                f"Error unregistering function: instance_name={instance_name}, error={e}")
            raise

    def execute(self, instance_name, input_data):

        try:
            logging.info(
                f"Executing function: instance_name={instance_name}, input_data={input_data}")
            if instance_name not in self.function_instances:
                raise KeyError(f"Instance {instance_name} not found.")

            instance = self.function_instances[instance_name]
            function_data = instance["function_data"]
            api_spec = function_data.get("function_api_spec", {})

            # Validate input_data against the API spec
            self.validate_input(input_data, api_spec)

            # Initialize the appropriate executor based on protocol type
            if function_data["function_protocol_type"] == "http":
                executor = HTTPExecutor(
                    function=function_data, input_data=input_data)
            elif function_data["function_protocol_type"] == "websocket":
                executor = WebSocketExecutor(
                    function=function_data, input_data=input_data)
            else:
                raise ValueError(
                    f"Unsupported protocol type {function_data['function_protocol_type']}")

            # Execute the function using the executor
            result = executor.execute()

            if not result['success']:
                raise Exception(result['message'])

            return result['data']

        except Exception as e:
            logging.error(
                f"Error executing function: instance_name={instance_name}, error={e}")
            raise

    def get_instance_data(self, instance_name):

        try:
            logging.info(f"Fetching data for instance: {instance_name}")
            if instance_name in self.function_instances:
                return self.function_instances[instance_name]["function_data"]
            else:
                raise KeyError(f"Instance {instance_name} not found.")
        except Exception as e:
            logging.error(
                f"Error fetching instance data: instance_name={instance_name}, error={e}")


class FunctionExecutor:
    def __init__(self, function_id, function_data):
        self.function_id = function_id
        self.function_data = function_data
        self.executor = self._initialize_executor()

    def _initialize_executor(self):
        if self.function_data["function_protocol_type"] == "http":
            return HTTPExecutor(function=self.function_data)
        elif self.function_data["function_protocol_type"] == "websocket":
            return WebSocketExecutor(function=self.function_data)
        else:
            raise ValueError(
                f"Unsupported protocol type {self.function_data['function_protocol_type']}")

    def validate_inputs(self, input_data):
        def validate(data, spec, path="root"):
            if not isinstance(spec, dict):
                raise ValueError(
                    f"Invalid API spec at {path}. Must be a dict.")

            for key, constraints in spec.items():
                if key not in data:
                    raise ValueError(
                        f"Missing required field '{key}' at {path}.")

                value = data[key]
                field_type = constraints.get("type", "any")

                if field_type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(
                        f"Field '{key}' at {path} must be a number.")
                elif field_type == "string" and not isinstance(value, str):
                    raise ValueError(
                        f"Field '{key}' at {path} must be a string.")
                elif field_type == "array" and not isinstance(value, list):
                    raise ValueError(
                        f"Field '{key}' at {path} must be an array.")
                elif field_type == "object" and not isinstance(value, dict):
                    raise ValueError(
                        f"Field '{key}' at {path} must be an object.")
                elif field_type == "any":
                    pass
                else:
                    raise ValueError(
                        f"Unsupported type '{field_type}' for field '{key}' at {path}.")

        api_spec = self.function_data.get("function_api_spec", {})
        validate(input_data, api_spec)
        return True

    def execute(self, input_data):
        try:
            logging.info(
                f"Executing function: function_id={self.function_id}, input_data={input_data}")
            self.validate_input(input_data)
            result = self.executor.execute(input_data)

            if not result['success']:
                raise Exception(result['message'])

            logging.info(
                f"Successfully executed function: function_id={self.function_id}")
            return result['data']
        except Exception as e:
            logging.error(
                f"Error executing function: function_id={self.function_id}, error={e}")
            raise


class FunctionWorkflowExecutor:
    def __init__(self, functions_manager: FunctionsManager):
        self.functions_manager = functions_manager

    def execute_workflow(self,
                         workflow_id: str,
                         mapping_org_id: str,
                         user_input: Dict[str, Any],
                         initial_payload: Dict[str, Any],
                         global_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a function workflow based on DAG returned from workflow_to_functions_graph.

        Args:
            workflow_id: ID of the workflow (workflow_type).
            mapping_org_id: Org ID used to fetch the workflow graph and actions.
            user_input: Input used for DSL-based selection.
            initial_payload: Payload to be passed into the root function.
            global_settings: Additional context for DSL execution.

        Returns:
            A dictionary mapping function_id to its output result.
        """
        try:
            logger.info(f"Executing function workflow '{workflow_id}' for org '{mapping_org_id}'")

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

                logger.info(f"Executing function '{fid}' with input: {input_data}")
                output = self.functions_manager.execute_function_by_id(fid, input_data)
                logger.info(f"Function '{fid}' executed successfully.")
                results[fid] = output

            # Topological execution
            visited = set()
            stack = [fid for fid in function_graph if not reverse_deps[fid]]  # Start with roots

            while stack:
                node = stack.pop(0)
                if node in visited:
                    continue
                preds = reverse_deps[node]
                if all(pred in results for pred in preds):
                    execute_node(node)
                    visited.add(node)
                    stack.extend([succ for succ in function_graph[node] if succ not in visited])
                else:
                    stack.append(node)  # Defer execution until dependencies are met

            return results

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise