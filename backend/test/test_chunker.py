from pathlib import Path

from backend.ingestion.loader import extract_text_from_pdf
from backend.ingestion.cleaner import clean_text
from backend.ingestion.chunker import create_chunks


pdf_path = Path(
    "documents/crop_guides/ICAR En-Kharif Agro-Advisories for Farmers 2025.pdf"
)

pages = extract_text_from_pdf(pdf_path)

all_chunks = []

for page in pages:
    cleaned_text = clean_text(page["text"])

    if cleaned_text:
        chunks = create_chunks(cleaned_text)

        for chunk in chunks:
            all_chunks.append({
                "page_number": page["page_number"],
                "text": chunk
            })

print("Total chunks:", len(all_chunks))

for i, chunk in enumerate(all_chunks[100:105], start=101):
    print(f"\n--- Chunk {i} | Page {chunk['page_number']} ---")
    print(chunk["text"])