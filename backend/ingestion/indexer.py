from pathlib import Path

from backend.ingestion.loader import extract_text_from_pdf
from backend.ingestion.cleaner import clean_text
from backend.ingestion.chunker import create_chunks


DOCUMENTS_DIR = Path("documents")


def get_category(pdf_path):
    return pdf_path.parent.name


def prepare_chunks():

    all_chunks = []

    pdf_files = list(DOCUMENTS_DIR.rglob("*.pdf"))

    print("PDF files found:", len(pdf_files))

    for pdf_path in pdf_files:

        print("\nProcessing:")
        print(pdf_path)

        category = get_category(pdf_path)
        document_name = pdf_path.name

        pages = extract_text_from_pdf(pdf_path)

        for page in pages:

            cleaned_text = clean_text(page["text"])

            if not cleaned_text:
                continue

            chunks = create_chunks(cleaned_text)

            for chunk in chunks:

                all_chunks.append({
                    "document_name": document_name,
                    "category": category,
                    "page_number": page["page_number"],
                    "text": chunk
                })

    return all_chunks