from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import os
import re
import json
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(title="SSC CGL PDF Extractor")

# Set Tesseract command path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Define models
class QuestionAnswer(BaseModel):
    Qno: int
    Q: List[str]
    Ans: List[Dict[str, List[str]]]
    Correct_Answer: List[str]

class Section(BaseModel):
    Section_name: str
    Total_questions: int
    QA: List[QuestionAnswer]

class ExamData(BaseModel):
    Exam_Date: str
    Exam_Time: str
    Subject: str
    Section: List[Section]

class PDFExtractor:
    def __init__(self, poppler_path: Optional[str] = None):
        self.image_base_path = "extracted_images"
        self.poppler_path = poppler_path  # Path to Poppler binaries (optional)
        Path(self.image_base_path).mkdir(parents=True, exist_ok=True)

    def extract_metadata(self, text: str) -> Dict[str, str]:
        metadata = {}
        date_match = re.search(r"Exam Date\s*(\d{2}/\d{2}/\d{4})", text)
        if date_match:
            metadata["Exam_Date"] = date_match.group(1)
        time_match = re.search(r"Exam Time\s*([\d:]+\s*(?:AM|PM)\s*-\s*[\d:]+\s*(?:AM|PM))", text)
        if time_match:
            metadata["Exam_Time"] = time_match.group(1)
        subject_match = re.search(r"Subject\s*(.+?)(?=\n|Section)", text)
        if subject_match:
            metadata["Subject"] = subject_match.group(1).strip()
        return metadata

    def extract_sections(self, text: str) -> List[Dict]:
        sections = []
        section_matches = re.finditer(r"Section\s*:\s*([^\n]+)", text)
        for section_match in section_matches:
            section_name = section_match.group(1).strip()
            sections.append({"Section_name": section_name, "Total_questions": 0, "QA": []})
        return sections

    def process_pdf(self, pdf_path: str) -> Dict:
        try:
            images = convert_from_path(pdf_path, poppler_path=self.poppler_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Poppler error: {e}")
        
        full_text = ""
        for image in images:
            text = pytesseract.image_to_string(np.array(image))
            full_text += text + "\n"
        
        metadata = self.extract_metadata(full_text)
        sections = self.extract_sections(full_text)

        # Ensure that Exam_Time is included in the response
        if "Exam_Time" not in metadata:
            metadata["Exam_Time"] = "Not available"  # Provide a default value if missing

        return {**metadata, "Section": sections}

# Initialize PDF extractor
poppler_path = r"C:\Program Files\poppler\poppler-24.08.0\Library\bin"
pdf_extractor = PDFExtractor(poppler_path=poppler_path)

@app.post("/extract-pdf/", response_model=ExamData)
async def extract_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        result = pdf_extractor.process_pdf(temp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/")
async def root():
    return {"message": "SSC CGL PDF Extractor API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
