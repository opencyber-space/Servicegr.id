import grpc
import logging
import json
from typing import Dict, Any

from . import rpc_service_pb2, rpc_service_pb2_grpc
from .resolver import Resolver

logger = logging.getLogger("ToolExecutorClient")
logging.basicConfig(level=logging.INFO)


class ToolExecutorClient:
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.target = f"{host}:{port}"
        try:
            self.channel = grpc.insecure_channel(self.target)
            self.stub = rpc_service_pb2_grpc.ToolExecutorStub(self.channel)
            logger.info(f"Connected to ToolExecutor at {self.target}")
        except Exception as e:
            logger.exception(f"Failed to connect to gRPC server at {self.target}")
            raise

    def call_tool(self, tool_name: str, input_bytes: bytes) -> Dict[str, Any]:
        try:
            request = rpc_service_pb2.CallFunctionRequest(
                tool_name=tool_name,
                input=input_bytes
            )
            response = self.stub.CallFunction(request)
            logger.info(f"Called tool '{tool_name}'")

            return {
                "success": response.success,
                "output": response.output,
                "error": response.error,
                "metadata": dict(response.metadata)
            }

        except grpc.RpcError as rpc_error:
            logger.error(f"RPC failed for tool '{tool_name}': {rpc_error}")
            return {
                "success": False,
                "output": b"",
                "error": str(rpc_error),
                "metadata": {}
            }
        except Exception as e:
            logger.exception(f"Unexpected error calling tool '{tool_name}'")
            return {
                "success": False,
                "output": b"",
                "error": str(e),
                "metadata": {}
            }


class ToolsExecutor:
    def __init__(self, grpc_port: int = 50051):
        self.resolver = Resolver(port=grpc_port)

    def execute_tool(self, tool_name: str, node_id: str, input_bytes: bytes) -> Dict[str, Any]:
        try:
            endpoint = self.resolver.resolve(tool_name, node_id)
            if not endpoint:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found on node '{node_id}'",
                    "output": None,
                    "metadata": {}
                }

            host, port = endpoint.split(":")
            client = ToolExecutorClient(host=host, port=int(port))
            response = client.call_tool(tool_name, input_bytes)

            # Attempt to decode bytes to JSON if possible
            output_json = None
            try:
                output_json = json.loads(response["output"].decode())
            except Exception:
                output_json = response["output"].decode(errors="replace")

            return {
                "success": response["success"],
                "output": output_json,
                "error": response["error"],
                "metadata": response["metadata"]
            }

        except Exception as e:
            logger.exception(f"Failed to execute tool '{tool_name}' on node '{node_id}'")
            return {
                "success": False,
                "error": str(e),
                "output": None,
                "metadata": {}
            }