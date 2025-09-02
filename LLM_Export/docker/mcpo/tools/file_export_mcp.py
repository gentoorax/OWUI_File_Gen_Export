import os
import logging
import uuid
import datetime
import zipfile
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

def _public_url(folder_path: str, filename: str) -> str:
    """Build a stable public URL for a generated file."""
    folder = os.path.basename(folder_path).lstrip("/")
    name = filename.lstrip("/")
    return f"{BASE_URL}/{folder}/{name}"

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
    filepath = os.path.join(folder_path, filename)
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
        filename = file_info.get("filename")
        content = file_info.get("content")
        format_type = file_info.get("format")
 
        if content is None:
            content = ""        

        filepath, fname = _generate_filename(folder_path, format_type, filename)
        
        if format_type == "py" or format_type == "cs" or format_type == "txt":
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
                story.append(Paragraph(content, styles["Normal"]))
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
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        
        generated_files.append(filepath)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if archive_format.lower() == "7z":
        archive_filename = f"{archive_name or 'archive'}_{timestamp}.7z"
        archive_path = os.path.join(folder_path, archive_filename)
        with py7zr.SevenZipFile(archive_path, mode='w') as archive:
            for file_path in generated_files:
                archive.write(file_path, os.path.basename(file_path))
    else: 
        archive_filename = f"{archive_name or 'archive'}_{timestamp}.zip"
        archive_path = os.path.join(folder_path, archive_filename)
        with zipfile.ZipFile(archive_path, 'w') as zipf:
            for file_path in generated_files:
                zipf.write(file_path, os.path.basename(file_path))
    
    return {"url": _public_url(folder_path, archive_filename)}

if __name__ == "__main__":
    log.info("Starting MCP server: file_export")
    mcp.run()
