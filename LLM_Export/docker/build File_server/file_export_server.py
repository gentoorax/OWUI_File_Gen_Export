# C:\temp\LLM_Export\tools\file_export_server.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
import pathlib

EXPORT_DIR = os.getenv("EXPORT_DIR", "/data/output")
os.makedirs(EXPORT_DIR, exist_ok=True)

app = FastAPI()

# Route pour servir les fichiers avec téléchargement forcé
@app.get("/files/{folder_name}/{filename}")
async def serve_file(folder_name: str, filename: str):
    # Construire le chemin complet du fichier
    file_path = os.path.join(EXPORT_DIR, folder_name, filename)

    # Vérifier que le fichier existe
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    # Forcer le téléchargement (au lieu d'afficher dans le navigateur)
    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=filename,  # Force le nom de fichier téléchargé
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Montage du dossier static (pour les autres fichiers)
app.mount("/files", StaticFiles(directory=EXPORT_DIR), name="files")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9003)