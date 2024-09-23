
import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt')
nltk.download('stopwords')

import os
import nltk
import PyPDF2
from transformers import pipeline
import streamlit as st
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
import warnings

# Suppress FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)

# Set NLTK data path
nltk.data.path.append(os.path.join(os.path.expanduser("~"), "nltk_data"))

# Ensure NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')




def extract_text_from_pdf(pdf_file):
    """
    Extract text from a PDF file.
    """
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def preprocess_text(text):
    """
    Preprocess the extracted text by removing newlines and extra spaces.
    """
    # Remove newlines and extra spaces
    text = ' '.join(text.split())
    return text


def summarize_text(text, max_length=150, min_length=50):
    """
    Summarize the given text using a pre-trained model.
    """
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    # Split text into chunks if it's too long for the model
    max_chunk_length = 1024
    chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]

    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
        summaries.append(summary[0]['summary_text'])

    return ' '.join(summaries)


def extract_key_takeaways(text, num_takeaways=5):
    """
    Extract key takeaways from the text using a simple TF-IDF like approach.
    """
    # Tokenize the text into sentences and words
    sentences = sent_tokenize(text)
    words = word_tokenize(text.lower())

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]

    # Calculate word frequencies
    word_freq = Counter(words)

    # Calculate sentence scores based on word frequencies
    sentence_scores = {}
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word in word_freq:
                if sentence not in sentence_scores:
                    sentence_scores[sentence] = word_freq[word]
                else:
                    sentence_scores[sentence] += word_freq[word]

    # Get top sentences as key takeaways
    key_takeaways = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_takeaways]

    return key_takeaways


def main():
    st.title("AI/ML Paper Summarizer")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file is not None:
        with st.spinner("Processing the PDF..."):
            # Extract and preprocess text
            raw_text = extract_text_from_pdf(uploaded_file)
            processed_text = preprocess_text(raw_text)

            # Generate summary
            summary = summarize_text(processed_text)

            # Extract key takeaways
            key_takeaways = extract_key_takeaways(processed_text)

        # Display results
        st.subheader("Summary")
        st.write(summary)

        st.subheader("Key Takeaways")
        for i, takeaway in enumerate(key_takeaways, 1):
            st.write(f"{i}. {takeaway}")

        # Option to view full text
        if st.checkbox("Show full text"):
            st.subheader("Full Text")
            st.text_area("", processed_text, height=300)


if __name__ == "__main__":
    main()