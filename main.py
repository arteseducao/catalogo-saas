from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from supabase import create_client, Client
import os, csv, shutil, uuid
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def swagger_ui():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Catálogo SaaS - API")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def gerar_catalogo(csv_path, template_path, html_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        produtos = list(reader)

    with open(template_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    container = soup.find('div', {'id': 'catalogo-container'})
    if not container:
        container = soup.new_tag('div', id='catalogo-container')
        soup.body.append(container)

    for p in produtos:
        card = soup.new_tag('div', attrs={'class': 'produto'})
        nome = soup.new_tag('h3')
        nome.string = p.get('Descrição', 'Produto sem nome')
        card.append(nome)

        preco = soup.new_tag('p')
        preco.string = f"R$ {p.get('Preço', '0,00')}"
        card.append(preco)

        container.append(card)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

@app.post("/upload/")
async def upload_files(file: UploadFile = File(...)):
    temp_csv = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(temp_csv, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    html_output = temp_csv.replace(".csv", ".html")
    template_path = "templates/catalogo_com_estoque.html"
    gerar_catalogo(temp_csv, template_path, html_output)

    with open(html_output, "rb") as f:
        file_key = f"catalogos/{os.path.basename(html_output)}"
        supabase.storage.from_('catalogos').upload(file_key, f, {
            "content-type": "text/html",
            "x-upsert": "true"
        })

    url = f"{SUPABASE_URL.replace('.supabase.co', '.supabase.storage.co')}/storage/v1/object/public/catalogos/{os.path.basename(html_output)}"
    return JSONResponse({"url": url})
