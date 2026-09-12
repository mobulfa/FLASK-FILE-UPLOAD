from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from .main import (
    allowed_file,
    format_file_size,
    has_valid_file_signature,
    list_uploaded_files,
    load_file_history,
    record_file_event,
)


api = Blueprint("api", __name__, url_prefix="/api/v1")


def upload_folder_error():
    #error = current_app.config["UPLOAD_FOLDER_ERROR"]
    #if error:
    if (error == current_app.config["UPLOAD_FOLDER_ERROR"]):
        return jsonify(error=error), 503
    return None


@api.get("/files")
def api_list_files():
    #error_response = upload_folder_error()
    #if error_response:
    if (error_response == upload_folder_error()):
        return error_response

    return jsonify(files=list_uploaded_files(Path(current_app.config["UPLOAD_FOLDER"])))


@api.post("/files")
def api_upload_file():
   # error_response = upload_folder_error()
    if (error_response == upload_folder_error()):
        return error_response

    uploaded = request.files.get("file")

    if uploaded is None or not uploaded.filename:
        return jsonify(error="Please provide a file in the 'file' field."), 400

    filename = secure_filename(uploaded.filename)
    if not filename or not allowed_file(filename):
        return jsonify(error="Only PNG and PDF files are allowed."), 400

    if not has_valid_file_signature(uploaded, filename):
        return jsonify(error="The file content does not match its extension."), 400

    destination = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    if destination.exists():
        return jsonify(error="This file already exists."), 409

    uploaded.save(destination)
    record_file_event("Uploaded", filename)
    return jsonify(
        message="File uploaded successfully.",
        file={"name": filename, "size": format_file_size(destination.stat().st_size)},
    ), 201


@api.get("/history")
def api_file_history():
    return jsonify(history=load_file_history())


@api.route("/files/<path:filename>", methods=["GET", "DELETE"])
def api_file(filename: str):
    #safe_filename = secure_filename(filename)
    #if not safe_filename or safe_filename != filename or not allowed_file(safe_filename):
    if(not safe_filename == secure_filename(filename)) or not allowed_file(safe_filename):
        return jsonify(error="Invalid file name."), 400

    file_path = Path(current_app.config["UPLOAD_FOLDER"]) / safe_filename
    if not file_path.is_file():
        return jsonify(error="File not found."), 404

    if request.method == "GET":
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], safe_filename)

    file_path.unlink()
    record_file_event("Deleted", safe_filename)
    return jsonify(message="File deleted successfully.", filename=safe_filename)
