from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os, shutil, uuid

app = FastAPI()

# CORS para frontend se comunicar com backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração Supabase via variáveis de ambiente
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/upload/")
async def upload_files(file: UploadFile = File(...)):
    temp_filename = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Simulando geração de catálogo (substituir depois)
    html_path = temp_filename.replace(".csv", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<html><body><h1>Catálogo gerado!</h1></body></html>")

    # Upload para Supabase
    with open(html_path, "rb") as f:
        file_key = f"catalogos/{os.path.basename(html_path)}"
        supabase.storage.from_('catalogos').upload(file_key, f, {"content-type": "text/html"})

    url = f"{SUPABASE_URL.replace('.supabase.co', '.supabase.storage.co')}/storage/v1/object/public/catalogos/{os.path.basename(html_path)}"
    return JSONResponse({"url": url})
