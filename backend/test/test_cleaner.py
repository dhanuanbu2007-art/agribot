from pathlib import Path

from backend.ingestion.loader import extract_text_from_pdf
from backend.ingestion.cleaner import clean_text


pdf_path = Path(
    "documents/crop_guides/ICAR En-Kharif Agro-Advisories for Farmers 2025.pdf"
)

pages = extract_text_from_pdf(pdf_path)

for page in pages[:3]:
    cleaned = clean_text(page["text"])

    print("\n--- Cleaned Page", page["page_number"], "---")
    print(cleaned[:1000])