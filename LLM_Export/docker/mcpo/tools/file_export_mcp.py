import os
import logging
import uuid
import datetime
import zipfile
import base64
import py7zr
from mcp.server.fastmcp import FastMCP
from openpyxl import Workbook
import csv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


EXPORT_DIR = r"/output"
os.makedirs(EXPORT_DIR, exist_ok=True)

# Read the file server base URL from environment (fallback to local default).
# Example to set in k8s:
#   FILE_EXPORT_BASE_URL=http://file-export-server.ai-system.svc.cluster.local:9003/files
BASE_URL_ENV = os.getenv("FILE_EXPORT_BASE_URL")
BASE_URL = (BASE_URL_ENV or "http://localhost:9003/files").rstrip("/")

# Basic logger (honours LOG_LEVEL if you set it)
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
log = logging.getLogger("file_export_mcp")

# Announce effective config on startup
if BASE_URL_ENV:
    log.info("FILE_EXPORT_BASE_URL set -> %s", BASE_URL)
else:
    log.warning("FILE_EXPORT_BASE_URL not set; using default -> %s", BASE_URL)
log.info("EXPORT_DIR -> %s", EXPORT_DIR)

mcp = FastMCP("file_export")


def _generate_unique_folder() -> str:
    folder_name = f"export_{uuid.uuid4().hex[:10]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    folder_path = os.path.join(EXPORT_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def _generate_filename(folder_path: str, ext: str, filename: str = None) -> tuple[str, str]:
    if not filename:
        filename = f"export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    base, ext = os.path.splitext(filename)
    filepath = os.path.join(folder_path, filename)
    counter = 1
    while os.path.exists(filepath):
        filename = f"{base}_{counter}{ext}"
        filepath = os.path.join(folder_path, filename)
        counter += 1
    return filepath, filename


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def _public_url(folder_path: str, filename: str) -> str:
    """Build a stable public URL for a generated file."""
    folder = os.path.basename(folder_path).lstrip("/")
    name = filename.lstrip("/")
    return f"{BASE_URL}/{folder}/{name}"


def _infer_ext_from_name(name: str) -> str:
    _, ext = os.path.splitext(name)
    return ext.lstrip(".").lower()


def _normalize_file_info(file_info: dict) -> tuple[str, str, str]:
    """
    Returns (rel_path, content, fmt).
    Accepts either:
      - {"filename": "...", "content": "...", "format": "cs"}
      - {"filename": "...", "code": "..."}                  # code alias
      - {"path/inside/zip/Program.cs": "..."}               # single-key map
    """
    if "filename" in file_info:
        rel_path = file_info["filename"]
        # accept 'content' or 'code' (alias)
        content = file_info.get("content", file_info.get("code"))
        fmt = (file_info.get("format") or _infer_ext_from_name(rel_path)) or "txt"
        return rel_path, content, fmt
    if len(file_info) == 1:
        rel_path, content = next(iter(file_info.items()))
        fmt = _infer_ext_from_name(rel_path) or "txt"
        return rel_path, content, fmt
    raise ValueError(
        "Invalid file_info; expected {filename,content[,format]} (or 'code' alias) "
        "or a single-key mapping {path: content}."
    )


@mcp.tool()
def create_excel(data: list[list[str]], filename: str = None) -> dict:
    folder_path = _generate_unique_folder()
    filepath, fname = _generate_filename(folder_path, "xlsx", filename)
    wb = Workbook()
    ws = wb.active
    for row in data:
        ws.append(row)
    wb.save(filepath)
    return {"url": _public_url(folder_path, fname)}


