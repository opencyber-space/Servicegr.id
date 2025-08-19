import json
from flask import Blueprint, request, jsonify
from .db import ClusterLocalToolsDB
from .db import ClusterLocalTools
from .service import ToolsExecutor
import logging

logger = logging.getLogger("ClusterLocalToolsAPI")
logging.basicConfig(level=logging.INFO)

cluster_tools_bp = Blueprint("cluster_tools_bp", __name__)
db = ClusterLocalToolsDB()

tools_executor_bp = Blueprint("tools_executor_bp", __name__)
executor = ToolsExecutor()
resolver = executor.resolver


@cluster_tools_bp.route("/tools", methods=["POST"])
def create_tool():
    try:
        data = request.json
        required_fields = {"name", "node_id", "description"}
        if not data or not required_fields.issubset(data):
            return jsonify({"error": "Missing required fields"}), 400

        tool = ClusterLocalTools.from_dict(
            data, func=lambda x: b"")  # Placeholder func
        inserted_id = db.create(tool)
        return jsonify({"message": "Tool created", "id": inserted_id}), 201
    except Exception as e:
        logger.exception("Error creating tool")
        return jsonify({"error": str(e)}), 500


@cluster_tools_bp.route("/tools/<node_id>/<name>", methods=["GET"])
def get_tool_by_name_and_node(node_id, name):
    try:
        tool = db.get_by_name_and_node(name, node_id)
        if tool:
            return jsonify(tool.to_dict()), 200
        return jsonify({"error": "Tool not found"}), 404
    except Exception as e:
        logger.exception("Error retrieving tool")
        return jsonify({"error": str(e)}), 500


@cluster_tools_bp.route("/tools/<node_id>", methods=["GET"])
def get_all_tools_for_node(node_id):
    try:
        tools = db.get_all_by_node(node_id)
        return jsonify([tool.to_dict() for tool in tools]), 200
    except Exception as e:
        logger.exception("Error retrieving tools for node")
        return jsonify({"error": str(e)}), 500


@cluster_tools_bp.route("/tools/<node_id>/<name>", methods=["PUT"])
def update_tool(node_id, name):
    try:
        updated_fields = request.json
        if not updated_fields:
            return jsonify({"error": "No fields provided to update"}), 400

        updated = db.update(name, node_id, updated_fields)
        if updated:
            return jsonify({"message": "Tool updated"}), 200
        return jsonify({"message": "No changes made"}), 200
    except Exception as e:
        logger.exception("Error updating tool")
        return jsonify({"error": str(e)}), 500


@cluster_tools_bp.route("/tools/<node_id>/<name>", methods=["DELETE"])
def delete_tool(node_id, name):
    try:
        deleted = db.delete(name, node_id)
        if deleted:
            return jsonify({"message": "Tool deleted"}), 200
        return jsonify({"error": "Tool not found"}), 404
    except Exception as e:
        logger.exception("Error deleting tool")
        return jsonify({"error": str(e)}), 500


@tools_executor_bp.route("/cluster-tools/execute", methods=["POST"])
def execute_cluster_tool():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        if "tool_name" not in data or "node_id" not in data or "input" not in data:
            return jsonify({"error": "Missing required fields: tool_name, node_id, input"}), 400

        tool_name = data["tool_name"]
        node_id = data["node_id"]
        input_payload = data["input"]

        # Convert input JSON to bytes
        try:
            input_bytes = json.dumps(input_payload).encode("utf-8")
        except Exception as e:
            logger.exception("Failed to encode input to bytes")
            return jsonify({"error": f"Invalid input serialization: {str(e)}"}), 400

        result = executor.execute_tool(tool_name, node_id, input_bytes)
        return jsonify(result), 200 if result["success"] else 500

    except Exception as e:
        logger.exception("Failed to execute cluster tool")
        return jsonify({"error": str(e)}), 500


@tools_executor_bp.route("/cluster-tools/resolve", methods=["POST"])
def resolve_cluster_tool():
    try:
        data = request.json
        if not data or "tool_name" not in data:
            return jsonify({"error": "Missing required field: tool_name"}), 400

        tool_name = data["tool_name"]

        # Query DB to find associated node_id
        tool = resolver.db.get_by_name_and_node(
            tool_name=tool_name, node_id=None)
        if not tool:
            return jsonify({"success": False, "error": f"Tool '{tool_name}' not found in database"}), 404

        endpoint = resolver.resolve(tool_name=tool.name, node_id=tool.node_id)
        if not endpoint:
            return jsonify({"success": False, "error": "Unable to resolve endpoint for tool"}), 404

        return jsonify({"success": True, "endpoint": endpoint}), 200

    except Exception as e:
        logger.exception("Failed to resolve tool endpoint")
        return jsonify({"success": False, "error": str(e)}), 500
