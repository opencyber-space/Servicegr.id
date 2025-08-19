import asyncio
import websockets
import logging
import json

from .handler import Handler


class FunctionWebSocketServer:
    def __init__(self, handler: Handler):
        self._setup_logging()
        self.handler_instance: Handler = handler

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("FunctionWebSocketServer")
        self.logger.info("FunctionWebSocketServer initialized")

    async def handler(self, websocket, path):
        try:
            async for message in websocket:
                self.logger.info(f"Received message: {message}")

                message = json.loads(message)

                self.handler_instance.validate(message)

                response = self.handler_instance.execute(message)

                response = {"success": True,
                            "data": response}
                
                await websocket.send(json.dumps(response))
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            error_response = {"success": False, "message": str(e)}
            await websocket.send(json.dumps(error_response))

    def run_server(self, host='0.0.0.0', port=5000):
        self.logger.info(f"Starting WebSocket server on {host}:{port}")
        start_server = websockets.serve(self.handler, host, port)

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


def start_websocket_server(handler_class):
    server = FunctionWebSocketServer(handler_class)
    server.run_server()
