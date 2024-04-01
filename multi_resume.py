import streamlit as st
import io
import base64
from PIL import Image
import pdf2image
import google.generativeai as genai
import os
import re
import csv

def get_gemini_response(input_text, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-pro-vision')
    if isinstance(pdf_content, list):
        response = model.generate_content([input_text, pdf_content[0], prompt])
    # If pdf_content is already a dictionary:
    elif isinstance(pdf_content, dict):
        response = model.generate_content([input_text, pdf_content, prompt])
    else:
        raise TypeError("pdf_content must be a list or dictionary")
    return response

def input_pdf_setup(uploaded_file):
    pdf_parts = []
    pdf_files = []
    if uploaded_file is not None:
        for file in uploaded_file:
            filename = file.name  # Retrieve filename
            pdf_files.append({"filename": filename})
            images = pdf2image.convert_from_bytes(file.read())
            for img in images:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                pdf_parts.append({
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(img_byte_arr).decode()
                })
        # Return a tuple containing both pdf_parts and pdf_files
        return pdf_parts, pdf_files
    else:
        raise FileNotFoundError("No file uploaded")
st.set_page_config(page_title="Resume Expert")
st.header("JobFit Analyzer")
st.subheader('This Application helps you in your Resume Review with help of GEMINI AI [LLM]')

input_text = st.text_input("Job Description: ", key="input")
uploaded_files = st.file_uploader("Upload your Resumes(PDF)...", type=["pdf"], accept_multiple_files=True)

pdf_contents = []
if uploaded_files is not None:
    st.write("PDFs Uploaded Successfully")

submit = st.button("Analyze Resumes")

input_prompt = """You are an skilled HR. Please review the resume and rate the skills and provide what skills are there. Also, provide a score for the every resume's fit for the job (out of 10).can you also rank the resume"""



if submit:
    if uploaded_files is not None:
        rankings = []
        # Unpack the tuple returned by input_pdf_setup function
        for i, pdf_content in enumerate([input_pdf_setup(uploaded_files[i:i+1]) for i in range(len(uploaded_files))]):
            response = get_gemini_response(input_text, pdf_content[0], input_prompt)
            parsed_response = response.text.split("\n")

            skills = []
            score = None
            for line in parsed_response:
                if line.strip() and not line.startswith("Resume"):
                    match = re.search(r'(\d+\.\d+|\d+)/10', line)
                    if match:
                        score = match.group()
                    else:
                        skills.append(line.strip())

            # Calculate rank based on score
            if score:
    # Extract the numeric part of the score and convert it to a float
                numeric_score = float(score.split('/')[0])
                rankings.append({"filename": pdf_content[1][0]["filename"], "score": numeric_score, "skills": ', '.join(skills)})
            else:
                rankings.append({"filename": pdf_content[1][0]["filename"], "score": 0, "skills": ', '.join(skills)})
                        # Unpack the tuple returned by input_pdf_setup function
            pdf_files = pdf_content[1]
            filename = pdf_files[0]["filename"] if pdf_files else "Unknown"
            st.write(f"Resume {i+1} Filename: {filename}")  # Display PDF filename
            st.write(f"Resume {i+1} Skills: {', '.join(skills)}")
            st.write(f"Score: {score if score else 'Not available'}")
            st.markdown("---")

        # Rank the resumes based on scores
        rankings.sort(key=lambda x: x["score"], reverse=True)

        # Save rankings to CSV file
        with open('resume_rankings.csv', 'w', newline='') as csvfile:
            fieldnames = ['Rank', 'Filename', 'Skills', 'Score']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i, rank in enumerate(rankings):
                writer.writerow({'Rank': i+1, 'Filename': rank["filename"], 'Skills': rank["skills"], 'Score': rank["score"]})

    else:
        st.write("Please upload PDF files to proceed.")

st.caption("Resume Expert - Making Job Applications Easier")
