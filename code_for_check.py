#base format
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import cv2
import numpy as np
import os

app = FastAPI()


@app.post("/upload_pdf")
async def upload_file(file: UploadFile = File(...)):
    # Load the PDF from the uploaded file
    pdf_document = fitz.open(stream=await file.read(), filetype="pdf")
    # Folder to save images
    image_folder = "extracted_images"
    os.makedirs(image_folder, exist_ok=True)

    extracted_data = {"text": [], "images": []}

    # Loop through each page in the PDF
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)

        # Extract text from the page
        text = page.get_text("text")
        extracted_data["text"].append(
            {"page": page_number + 1, "content": text})

        # Extract images from the page
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            image = pdf_document.extract_image(xref)
            image_bytes = image["image"]

            # Save the image
            image_filename = f"{
                image_folder}/image_page_{page_number + 1}_img_{img_index + 1}.png"
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)

            # Optionally, read the image using OpenCV (if further processing is needed)
            image_cv = cv2.imdecode(np.frombuffer(
                image_bytes, np.uint8), cv2.IMREAD_COLOR)

            # Store image path in the response data
            extracted_data["images"].append(
                {"page": page_number + 1, "image_path": image_filename})

    pdf_document.close()

    return JSONResponse(content=extracted_data)


#trial (only the sections)
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import os
import cv2
import numpy as np

app = FastAPI()

# Folder to save images
image_folder = "extracted_images"
os.makedirs(image_folder, exist_ok=True)

@app.post("/upload_pdf")
async def upload_file(file: UploadFile = File(...)):
    # Load the PDF from the uploaded file
    pdf_document = fitz.open(stream=await file.read(), filetype="pdf")
    
    extracted_data = {
        "Exam_Date": "13/09/2024",
        "Exam_Time": "12:30 PM - 1:30 PM",
        "Subject": "Combined Graduate Level Examination Tier I",
        "Section": []
    }
    
    # Loop through each page in the PDF
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)

        # Extract text from the page
        text = page.get_text("text")
        
        # Extract images from the page
        image_list = page.get_images(full=True)
        page_images = []
        for img_index, img in enumerate(image_list):
            xref = img[0]
            image = pdf_document.extract_image(xref)
            image_bytes = image["image"]

            # Save the image
            image_filename = f"{image_folder}/page_{page_number + 1}_img_{img_index + 1}.png"
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)

            # Optionally, read the image using OpenCV (if further processing is needed)
            image_cv = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

            # Store image path
            page_images.append(image_filename)

        # Now, let's process the extracted content based on the format you provided.
        section = {
            "Section_name": "General Intelligence and Reasoning",  # You can dynamically set this from text or metadata
            "Total_questions": 25,  # Based on the number of questions on this page or section
            "Q&A": []
        }

        # Placeholder for questions and answers (this would need to be parsed dynamically based on the PDF structure)
        # For now, a static example based on the format you've provided

        # Example for Q1 with image
        question_data = {
            "Q1": [
                "Select the option that represents the letters  which, when sequentially placed from left to right in the blanks below, will complete the letter series. f h _ h _ g f _ h g _ h _ f f _ g _ h _ f ",
                page_images[0] if page_images else ""  # Attach the image if it exists
            ],
            "Ans": [
                {
                    "Ans1": ["g h f h g f f g ", page_images[1] if len(page_images) > 1 else ""]
                },
                {
                    "Ans2": ["g h f h g h f g ", page_images[2] if len(page_images) > 2 else ""]
                },
                {
                    "Ans3": ["g h f f g h f g ", ""]
                },
                {
                    "Ans4": ["g h f h g h h g", page_images[3] if len(page_images) > 3 else ""]
                }
            ],
            "Correct_Answer": ["Ans4"]
        }

        section["Q&A"].append(question_data)

        # Add the section to the extracted data
        extracted_data["Section"].append(section)

    pdf_document.close()
    
    return JSONResponse(content=extracted_data)



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


#trial (extract some random questions)
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
        "Exam_Date": None,
        "Exam_Time": None,
        "Subject": None,
        "Section": []
    }

    # Helper function to save images
    def save_image(img, page_number, item_type, item_id):
        image_filename = f"{image_folder}/image_page_{page_number + 1}_{item_type}_{item_id}.png"
        cv2.imwrite(image_filename, img)
        return image_filename

    # Function to detect green ticks in images
    def is_green_tick_present(img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Define range for green color in HSV
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([80, 255, 255])
        # Create a mask to isolate green areas
        mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixels = cv2.countNonZero(mask)
        # Return True if green tick is detected (adjust threshold as needed)
        return green_pixels > 50

    # Define regex patterns for extracting Exam details, sections, questions, and answers
    exam_date_pattern = re.compile(r"Exam Date:\s*(\d{2}/\d{2}/\d{4})")
    exam_time_pattern = re.compile(r"Exam Time:\s*([\d:]+ [APM]+ - [\d:]+ [APM]+)")
    subject_pattern = re.compile(r"Subject:\s*([\w\s]+)")
    section_pattern = re.compile(r"Section\s*:\s*([\w\s]+)")
    question_pattern = re.compile(r"(Q\.\d+)\s*(.*?)\s*(?=(Q\.\d+|Ans|$))", re.DOTALL)
    answer_pattern = re.compile(r"(Ans\.\d+)\s*(.*?)\s*(?=Ans\.\d+|$)", re.DOTALL)

    # Loop through each page in the PDF
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        text = page.get_text("text")

        # Extract exam details if not already found
        if not extracted_data["Exam_Date"]:
            date_match = exam_date_pattern.search(text)
            if date_match:
                extracted_data["Exam_Date"] = date_match.group(1)

        if not extracted_data["Exam_Time"]:
            time_match = exam_time_pattern.search(text)
            if time_match:
                extracted_data["Exam_Time"] = time_match.group(1)

        if not extracted_data["Subject"]:
            subject_match = subject_pattern.search(text)
            if subject_match:
                extracted_data["Subject"] = subject_match.group(1)

        # Extract sections from the text
        section_matches = section_pattern.findall(text)
        
        for section_name in section_matches:
            section_data = {
                "Section_name": section_name.strip(),
                "Q&A": []
            }

            # Extract questions for the current section
            question_matches = question_pattern.findall(text)
            for q_num, question_text, _ in question_matches:
                question_data = {
                    "Question": q_num,
                    "Text": question_text.strip(),
                    "Ans": [],
                    "Correct_Answer": []
                }

                # Extract answers for the current question
                answer_matches = answer_pattern.findall(text)
                for ans_id, ans_text in answer_matches:
                    # Find answer images and check for green tick mark
                    answer_image_path = None
                    for image_index, img_info in enumerate(page.get_images(full=True)):
                        xref = img_info[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
                        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        
                        # Save the answer image and check for green tick
                        answer_image_path = save_image(img, page_number, "Answer", f"{q_num}_{ans_id}")
                        if is_green_tick_present(img):
                            question_data["Correct_Answer"].append(ans_id)

                    question_data["Ans"].append({ans_id: [ans_text.strip(), answer_image_path]})

                # Add question data to section
                section_data["Q&A"].append(question_data)

            # Add the section data to the final structure
            extracted_data["Section"].append(section_data)

    pdf_document.close()

    return JSONResponse(content=extracted_data)




