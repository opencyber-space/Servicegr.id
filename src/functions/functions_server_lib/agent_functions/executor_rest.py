from flask import Flask, jsonify, request
import logging

from .handler import Handler


class FunctionServer:
    def __init__(self, handler: Handler):
        self.app = Flask(__name__)
        self._setup_routes()
        self._setup_logging()
        self.handler = handler

    def _setup_routes(self):
        @self.app.route('/')
        def home():
            try:
                message = request.get_json()
                self.handler.validate(message)
                response = self.handler.execute(message)
                return jsonify({"success": True, "data": response})
            except Exception as e:
                self.app.logger.error(f"Error in home route: {e}")
                return jsonify({"success": False, "message": str(e)}), 500

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.app.logger.info("FunctionServer initialized")

    def run_server(self, host='0.0.0.0', port=5000):
        try:
            self.app.logger.info(f"Starting server on {host}:{port}")
            self.app.run(host=host, port=port)
        except Exception as e:
            self.app.logger.error(f"Error starting server: {e}")


if __name__ == "__main__":
    server = FunctionServer()
    server.run_server()
