import os
from pypdf import PdfReader

def extract_pdf_to_text(pdf_path: str, out_path: str):
    print(f"Extracting {pdf_path}...")
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
        
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved extracted text to {out_path}")

if __name__ == "__main__":
    # Make sure you put the PDF in the root directory
    extract_pdf_to_text("2609.35738v1.pdf", "data/doc_paper.txt")