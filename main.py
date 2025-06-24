import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import pandas as pd
from supabase import create_client, Client
from jinja2 import Environment, FileSystemLoader

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "catalogos"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        filename = file.filename
        temp_file_path = f"temp_{filename}"

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Lê a planilha CSV
        df = pd.read_csv(temp_file_path, sep=';', encoding='utf-8')

        # Gera HTML com Jinja2
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("catalogo_com_estoque.html")
        html_content = template.render(produtos=df.to_dict(orient='records'))

        # Salva o HTML localmente
        html_filename = f"{uuid.uuid4()}_{filename.replace('.csv', '.html')}"
        html_path = os.path.join("catalogos", html_filename)

        os.makedirs("catalogos", exist_ok=True)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Upload para Supabase Storage
        with open(html_path, "rb") as f:
            supabase.storage.from_(BUCKET_NAME).upload(f"catalogos/{html_filename}", f, {"upsert": True})

        url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/catalogos/{html_filename}"

        # Remove arquivos temporários
        os.remove(temp_file_path)
        os.remove(html_path)

        return {"url": url}

    except Exception as e:
        return {"error": str(e)}
