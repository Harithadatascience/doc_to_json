from fastapi import FastAPI, File, UploadFile
import fitz  # PyMuPDF for PDF parsing
import os

# Initialize FastAPI app
app = FastAPI()

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Save the uploaded PDF file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    # Initialize variables for extracted details
    exam_date = ""
    exam_time = ""
    subject = ""
    section = []

    # Open the PDF document
    pdf_document = fitz.open(temp_file_path)

    # Traverse all pages to find the required details
    for page in pdf_document:
        blocks = page.get_text("blocks")  # Extract blocks of text from the page

        for block in blocks:
            block_text = block[4]  # Extract the actual text from the block
            block_text = block_text.replace("\n", " ").strip()  # Remove newlines and extra spaces

            # Debugging: Print block content
            print(f"Block Text: {block_text}")

            # Check for Exam Date, Exam Time, and Subject in the same block
            if "Exam Date" in block_text:
                # Extract Exam Date, Exam Time, and Subject from the block
                if not exam_date:
                    exam_date = block_text.split("Exam Date")[-1].split("Exam Time")[0].strip()
                if "Exam Time" in block_text and not exam_time:
                    exam_time = block_text.split("Exam Time")[-1].split("Subject")[0].strip()
                if "Subject" in block_text and not subject:
                    subject = block_text.split("Subject")[-1].strip()

            # Stop further processing if all required fields are found
            if exam_date and exam_time and subject:
                break
        # Break out of the loop once data is found
        if exam_date and exam_time and subject:
            break

    # Close the PDF document
    pdf_document.close()

    # Remove the temporary file
    os.remove(temp_file_path)

    # Construct the JSON response in the desired format
    result = {
        "Exam Date": exam_date,
        "Exam Time": exam_time,
        "Subject": subject,
        "Section": section  # Assuming the section list is empty as per your requirement
    }

    # Return the result
    return result


#extracts section name

from fastapi import FastAPI, File, UploadFile
import fitz  # PyMuPDF for PDF parsing
import os

# Initialize FastAPI app
app = FastAPI()

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Save the uploaded PDF file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    # Initialize variables for extracted details
    exam_date = ""
    exam_time = ""
    subject = ""
    sections = []  # List to store section information

    # Open the PDF document
    pdf_document = fitz.open(temp_file_path)

    # Traverse all pages to find the required details
    for page in pdf_document:
        blocks = page.get_text("blocks")  # Extract blocks of text from the page

        for block in blocks:
            block_text = block[4]  # Extract the actual text from the block
            block_text = block_text.replace("\n", " ").strip()  # Remove newlines and extra spaces

            # Debugging: Print block content
            print(f"Block Text: {block_text}")

            # PART 1: Extract Exam Date, Exam Time, and Subject
            if "Exam Date" in block_text and not exam_date:
                # Extract Exam Date, Exam Time, and Subject from the block
                exam_date = block_text.split("Exam Date")[-1].split("Exam Time")[0].strip()
            if "Exam Time" in block_text and not exam_time:
                exam_time = block_text.split("Exam Time")[-1].split("Subject")[0].strip()
            if "Subject" in block_text and not subject:
                subject = block_text.split("Subject")[-1].strip()

            # PART 2: Extract Section Names
            if "Section" in block_text:  # Check if "Section" is in the block
                # Extract the text after "Section" and treat it as the section name
                section_name = block_text.split("Section", 1)[-1].strip()
                if section_name:
                    # Add the extracted section name to the sections list
                    sections.append({
                        "Section_name": section_name,
                        "Total_questions": None,
                        "Q&A": []
                    })

    # Close the PDF document
    pdf_document.close()

    # Remove the temporary file
    os.remove(temp_file_path)

    # Construct the JSON response in the desired format
    result = {
        "Exam Date": exam_date,
        "Exam Time": exam_time,
        "Subject": subject,
        "Sections": sections  # Renamed key to "Sections" to indicate a list
    }

    return result

#extract upto total questions
from fastapi import FastAPI, File, UploadFile
import fitz  # PyMuPDF for PDF parsing
import os
import re  # Regular expressions for detecting questions

