
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
async def upload_csv(file: UploadFile = File(...)):
    # Salvar o CSV temporariamente
    contents = await file.read()
    file_id = str(uuid.uuid4())
    original_name = file.filename.replace(".csv", "")
    csv_filename = f"{file_id}_{file.filename}"
    csv_path = f"/tmp/{csv_filename}"
    with open(csv_path, "wb") as f:
        f.write(contents)

    # Carregar CSV
    df = pd.read_csv(csv_path, sep=";", dtype=str).fillna("")

    # Agrupar por categoria mantendo ordem
    df["Categoria_ordem"] = df.groupby("Categoria").ngroup()
    df = df.sort_values(["Categoria_ordem"])

    # Carregar o template
    env = Environment(loader=FileSystemLoader("/opt/render/project/src/template"))
    template = env.get_template("catalogo_com_estoque.html")

    # Renderizar HTML
    categorias = df["Categoria"].unique()
    produtos_por_categoria = {cat: df[df["Categoria"] == cat].to_dict("records") for cat in categorias}
    html = template.render(produtos_por_categoria=produtos_por_categoria)

    # Salvar HTML
    html_filename = f"{file_id}_{original_name}.html"
    html_path = f"/tmp/{html_filename}"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Upload para Supabase
    with open(html_path, "rb") as f:
        supabase.storage.from_(BUCKET_NAME).upload(
            f"catalogos/{html_filename}", f, {"content-type": "text/html"}
        )

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/catalogos/catalogos/{html_filename}"
    return {"url": public_url}
