from __future__ import annotations

import os
import subprocess
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_UPLOAD_FOLDER = BASE_DIR / "files"
#DEFAULT_UPLOAD_FOLDER = Path(r"Z:\IT Department\Manuelito\files")
ALLOWED_EXTENSIONS = {"pdf", "png"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    """Return whether a filename has one of the supported extensions."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_upload_folder(upload_folder: Path) -> None:
    """Ensure the configured upload location can be created and used."""
    if upload_folder.drive and not Path(f"{upload_folder.drive}\\").exists():
        raise RuntimeError(
            f"Upload drive '{upload_folder.drive}' is unavailable. "
            f"Check the configured path: {upload_folder}"
        )

    if upload_folder.exists() and not upload_folder.is_dir():
        raise RuntimeError(f"Upload path is not a directory: {upload_folder}")

    try:
        upload_folder.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise RuntimeError(f"Cannot create upload directory: {upload_folder}") from error


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


def list_uploaded_files(upload_folder: Path) -> list[dict[str, str]]:
    """Return uploaded file names and readable sizes in stable display order."""
    files = []
    for path in sorted(upload_folder.iterdir(), key=lambda item: item.name.lower()):
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
        UPLOAD_FOLDER=str(DEFAULT_UPLOAD_FOLDER),
        UPLOAD_FOLDER_ERROR=None,
    )
    try:
        validate_upload_folder(DEFAULT_UPLOAD_FOLDER)
    except RuntimeError as error:
        app.config["UPLOAD_FOLDER_ERROR"] = str(error)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(_error):
        flash("File is too large. Maximum upload size is 10 MB.", "error")
        return redirect(url_for("index"))

    @app.get("/browse-folder")
    def browse_folder():
        try:
            current_folder = Path(app.config["UPLOAD_FOLDER"])
            initial_folder = str(current_folder if current_folder.is_dir() else BASE_DIR)
            folder_picker = (
                "$InitialDirectory = $env:UPLOAD_INITIAL_DIRECTORY; "
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
                "$dialog.Description = 'Choose upload folder'; "
                "$dialog.SelectedPath = $InitialDirectory; "
                "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
                "{ $dialog.SelectedPath }"
            )
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-STA", "-Command", folder_picker],
                capture_output=True,
                text=True,
                timeout=300,
                env={**os.environ, "UPLOAD_INITIAL_DIRECTORY": initial_folder},
            )
            if result.returncode != 0:
                details = result.stderr.strip() or "PowerShell returned an unknown error."
                raise RuntimeError(details)
            selected_folder = result.stdout.strip()
        except Exception as error:
            flash(f"Could not open the folder browser: {error}", "error")
            return redirect(url_for("index"))

        if not selected_folder:
            return redirect(url_for("index"))

        upload_folder = Path(selected_folder)
        try:
            validate_upload_folder(upload_folder)
        except RuntimeError as error:
            flash(str(error), "error")
            return redirect(url_for("index"))

        app.config["UPLOAD_FOLDER"] = str(upload_folder)
        app.config["UPLOAD_FOLDER_ERROR"] = None
        flash(f"Files will now be saved in {upload_folder}.")
        return redirect(url_for("index"))

    @app.post("/settings")
    def update_settings():
        folder_text = request.form.get("upload_folder", "").strip()
        if not folder_text:
            flash("Please enter a folder path.", "error")
            return redirect(url_for("index"))

        upload_folder = Path(folder_text).expanduser()
        try:
            validate_upload_folder(upload_folder)
        except RuntimeError as error:
            flash(str(error), "error")
            return redirect(url_for("index"))

        app.config["UPLOAD_FOLDER"] = str(upload_folder)
        app.config["UPLOAD_FOLDER_ERROR"] = None
        flash(f"Files will now be saved in {upload_folder}.")
        return redirect(url_for("index"))

    @app.route("/", methods=["GET", "POST"])
    def index():
        upload_folder_error = app.config["UPLOAD_FOLDER_ERROR"]
        if upload_folder_error:
            flash(upload_folder_error, "error")
            return render_template("main.html", files=[], upload_folder=app.config["UPLOAD_FOLDER"])

        upload_folder = Path(app.config["UPLOAD_FOLDER"])

        if request.method == "POST":
            uploaded = request.files.get("file")

            if uploaded is None or not uploaded.filename:
                flash("Please choose a file to upload.", "error")
                return redirect(url_for("index"))

            filename = secure_filename(uploaded.filename)
            if not filename or not allowed_file(filename):
                flash("Only PNG and PDF files are allowed.", "error")
                return redirect(url_for("index"))

            if not has_valid_file_signature(uploaded, filename):
                flash("The file content does not match its extension.", "error")
                return redirect(url_for("index"))

            destination = upload_folder / filename
            if destination.exists():
                flash("This file already exists. Please choose another file.", "error")
                return redirect(url_for("index"))

            uploaded.save(destination)
            flash(f"{filename} uploaded successfully.")
            return redirect(url_for("index"))

        return render_template(
            "main.html",
            files=list_uploaded_files(upload_folder),
            upload_folder=app.config["UPLOAD_FOLDER"],
        )

    @app.route("/files/<path:filename>")
    def uploaded_file(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.post("/delete/<path:filename>")
    def delete_file(filename: str):
        safe_filename = secure_filename(filename)
        if not safe_filename or safe_filename != filename:
            flash("Invalid file name.", "error")
            return redirect(url_for("index"))

        file_path = Path(app.config["UPLOAD_FOLDER"]) / safe_filename
        if not file_path.is_file():
            flash("File not found.", "error")
            return redirect(url_for("index"))

        file_path.unlink()
        flash(f"{safe_filename} deleted successfully.")
        return redirect(url_for("index"))

    return app


app = create_app()
