from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR / "static" / "files"
ALLOWED_EXTENSIONS = {"pdf", "png"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    """Return whether a filename has one of the supported extensions."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def has_valid_file_signature(uploaded_file, filename: str) -> bool:
    """Return whether the file header matches its supported extension."""
    extension = filename.rsplit(".", 1)[1].lower()
    signature_length = 8 if extension == "png" else 5
    header = uploaded_file.stream.read(signature_length)
    uploaded_file.stream.seek(0)

    if extension == "png":
        return header == b"\x89PNG\r\n\x1a\n"
    return header == b"%PDF-"


def format_file_size(size: int) -> str:
    """Format a file size using a readable unit."""
    units = ("B", "KB", "MB", "GB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{size} B"
        value /= 1024
    return f"{size} B"


def list_uploaded_files() -> list[dict[str, str]]:
    """Return uploaded file names and readable sizes in stable display order."""
    files = []
    for path in sorted(UPLOAD_FOLDER.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file():
            files.append({"name": path.name, "size": format_file_size(path.stat().st_size)})
    return files


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me"),
        MAX_CONTENT_LENGTH=MAX_UPLOAD_SIZE,
        UPLOAD_FOLDER=str(UPLOAD_FOLDER),
    )
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(_error):
        flash("File is too large. Maximum upload size is 10 MB.")
        return redirect(url_for("index"))

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            uploaded = request.files.get("file")

            if uploaded is None or not uploaded.filename:
                flash("Please choose a file to upload.")
                return redirect(url_for("index"))

            filename = secure_filename(uploaded.filename)
            if not filename or not allowed_file(filename):
                flash("Only PNG and PDF files are allowed.")
                return redirect(url_for("index"))

            if not has_valid_file_signature(uploaded, filename):
                flash("The file content does not match its extension.")
                return redirect(url_for("index"))

            destination = UPLOAD_FOLDER / filename
            if destination.exists():
                flash("This file already exists. Please choose another file.")
                return redirect(url_for("index"))

            uploaded.save(destination)
            flash(f"{filename} uploaded successfully.")
            return redirect(url_for("index"))

        return render_template("main.html", files=list_uploaded_files())

    @app.route("/files/<path:filename>")
    def uploaded_file(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.post("/delete/<path:filename>")
    def delete_file(filename: str):
        safe_filename = secure_filename(filename)
        if not safe_filename or safe_filename != filename:
            flash("Invalid file name.")
            return redirect(url_for("index"))

        file_path = UPLOAD_FOLDER / safe_filename
        if not file_path.is_file():
            flash("File not found.")
            return redirect(url_for("index"))

        file_path.unlink()
        flash(f"{safe_filename} deleted successfully.")
        return redirect(url_for("index"))

    return app


app = create_app()
