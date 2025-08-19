from concurrent import futures
import grpc
import logging

from .decorator import ToolExecutor

from . import rpc_service_pb2
from . import rpc_service_pb2_grpc
from .sync import ToolRegistrySyncer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ToolGRPCServer")


class ToolExecutorService(rpc_service_pb2_grpc.ToolExecutorServicer):
    def __init__(self):
        self.executor = ToolExecutor()

    def CallFunction(self, request, context):
        tool_name = request.tool_name
        input_bytes = request.input

        logger.info(f"Received RPC call for tool: {tool_name}")
        success, output, error, metadata = self.executor.execute(
            tool_name, input_bytes)

        return rpc_service_pb2.CallFunctionResponse(
            success=success,
            output=output,
            error=error,
            metadata=metadata
        )


def serve(port: int = 50051):
    
    sync = ToolRegistrySyncer()
    sync.sync_tools()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rpc_service_pb2_grpc.add_ToolExecutorServicer_to_server(
        ToolExecutorService(), server)
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"Starting ToolExecutor gRPC server on port {port}")
    server.start()
    server.wait_for_termination()