# Initialize FastAPI app
app = FastAPI()

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Save the uploaded PDF file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    # Initialize variables for extracted details
    exam_date = ""
    exam_time = ""
    subject = ""
    sections = {}  # Dictionary to store sections by name and their details
    current_section = None  # Variable to track which section we're in

    # Open the PDF document
    pdf_document = fitz.open(temp_file_path)

    # Traverse all pages to find the required details
    for page in pdf_document:
        blocks = page.get_text("blocks")  # Extract blocks of text from the page

        for block in blocks:
            block_text = block[4]  # Extract the actual text from the block
            block_text = block_text.replace("\n", " ").strip()  # Remove newlines and extra spaces

            # PART 1: Extract Exam Date, Exam Time, and Subject
            if "Exam Date" in block_text and not exam_date:
                exam_date = block_text.split("Exam Date")[-1].split("Exam Time")[0].strip()
            if "Exam Time" in block_text and not exam_time:
                exam_time = block_text.split("Exam Time")[-1].split("Subject")[0].strip()
            if "Subject" in block_text and not subject:
                subject = block_text.split("Subject")[-1].strip()

            # PART 2: Extract Section Names and Initialize them in the dictionary
            section_match = re.match(r"(?i)\s*Section[:\s]+(.+)", block_text)
            if section_match:
                section_name = section_match.group(1).strip()
                if section_name and section_name not in sections:
                    # Set Total_questions to 25 directly
                    sections[section_name] = {
                        "Section_name": section_name,
                        "Total_questions": 25,  # Fixed count
                        "Q&A": []
                    }
                current_section = section_name

    # Close the PDF document
    pdf_document.close()

    # Remove the temporary file
    os.remove(temp_file_path)

    # Construct the JSON response in the desired format
    result = {
        "Exam Date": exam_date,
        "Exam Time": exam_time,
        "Subject": subject,
        "Sections": list(sections.values())  # Convert dictionary values to list for response
    }

    return result

#improperly extract the questions

from fastapi import FastAPI, File, UploadFile
import fitz  # PyMuPDF for PDF parsing
import os
import re  # Regular expressions for detecting questions

# Initialize FastAPI app
app = FastAPI()

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Save the uploaded PDF file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    # Initialize variables for extracted details
    exam_date = ""
    exam_time = ""
    subject = ""
    sections = {}  # Dictionary to store sections by name and their details
    current_section = None  # Variable to track which section we're in

    # Open the PDF document
    pdf_document = fitz.open(temp_file_path)

    # Traverse all pages to find the required details
    for page in pdf_document:
        blocks = page.get_text("blocks")  # Extract blocks of text from the page

        for block in blocks:
            block_text = block[4]  # Extract the actual text from the block
            block_text = block_text.replace("\n", " ").strip()  # Remove newlines and extra spaces

            # PART 1: Extract Exam Date, Exam Time, and Subject
            if "Exam Date" in block_text and not exam_date:
                exam_date = block_text.split("Exam Date")[-1].split("Exam Time")[0].strip()
            if "Exam Time" in block_text and not exam_time:
                exam_time = block_text.split("Exam Time")[-1].split("Subject")[0].strip()
            if "Subject" in block_text and not subject:
                subject = block_text.split("Subject")[-1].strip()

            # PART 2: Extract Section Names and Initialize them in the dictionary
            section_match = re.match(r"(?i)\s*Section[:\s]+(.+)", block_text)
            if section_match:
                section_name = section_match.group(1).strip()
                if section_name and section_name not in sections:
                    sections[section_name] = {
                        "Section_name": section_name,
                        "Total_questions": 25,  # Fixed count
                        "Q&A": []
                    }
                current_section = section_name

            # PART 3: Extract Question Numbers (Qno) and Questions (Q)
            # Regex to detect question numbers like Q.1, Q.2, etc.
            question_match = re.match(r"^Q\.(\d+)\s*(.+)", block_text)
            if question_match and current_section:
                question_number = question_match.group(1)  # Extract Qno
                question_text = question_match.group(2).strip()  # Extract question

                # Add the extracted question to the current section's Q&A
                sections[current_section]["Q&A"].append({
                    "Qno": int(question_number),
                    "Q": [question_text],  # Add the question text
                    "Ans": [],  # Ans array is empty as per your request
                    "Correct_Answer": []  # Correct_Answer array remains empty for now
                })

    # Close the PDF document
    pdf_document.close()

    # Remove the temporary file
    os.remove(temp_file_path)

    # Construct the JSON response in the desired format
    result = {
        "Exam Date": exam_date,
        "Exam Time": exam_time,
        "Subject": subject,
        "Sections": list(sections.values())  # Convert dictionary values to list for response
    }

    return result


