from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import cv2
import numpy as np
import os

app = FastAPI()

# Folder to save images
image_folder = "extracted_images"
os.makedirs(image_folder, exist_ok=True)

@app.post("/upload_pdf")
async def upload_file(file: UploadFile = File(...)):
    # Load the PDF from the uploaded file
    pdf_document = fitz.open(stream=await file.read(), filetype="pdf")
    
    extracted_data = {"text": [], "images": []}
    
    # Loop through each page in the PDF
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)

        # Extract text from the page
        text = page.get_text("text")
        extracted_data["text"].append({"page": page_number + 1, "content": text})

        # Extract images from the page
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            image = pdf_document.extract_image(xref)
            image_bytes = image["image"]

            # Save the image
            image_filename = f"{image_folder}/image_page_{page_number + 1}_img_{img_index + 1}.png"
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)

            # Optionally, read the image using OpenCV (if further processing is needed)
            image_cv = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

            # Store image path in the response data
            extracted_data["images"].append({"page": page_number + 1, "image_path": image_filename})

    pdf_document.close()
    
    return JSONResponse(content=extracted_data)
