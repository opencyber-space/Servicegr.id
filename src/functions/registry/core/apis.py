from flask import Flask, request, jsonify
from flask_graphql import GraphQLView
import logging

from .crud import FunctionsRegistryCRUD
from .uploader import FunctionsS3Uploader
from .parser import FunctionPackageParser
from .schema import FunctionEntry
from .ql import schema  # Your GraphQL schema for functions

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FunctionsAPI")

# Initialize services
crud = FunctionsRegistryCRUD(mongo_uri="mongodb://localhost:27017")
s3_uploader = FunctionsS3Uploader(
    aws_access_key_id="ACCESS",
    aws_secret_access_key="SECRET",
    bucket_name="functions-assets",
    endpoint_url="http://ceph.local:9000",
    public_url_base="http://ceph.local:9000/functions-assets"
)
zip_parser = FunctionPackageParser(s3_uploader=s3_uploader, registry_crud=crud)


@app.route("/functions/upload", methods=["POST"])
def upload_function_bundle():
    if "file" not in request.files:
        return jsonify({"error": "Missing file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_path = f"/tmp/{file.filename}"
    file.save(file_path)
    function_id = zip_parser.process_zip_package(file_path)

    if not function_id:
        return jsonify({"error": "Failed to process function package"}), 500

    return jsonify({"message": "Function uploaded successfully", "function_id": function_id}), 200


@app.route("/functions/<function_id>", methods=["GET"])
def get_function(function_id):
    function = crud.get_function(function_id)
    if function:
        return jsonify(function.to_dict()), 200
    return jsonify({"error": "Function not found"}), 404


@app.route("/functions/<function_id>", methods=["PUT"])
def update_function(function_id):
    updates = request.json
    if not updates:
        return jsonify({"error": "Missing update payload"}), 400

    success = crud.update_function(function_id, updates)
    if success:
        return jsonify({"message": "Function updated successfully"}), 200
    return jsonify({"error": "Function not found"}), 404


@app.route("/functions/<function_id>", methods=["DELETE"])
def delete_function(function_id):
    success = crud.delete_function(function_id)
    if success:
        return jsonify({"message": "Function deleted successfully"}), 200
    return jsonify({"error": "Function not found"}), 404


@app.route("/functions/query/by-type", methods=["GET"])
def query_function_by_type():
    function_type = request.args.get("type")
    return jsonify([f.to_dict() for f in crud.get_functions_by_type(function_type)]), 200


@app.route("/functions/query/by-tag", methods=["GET"])
def query_function_by_tag():
    tag = request.args.get("tag")
    return jsonify([f.to_dict() for f in crud.get_functions_by_tag(tag)]), 200


@app.route("/functions/query/by-keyword", methods=["GET"])
def query_function_by_keyword():
    keyword = request.args.get("keyword")
    return jsonify([f.to_dict() for f in crud.get_functions_by_search_text(keyword)]), 200


@app.route("/functions/query/by-system-flag", methods=["GET"])
def query_function_by_system_flag():
    is_system = request.args.get("is_system", "false").lower() == "true"
    return jsonify([f.to_dict() for f in crud.get_functions_by_system_flag(is_system)]), 200


@app.route("/functions/query/generic", methods=["POST"])
def query_function_generic():
    mongo_query = request.json
    return jsonify([f.to_dict() for f in crud.query_functions(mongo_query)]), 200


app.add_url_rule(
    "/functions/graphql",
    view_func=GraphQLView.as_view(
        "functions_graphql",
        schema=schema,
        graphiql=True,
        get_context=lambda: {"crud": crud}
    )
)


def run_functions_server():
    app.run(host='0.0.0.0', port=6000)
