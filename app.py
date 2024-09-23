import nltk
import ssl
import os
import PyPDF2
from transformers import pipeline
import streamlit as st
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
import warnings

# Suppress FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)

# Handle SSL issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Set NLTK data path
nltk_data_path = os.path.join(os.getcwd(), "nltk_data")
if not os.path.exists(nltk_data_path):
    os.makedirs(nltk_data_path)

# Ensure NLTK data is downloaded
nltk.data.path.append(nltk_data_path)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', download_dir=nltk_data_path)
    nltk.download('stopwords', download_dir=nltk_data_path)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to preprocess text
def preprocess_text(text):
    text = ' '.join(text.split())
    return text

# Function to summarize text
def summarize_text(text, max_length=150, min_length=50):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    max_chunk_length = 1024
    chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    return ' '.join(summaries)

# Function to extract key takeaways
def extract_key_takeaways(text, num_takeaways=5):
    sentences = sent_tokenize(text)
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]
    word_freq = Counter(words)
    sentence_scores = {}
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word in word_freq:
                if sentence not in sentence_scores:
                    sentence_scores[sentence] = word_freq[word]
                else:
                    sentence_scores[sentence] += word_freq[word]
    key_takeaways = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_takeaways]
    return key_takeaways

# Main function to run the app
def main():
    st.title("AI/ML Paper Summarizer")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file is not None:
        with st.spinner("Processing the PDF..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            processed_text = preprocess_text(raw_text)
            summary = summarize_text(processed_text)
            key_takeaways = extract_key_takeaways(processed_text)

        st.subheader("Summary")
        st.write(summary)

        st.subheader("Key Takeaways")
        for i, takeaway in enumerate(key_takeaways, 1):
            st.write(f"{i}. {takeaway}")

        if st.checkbox("Show full text"):
            st.subheader("Full Text")
            st.text_area("", processed_text, height=300)

if __name__ == "__main__":
    main()
