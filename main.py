
import os
import uuid
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client
from fastapi.responses import JSONResponse

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        extension = file.filename.split(".")[-1]
        content_type = "text/html" if extension == "html" else "text/csv"
        unique_id = str(uuid.uuid4())
        supabase_file_name = f"{unique_id}_{file.filename}"

        supabase.storage.from_("catalogos").upload(
            supabase_file_name, file_content, file_options={"content-type": content_type}
        )

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/catalogos/{supabase_file_name}"

        return JSONResponse(content={"url": public_url})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
