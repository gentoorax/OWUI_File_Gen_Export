# OWUI_File_Gen_Export – Export Files Directly from Open WebUI

A lightweight, MCPO-integrated tool that lets you **generate and export real files** (PDF, Excel, ZIP, etc.) directly from Open WebUI — just like ChatGPT or Claude.

✅ Supports both **Python** and **Docker**  
✅ Fully configurable  
✅ Ready for production workflows  
✅ Open source & MIT licensed

---

🚀 **Create and export files easily from Open WebUI!**

This tool allows seamless file generation and export directly from your Open WebUI environment using Python and FastAPI.

## Multi files

https://github.com/user-attachments/assets/41dadef9-7981-4439-bf5f-3b82fcbaff04


## Single archive

https://github.com/user-attachments/assets/1e70a977-62f1-498c-895c-7db135ded95b


## 🚀 Quick Start

### 🔧 For Python Users

1. Clone the repo:
   ```bash
   git clone https://github.com/GlisseManTV/OWUI_File_Gen_Export.git
   ```

2. Update `YourPATH` and `YourURL` in:
   - `LLM_Export/tools/file_export_server.py`
   - `LLM_Export/tools/file_export_mcp.py`

3. Install dependencies:
   ```bash
   pip install openpyxl reportlab py7zr fastapi uvicorn python-multipart mcp
   ```

4. Run the server:
   ```bat
   start "File Export Server" python "YourPATH/LLM_Export/tools/file_export_server.py"
   ```

5. Use it in Open WebUI — your AI can now generate and export files in real time!

---

## 🐳 Docker Support (Recommended)

All Docker configurations are in the `docker/` folder.

### 📦 File Export Server (Docker)

📁 Path: `docker/file_server/`

- `Dockerfile.server`
- `file_server_compose.yaml`
- `file_export_server.py`

🔧 **Setup:**
- Update `port` in `file_server_compose.yaml` if needed
- Set `path to output` to your **absolute host path** (e.g., `/home/user/exports`)
- Ensure `Dockerfile.server` and `file_export_server.py` are in the **same directory**

> ⚠️ Important: `Dockerfile.server` and `file_export_server.py` must be in the same folder for build to work.

---

### 🖥️ MCPO Server (Docker)

📁 Path: `docker/mcpo/`

- `Dockerfile`
- `requirements.txt`
- `config.json`
- `MCPO_server_compose.yaml`

🔧 **Setup:**
- Update `path to installation folder` and `path to output` in `MCPO_server_compose.yaml`
- `path to output` must match the one in `file_server_compose.yaml`
- Set `rootPath` to the **exact root folder** where you’ll place the `LLM_Export` folder

> ⚠️ Important: `Dockerfile` and `requirements.txt` must be in the same directory for the image to build.

---

## 🛠️ Build & Run

```yaml
# Build and run
services:
  mcpo:
    build: .
    ports:
      - 8000:8000
    volumes:
      - /mnt/Nvme_Apps/Ollama_Models:/rootPath
      - /mnt/Nvme_Apps/Ollama_Models/LLM_Export/output:/output
    command: |
      mcpo --api-key top-secret --config /rootPath/config.json
networks: {}
```
```yaml
# Build and run
services:
  file_export_server:
    build:
      context: .
      dockerfile: dockerfile.server
    container_name: file_export_server
    environment:
      - EXPORT_DIR=/data/output
    volumes:
      - /mnt/Nvme_Apps/Ollama_Models/LLM_Export/output:/data/output
    ports:
      - 9003:9003
networks: {}
```

> ✅ Always rebuild the MCPO image when adding new dependencies.

---

## 📦 Supported File Types

- ✅ `.xlsx` (Excel)
- ✅ `.pdf` (PDF)
- ✅ `.csv` (CSV)
- ✅ `.zip` and `.7z` (Archives)
- ✅ Any other file type 

---

## 📂 Project Structure

```
OWUI_File_Gen_Export/
├── LLM_Export/
│   ├── tools/
│   │   ├── file_export_server.py
│   │   └── file_export_mcp.py
│   └── ...
├── docker/
│   ├── file_server/
│   │   ├── Dockerfile.server
│   │   ├── file_server_compose.yaml
│   │   └── file_export_server.py
│   └── mcpo/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── config.json
│   │   └── MCPO_server_compose.yaml
│   └──tools/
│        └── file_export_mcp.py
└── README.md
```

---

## 📌 Notes

- File output paths must match between `file_server` and `MCPO`
- Use `docker-compose down` to stop services
- Always use **absolute paths** for volume mounts

---

## 🔗 Try It Now

👉 [GitHub Repository](https://github.com/GlisseManTV/OWUI_File_Gen_Export)

---

## 🌟 Why This Matters

This tool turns Open WebUI into a **true productivity engine** — where AI doesn’t just chat, but **delivers usable, downloadable files**.

---

## 📄 License

MIT License – Feel free to use, modify, and distribute.

---

📬 **Need help?** Open an issue or start a discussion on GitHub!

