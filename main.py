import fitz

from fastapi import FastAPI, File, UploadFile
app = FastAPI()


@app.post("/")
async def upload_file(file: UploadFile = File(...)):
    new_file = fitz.open(file)
    
    return {"content_type": content_type}