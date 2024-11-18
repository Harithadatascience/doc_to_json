#trial 3 (extracts only the sections)

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import cv2
import numpy as np
import os
import re

app = FastAPI()

@app.post("/upload_pdf")
async def upload_file(file: UploadFile = File(...)):
    # Load the PDF from the uploaded file
    pdf_document = fitz.open(stream=await file.read(), filetype="pdf")
    
    # Folder to save images
    image_folder = "extracted_images"
    os.makedirs(image_folder, exist_ok=True)

    # Initialize the result structure
    extracted_data = {
        "Exam_Date": "13/09/2024",  # Example date, replace if needed
        "Exam_Time": "12:30 PM - 1:30 PM",  # Example time
        "Subject": "Combined Graduate Level Examination Tier I",  # Example subject
        "Section": []
    }

    # Helper function to extract and save images
    def save_image(image_bytes, page_number, item_type, item_id):
        image_filename = f"{image_folder}/image_page_{page_number + 1}_{item_type}_{item_id}.png"
        with open(image_filename, "wb") as img_file:
            img_file.write(image_bytes)
        return image_filename

    # Define regex patterns for extracting sections, questions, and answers
    section_pattern = re.compile(r"(Section\s*[:\-]?\s*[\w\s]+)")
    question_pattern = re.compile(r"(Q\d+)\.\s*(.*?)\s*(?=(Q\d+\.|Ans|$))", re.DOTALL)
    answer_pattern = re.compile(r"(Ans\d)\.\s*(.*?)\s*(?=Ans\d|$)", re.DOTALL)

    # Loop through each page in the PDF
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        text = page.get_text("text")

        # Extract sections from the text
        section_matches = section_pattern.findall(text)
        
        for section_name in section_matches:
            section_data = {
                "Section_name": section_name.strip(),
                "Total_questions": 25,  # Placeholder: you can extract this from the document if needed
                "Q&A": []
            }

            # Extract questions for the current section
            question_matches = question_pattern.findall(text)
            for q_num, question_text, _ in question_matches:
                question_data = {
                    q_num: [question_text.strip(), f"{image_folder}/image_page_{page_number + 1}_{q_num}.png"],
                    "Ans": [],
                    "Correct_Answer": []
                }

                # Extract answers for the current question
                answer_matches = answer_pattern.findall(text)
                for ans_id, ans_text in answer_matches:
                    # Save answer image (if necessary, can adjust logic here)
                    answer_image = save_image(image_bytes=b"", page_number=page_number, item_type="Answer", item_id=f"{q_num}_{ans_id}")
                    question_data["Ans"].append({ans_id: [ans_text.strip(), answer_image]})

                # Assume the last answer is correct (adjust as needed)
                question_data["Correct_Answer"] = ["Ans4"]  # Example, update with actual logic if available

                # Add question data to section
                section_data["Q&A"].append(question_data)

            # Add the section data to the final structure
            extracted_data["Section"].append(section_data)

    pdf_document.close()

    return JSONResponse(content=extracted_data)
