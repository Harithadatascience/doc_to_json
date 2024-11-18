from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import cv2
import numpy as np
import os
from typing import List, Dict, Any
import json
import re
from datetime import datetime

app = FastAPI()

class PDFExtractor:
    def __init__(self):
        self.question_image_dir = "extracted_images_questions"
        self.option_image_dir = "extracted_images_options"
        self.ensure_directories()             
        
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.question_image_dir, exist_ok=True)
        os.makedirs(self.option_image_dir, exist_ok=True)
    
    def extract_metadata(self, page_text: str) -> Dict[str, str]:
        """Extract exam metadata from the PDF page"""
        metadata = {}
        
        # Extract exam date
        date_match = re.search(r'Exam Date[:\s]+(\d{2}/\d{2}/\d{4})', page_text)
        if date_match:
            metadata["Exam Date"] = date_match.group(1)
            
        # Extract exam time
        time_match = re.search(r'Exam Time[:\s]+([\d:]+\s*(?:AM|PM)\s*-\s*[\d:]+\s*(?:AM|PM))', page_text)
        if time_match:
            metadata["Exam Time"] = time_match.group(1)
            
        # Extract subject
        subject_match = re.search(r'Subject[:\s]+(.*?)(?:\n|$)', page_text)
        if subject_match:
            metadata["Subject"] = subject_match.group(1).strip()
            
        return metadata

    def detect_green_tick(self, image_data: bytes) -> bool:
        """Detect if an image contains a green tick mark"""
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define green color range
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([80, 255, 255])
        
        # Create mask for green color
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Calculate percentage of green pixels
        green_pixels = cv2.countNonZero(mask)
        total_pixels = img.shape[0] * img.shape[1]
        green_percentage = (green_pixels / total_pixels) * 100
        
        return green_percentage > 5  # Threshold for detecting green tick

    def save_image(self, image_data: bytes, section_name: str, q_number: int, 
                  image_type: str, option_number: int = None) -> str:
        """Save extracted image and return its path"""
        base_dir = self.question_image_dir if image_type == 'question' else self.option_image_dir
        
        if image_type == 'question':
            filename = f"page_{section_name}_Q{q_number}.png"
        else:
            filename = f"page_{section_name}_Q{q_number}_Ans{option_number}.png"
            
        file_path = os.path.join(base_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(image_data)
            
        return file_path

    def extract_questions(self, page: fitz.Page, section_name: str) -> List[Dict]:
        """Extract questions, options and correct answers from a page"""
        questions = []
        current_question = None
        
        # Get text blocks from the page
        blocks = page.get_text("blocks")
        
        for block in blocks:
            text = block[4]
            
            # Detect question
            q_match = re.match(r'Q\.(\d+)', text)
            if q_match:
                if current_question:
                    questions.append(current_question)
                    
                current_question = {
                    "Qno": int(q_match.group(1)),
                    "Q": [],
                    "Ans": [],
                    "Correct_Answer": None
                }
                
                # Extract question text/image
                question_content = text[q_match.end():].strip()
                if question_content:
                    current_question["Q"].append(question_content)
                
                # Check for question images
                rect = fitz.Rect(block[0], block[1], block[2], block[3])
                images = page.get_images(full=True)
                
                if images:
                    for img in images:
                        xref = img[0]
                        image_data = page.parent.extract_image(xref)["image"]
                        image_path = self.save_image(
                            image_data, 
                            section_name, 
                            current_question["Qno"], 
                            'question'
                        )
                        current_question["Q"].append(image_path)
            
            # Detect options
            ans_match = re.search(r'(?:^|\n)(\d)\.\s*(.*?)(?=\n|$)', text)
            if ans_match and current_question:
                option_num = int(ans_match.group(1))
                option_text = ans_match.group(2).strip()
                
                option = {
                    f"Ans{option_num}": [option_text]
                }
                
                # Check for option images
                rect = fitz.Rect(block[0], block[1], block[2], block[3])
                images = page.get_images(full = True)
                
                if images:
                    for img in images:
                        xref = img[0]
                        image_data = page.parent.extract_image(xref)["image"]
                        
                        # Detect if this option is correct (has green tick)
                        if self.detect_green_tick(image_data):
                            current_question["Correct_Answer"] = [f"Ans{option_num}"]
                            
                        image_path = self.save_image(
                            image_data,
                            section_name,
                            current_question["Qno"],
                            'option',
                            option_num
                        )
                        option[f"Ans{option_num}"].append(image_path)
                
                current_question["Ans"].append(option)
        
        if current_question:
            questions.append(current_question)
            
        return questions

    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process the complete PDF and return structured data"""
        doc = fitz.open(pdf_path)
        result = {}
        
        # Extract metadata from first page
        first_page = doc[0]
        metadata = self.extract_metadata(first_page.get_text())
        result.update(metadata)
        
        # Initialize sections
        result["Section"] = []
        current_section = None
        
        for page in doc:
            text = page.get_text()
            
            # Detect section
            section_match = re.search(r'Section\s*:\s*(.*?)(?:\n|$)', text)
            if section_match:
                if current_section:
                    result["Section"].append(current_section)
                    
                section_name = section_match.group(1).strip()
                current_section = {
                    "Section_name": section_name,
                    "Total_questions": 0,
                    "Q&A": []
                }
                
                # Extract questions for this section
                questions = self.extract_questions(page, section_name)
                current_section["Q&A"].extend(questions)
                current_section["Total_questions"] = len(questions)
        
        if current_section:
            result["Section"].append(current_section)
            
        doc.close()
        return result

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process PDF
        extractor = PDFExtractor()
        result = extractor.process_pdf(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
