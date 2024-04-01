import streamlit as st
import io
import base64
from PIL import Image
import pdf2image
import google.generativeai as genai
import os
import re
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_text, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response

def input_pdf_setup(uploaded_file):
    pdf_parts = []
    pdf_files = []
    if uploaded_file is not None:
        for file in uploaded_file:
            pdf_files.append({"filename": file.name})
            # Convert PDF to image
            images = pdf2image.convert_from_bytes(file.read())
            # Take the first page for simplicity, or loop through images for all pages
            first_page = images[0]

            # Convert to bytes
            img_byte_arr = io.BytesIO()
            first_page.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

            pdf_parts.append({
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()  # encode to base64
            })
        return pdf_parts, pdf_files
    else:
        raise FileNotFoundError("No file uploaded")

## Streamlit App

st.set_page_config(page_title="Resume Expert")

st.header("JobFit Analyzer")
st.subheader('This Application helps you in your Resume Review with help of GEMINI AI [LLM]')
input_text = st.text_input("Job Description: ", key="input")

uploaded_files = st.file_uploader("Upload your Resumes(PDF)...", type=["pdf"], accept_multiple_files=True)

pdf_contents = []

if uploaded_files is not None:
    st.write("PDFs Uploaded Successfully")

submit = st.button("Analyze Resumes")

input_prompt = """
You are an skilled HR. Please review the resume and rate the skills and provide what skills are there. Also, provide a score for the every resume's fit for the job (out of 10).
can you also rank the resume"""

            
if submit:
    if uploaded_files is not None:
        pdf_contents = [input_pdf_setup(uploaded_files[i:i+1]) for i in range(len(uploaded_files))]
        
        st.subheader("Analysis Results:")
        for i, pdf_content in enumerate(pdf_contents):
            response = get_gemini_response(input_text, pdf_content, input_prompt)
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
            
            st.write(pdf_files)
            st.write(f"Resume {i+1} Skills: {', '.join(skills)}")

            st.write(f"Score: {score if score else 'Not available'}")
            st.markdown("---")
            # skills = []
            # score = None
            # for line in parsed_response:
            #     if line.strip() and not line.startswith("Resume") and "Score:" not in line:
            #         skills.append(line.strip())
            #     elif "Score:" in line:
            #         score = line.split(":")[1].strip()
            
            # st.write(f"Resume {i+1} Skills: {', '.join(skills)}")
            # st.write(f"Score: {score}")
            # st.markdown("---")
            # next_resume = f"Resume {i+2}"
            
    else:
        st.write("Please upload PDF files to proceed.")

st.caption("Resume Expert - Making Job Applications Easier")