@mcp.tool()
def create_csv(data: list[list[str]], filename: str = None) -> dict:
    folder_path = _generate_unique_folder()
    filepath, fname = _generate_filename(folder_path, "csv", filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(data)
    return {"url": _public_url(folder_path, fname)}


@mcp.tool()
def create_pdf(text: list[str], filename: str = None) -> dict:
    folder_path = _generate_unique_folder()
    filepath, fname = _generate_filename(folder_path, "pdf", filename)
    doc = SimpleDocTemplate(filepath)
    styles = getSampleStyleSheet()
    story = []
    for t in text:
        story.append(Paragraph(t, styles["Normal"]))
        story.append(Spacer(1, 12))
    doc.build(story)
    return {"url": _public_url(folder_path, fname)}


@mcp.tool()
def create_file(content: str, filename: str) -> dict:
    folder_path = _generate_unique_folder()
    base, ext = os.path.splitext(filename)
    filepath = os.path.join(folder_path, filename.lstrip("/"))
    _ensure_parent_dir(filepath)
    counter = 1
    while os.path.exists(filepath):
        filename = f"{base}_{counter}{ext}"
        filepath = os.path.join(folder_path, filename)
        counter += 1
    if ext.lower() == ".xml" and not content.strip().startswith("<?xml"):
        content = f'<?xml version="1.0" encoding="UTF-8"?>\n{content}'
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return {"url": _public_url(folder_path, filename)}


@mcp.tool()
def generate_and_archive(files_data: list[dict], archive_format: str = "zip", archive_name: str = None) -> dict:
    folder_path = _generate_unique_folder()
    generated_files = []

    for file_info in files_data:
        rel_path, content, format_type = _normalize_file_info(file_info)

        # Use provided relative path if any; otherwise synthesize a name
        if rel_path:
            filepath = os.path.join(folder_path, rel_path.lstrip("/"))
            fname = os.path.basename(filepath)
        else:
            filepath, fname = _generate_filename(folder_path, format_type, None)

        _ensure_parent_dir(filepath)

        # Accept a ready-made base64 zip/7z and write it as-is
        if format_type in ("zip", "7z") and isinstance(content, str) and len(content) > 0:
            try:
                raw = base64.b64decode(content, validate=True)
                with open(filepath, "wb") as f:
                    f.write(raw)
                generated_files.append(filepath)
                continue
            except Exception:
                # Not valid base64; fall through to text handling
                pass

        if format_type in ("py", "cs", "txt", "md", "json", "xml", "yml", "yaml", "sh", "bat", "ps1"):
            if content is None:
                raise ValueError(f"Missing 'content' for {rel_path}")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        elif format_type == "pdf":
            doc = SimpleDocTemplate(filepath)
            styles = getSampleStyleSheet()
            story = []
            if isinstance(content, list):
                for t in content:
                    story.append(Paragraph(t, styles["Normal"]))
                    story.append(Spacer(1, 12))
            else:
                story.append(Paragraph((content or ""), styles["Normal"]))
                story.append(Spacer(1, 12))
            doc.build(story)
        elif format_type == "xlsx":
            wb = Workbook()
            ws = wb.active
            if isinstance(content, list):
                for row in content:
                    ws.append(row)
            wb.save(filepath)
        elif format_type == "csv":
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                if isinstance(content, list):
                    csv.writer(f).writerows(content)
                else:
                    csv.writer(f).writerow([content])
        else:
            if content is None:
                content = ""
            mode = "wb" if isinstance(content, (bytes, bytearray)) else "w"
            with open(filepath, mode, encoding=None if "b" in mode else "utf-8") as f:
                f.write(content)

        generated_files.append(filepath)

    # Build archive file name cleanly (avoid double extensions)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    name = (archive_name or "archive")
    if name.lower().endswith(".zip"):
        name = name[: -len(".zip")]
    if name.lower().endswith(".7z"):
        name = name[: -len(".7z")]

    if archive_format.lower() == "7z":
        archive_filename = f"{name}_{timestamp}.7z"
        archive_path = os.path.join(folder_path, archive_filename)
        with py7zr.SevenZipFile(archive_path, mode='w') as archive:
            for file_path in generated_files:
                arcname = os.path.relpath(file_path, start=folder_path)  # keep folder structure
                archive.write(file_path, arcname)
    else:
        archive_format = "zip"
        archive_filename = f"{name}_{timestamp}.zip"
        archive_path = os.path.join(folder_path, archive_filename)
        with zipfile.ZipFile(archive_path, 'w') as zipf:
            for file_path in generated_files:
                arcname = os.path.relpath(file_path, start=folder_path)  # keep folder structure
                zipf.write(file_path, arcname)

    return {"url": _public_url(folder_path, archive_filename)}


if __name__ == "__main__":
    log.info("Starting MCP server: file_export")
    mcp.run()
