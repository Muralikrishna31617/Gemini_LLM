import streamlit as st
import os
import json
import subprocess
import sys

# Ensure fuzzywuzzy is installed
try:
    from fuzzywuzzy import fuzz
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fuzzywuzzy"])
    from fuzzywuzzy import fuzz

# Ensure black is installed
try:
    from black import format_str, FileMode
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "black"])
    from black import format_str, FileMode

import google.generativeai as genai

# Configure Genai Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load JSON dataset
with open('coding_questions.json') as f:
    coding_data = json.load(f)

def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt, question])
    return response.text

def find_answer_in_json(question):
    highest_similarity = 0
    best_match = None
    for entry in coding_data:
        similarity = fuzz.ratio(question.lower().strip(), entry["question"].lower().strip())
        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = entry
    if highest_similarity > 70:  # Set a threshold for similarity
        return format_answer(best_match["answer"])
    return None

def format_code_in_chunks(code, max_lines=200):
    """Split code into chunks and format each chunk separately."""
    lines = code.split('\n')
    chunks = [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)]
    formatted_chunks = []
    for chunk in chunks:
        chunk_code = "\n".join(chunk)
        try:
            # Attempt to format each chunk using black
            formatted_chunk = format_str(chunk_code, mode=FileMode())
        except Exception as e:
            # If black formatting fails, try a manual indentation fix
            formatted_chunk = "\n".join("    " + line if line.strip() else line for line in chunk_code.split('\n'))
            st.warning(f"Black formatting error in chunk: {e}")
        formatted_chunks.append(formatted_chunk)
    return "\n".join(formatted_chunks)

def format_answer(answer_dict):
    formatted_answer = ""
    for language, code in answer_dict.items():
        if language.lower() == "python":
            formatted_code = format_code_in_chunks(code)
        else:
            formatted_code = code  # Add other formatting tools if necessary
        formatted_answer += f"```{language.lower()}\n{formatted_code}\n```\n"
    return formatted_answer if formatted_answer else "No solution available for this question."
# Streamlit App
st.set_page_config(page_title="Coding Question Assistant")
st.header("Gemini App for Coding Questions")

question = st.text_input("Input your coding question: ", key="input")
submit = st.button("Ask the question")

if submit:
    response = find_answer_in_json(question)
    if response:
        st.subheader("The Response is")
        st.markdown(response)
    else:
        st.subheader("No matching question found in the dataset. Generating response using Gemini...")
        gemini_response = get_gemini_response(question, "Provide a detailed code solution in Bash for the following question:")
        # Beautify the Bash response
        formatted_gemini_response = "\n".join([line.strip() for line in gemini_response.split('\n') if line.strip()])
        st.markdown(f"```bash\n{formatted_gemini_response}\n```")
