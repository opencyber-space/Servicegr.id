from .executor_rest import FunctionServer
from .executor_websocket import FunctionWebSocketServer

from .handler import create_handler

def start_server(obj, mode="rest", port=5555):
    try:

        handler = create_handler(obj)

        if mode == "rest":
            server = FunctionServer(handler)
            server.run_server(port=port)
        
        if mode == "websocket":
            server = FunctionWebSocketServer(handler)
            server.run_server(port=port)
        
    except Exception as e:
        raise e