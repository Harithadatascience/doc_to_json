from fastapi import FastAPI, File, UploadFile
app = FastAPI()


@app.post("/")
async def upload_file(file: UploadFile = File(...)):
    content_type = file.content_type
    return {"content_type": content_type}