#improperly shuffle the questions

from fastapi import FastAPI, File, UploadFile
import fitz  # PyMuPDF for PDF parsing
import os
import re  # Regular expressions for detecting questions

# Initialize FastAPI app
app = FastAPI()

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Save the uploaded PDF file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    # Initialize variables for extracted details
    exam_date = ""
    exam_time = ""
    subject = ""
    sections = {}  # Dictionary to store sections by name and their details
    current_section = None  # Variable to track which section we're in

    # Folder for extracted images
    extracted_images_folder = "extracted_questions_images"
    os.makedirs(extracted_images_folder, exist_ok=True)

    # Open the PDF document
    pdf_document = fitz.open(temp_file_path)

    # Traverse all pages to find the required details
    for page in pdf_document:
        blocks = page.get_text("blocks")  # Extract blocks of text from the page

        for block in blocks:
            block_text = block[4]  # Extract the actual text from the block
            block_text = block_text.replace("\n", " ").strip()  # Remove newlines and extra spaces

            # PART 1: Extract Exam Date, Exam Time, and Subject
            if "Exam Date" in block_text and not exam_date:
                exam_date = block_text.split("Exam Date")[-1].split("Exam Time")[0].strip()
            if "Exam Time" in block_text and not exam_time:
                exam_time = block_text.split("Exam Time")[-1].split("Subject")[0].strip()
            if "Subject" in block_text and not subject:
                subject = block_text.split("Subject")[-1].strip()

            # PART 2: Extract Section Names and Initialize them in the dictionary
            section_match = re.match(r"(?i)\s*Section[:\s]+(.+)", block_text)
            if section_match:
                section_name = section_match.group(1).strip()
                if section_name and section_name not in sections:
                    sections[section_name] = {
                        "Section_name": section_name,
                        "Total_questions": 25,  # Fixed count
                        "Q&A": []
                    }
                current_section = section_name

        # PART 3: Extract Questions and Images
        if current_section:
            for block in blocks:
                block_text = block[4].replace("\n", " ").strip()
                # Match question pattern
                question_match = re.match(r"(Q\.\d+)", block_text)
                if question_match:
                    question_no = int(re.findall(r"\d+", question_match.group(1))[0])
                    question_data = {
                        "Qno": question_no,
                        "Q": [],
                        "Ans": [],
                        "Correct_Answer": []
                    }

                    # Check if block contains an image
                    for image_index, img in enumerate(page.get_images(full=True)):
                        xref = img[0]
                        pix = fitz.Pixmap(pdf_document, xref)
                        if pix.n - pix.alpha < 4:  # This is RGB or grayscale
                            pix.save(f"{extracted_images_folder}/page{page.number + 1}_Q{question_no}.png")
                            question_data["Q"].append(f"images/page{page.number + 1}_Q{question_no}.png")
                        pix = None  # Free memory

                    # If it's text, add directly
                    if block_text:
                        question_data["Q"].append(block_text)

                    # Append to current section's Q&A
                    sections[current_section]["Q&A"].append(question_data)

    # Close the PDF document
    pdf_document.close()

    # Remove the temporary file
    os.remove(temp_file_path)

    # Construct the JSON response in the desired format
    result = {
        "Exam Date": exam_date,
        "Exam Time": exam_time,
        "Subject": subject,
        "Section": list(sections.values())
    }

    return result
