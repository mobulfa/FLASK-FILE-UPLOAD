# Flask File Upload

A small Flask application for uploading, viewing, and deleting PNG and PDF files.
Uploaded files are stored in `static/files` and displayed in a table with their
file name, size, download link, and delete action.

## Features

- Upload PNG and PDF files.
- Enforce a maximum upload size of 10 MB.
- Verify file signatures so renamed text or script files are rejected.
- Sanitize uploaded filenames before saving them.
- Reject duplicate filenames.
- Display uploaded file names and formatted file sizes.
- Download uploaded files by selecting their file name.
- Delete uploaded files with an icon action button.
- Show validation and upload status messages in the page.
- Record successful uploads and deletions in a SQLite database.
- Serve CSS and JavaScript from the `static/assets` folder.

## Project Structure

```text
FLASK-FILE-UPLOAD/
├── app.py                    # Application entry point
├── module/
│   ├── __init__.py
│   └── main.py               # Flask app, routes, and upload logic
├── templates/
│   └── main.html             # Upload page and file table
├── static/
│   ├── assets/
│   │   ├── main.js
│   │   └── style.css
├── files/                    # Default uploaded files folder
├── file_history.db           # Local SQLite history database (created at startup)
├── file_history.json         # Legacy history file used for one-time migration
├── requirements.txt
└── README.md
```

## Setup

Create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the App

Start the Flask development server with:

```powershell
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser.

## Upload Rules

- Accepted extensions: `.png` and `.pdf`
- Maximum request size: 10 MB
- The file signature must match the extension:
	- PNG files must contain the standard PNG signature.
	- PDF files must begin with `%PDF-`.
- A file cannot be uploaded if another file with the same name already exists.

## Configuration

Set `FLASK_SECRET_KEY` to replace the development secret key used by Flask:

```powershell
$env:FLASK_SECRET_KEY = "your-secret-key"
```

## SQLite History Database

The application uses SQLite to record successful upload and delete actions.
The database is created automatically in the project root as `file_history.db`.
Its `file_history` table stores the action, filename, timestamp, and computer
name for each event.

If `file_history.json` exists when the application starts and the SQLite table
is empty, its records are imported once. Both local history files are ignored
by Git.

The current application is intended for local development. Use a production
WSGI server and additional security scanning before deploying it publicly.