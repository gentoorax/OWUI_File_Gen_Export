# LLM_Export - File Export Tool

🚀 **Create and export files easily from Open WebUI!**

This tool allows seamless file generation and export directly from your Open WebUI environment using Python and FastAPI.

## Multi files

https://github.com/user-attachments/assets/41dadef9-7981-4439-bf5f-3b82fcbaff04


## Single archive

https://github.com/user-attachments/assets/1e70a977-62f1-498c-895c-7db135ded95b



---

## 📌 How to Use

### 1. Clone or Download the Repository

- Clone the Git repository or download and unzip the folder where you want it.

### 2. Update Configuration Files

You need to modify two files:

1. `LLM_Export/tools/file_export_server.py`
2. `LLM_Export/tools/file_export_mcp.py`

Replace the placeholder values:

- `YourPATH` → Your actual project path (e.g., `/home/user/LLM_Export`)
- `YourURL` → Your server URL (e.g., `http://localhost:8000`)
- `YourAPIkey` → Your MCPO API key

### 3. Install Required Dependencies

Run the following command to install all required packages:

```bash
pip install openpyxl reportlab py7zr fastapi uvicorn python-multipart
```

> ✅ These packages are essential for:
> - `openpyxl` → Excel file generation
> - `reportlab` → PDF creation
> - `py7zr` → 7z archive support
> - `fastapi` + `uvicorn` → Backend server
> - `python-multipart` → File upload handling

### 4. Configure MCPO Server

Update your `config.json` with the following snippet:

```json
{
  "mcpServers": {
    "file_export": {
      "command": "python",
      "args": [
        "-m",
        "LLM_Export.tools.file_export_mcp"
      ],
      "env": {
        "PYTHONPATH": "YourPATH"
      },
      "disabled": false,
      "autoApprove": []
    }
  },
  "logLevel": "DEBUG"
}
```

Replace `YourPATH` with the same path used in the Python files.

### 5. Start the Servers

Use this batch script (`start_servers.bat`) to launch both servers:

```bat
@echo off
start "MCPO Server" mcpo --host 0.0.0.0 --port 9002 --api-key "YourAPIkey" --config "PathTo\config.json"
start "File Export Server" python "YourPATH\LLM_Export\tools\file_export_server.py" --> Add this line to your MCPO start script
exit
```

> 💡 Replace:
> - `YourAPIkey` with your actual MCPO API key
> - `PathTo\config.json` with the correct path
> - `YourPATH` with your project root path

---

## 🛠️ Troubleshooting

- If the file export fails, check:
  - `PYTHONPATH` is correctly set
  - All dependencies are installed
  - The server ports are not blocked
  - The `config.json` file is valid JSON

---

## 📦 Supported File Types

- ✅ `.xlsx` (Excel)
- ✅ `.pdf` (PDF)
- ✅ `.csv` (CSV)
- ✅ `.*` (Every other file types)
- ✅ `.zip` and `.7z` (Archives)



# Example of config :

### In `file_export_mcp.py`:

line 12: ``EXPORT_DIR = r"C:\temp\LLM_Export\output"``
line 15: ``BASE_URL = "http://192.168.0.60:9003/files"``



### In `file_export_server.py`:

line 9: ``EXPORT_DIR = r"C:\temp\LLM_Export\output"``

### MCPO config.json:
```json
{
  "mcpServers": {
    "file_export": {
      "command": "python",
      "args": [
        "-m",
        "LLM_Export.tools.file_export_mcp"
      ],
      "env": {
        "PYTHONPATH": "C:\\temp"
      },
      "disabled": false,
      "autoApprove": []
    }
  },
  "logLevel": "DEBUG"
}
```


---

## 📎 License

MIT License – Feel free to use, modify, and distribute.

---

📬 **Need help?** Open an issue or a discussion on the GitHub repository! 

---

