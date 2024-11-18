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
