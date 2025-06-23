import uuid
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os

app = FastAPI()

# Permitir CORS para facilitar testes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis de ambiente (substitua pelos valores reais ou configure no Render)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    # Gere um nome único para o arquivo
    supabase_file_name = f"{uuid.uuid4()}_{file.filename}"
    path_in_bucket = f"catalogos/{supabase_file_name}"

    # Upload do conteúdo
    supabase.storage.from_("catalogos").upload(
        path=path_in_bucket,
        file=contents,
        file_options={"content-type": "text/html"}
    )

    # URL corrigida com subpasta 'catalogos/'
    public_url = f"https://{SUPABASE_URL}/storage/v1/object/public/catalogos/catalogos/{supabase_file_name}"
    return {"url": public_url}