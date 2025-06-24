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
    # 1. Salvar CSV com nome único
    csv_filename = f"{uuid.uuid4()}_{file.filename}"
    with open(csv_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Ler CSV
    try:
        df = pd.read_csv(csv_filename, sep=";", encoding="utf-8")
    except Exception as e:
        return {"error": f"Erro ao ler CSV: {str(e)}"}

    # 3. Gerar HTML com Jinja2
    env = Environment(loader=FileSystemLoader("templates"))
    try:
        template = env.get_template("catalogo_com_estoque.html")
    except Exception as e:
        return {"error": f"Erro ao carregar template HTML: {str(e)}"}

    html_output = template.render(produtos=df.to_dict(orient="records"))

    # 4. Salvar HTML
    html_filename = csv_filename.replace(".csv", ".html")
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_output)

    # 5. Enviar HTML para o Supabase
    try:
        with open(html_filename, "rb") as f:
            supabase.storage.from_(BUCKET_NAME).upload(f"catalogos/{html_filename}", f)
    except Exception as e:
        return {"error": f"Erro ao enviar HTML para o Supabase: {str(e)}"}

    # 6. Retornar link público
    url = f"{SUPABASE_URL}/storage/v1/object/public/catalogos/{html_filename}"
    return {"url": url}
