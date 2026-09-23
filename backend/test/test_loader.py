from pathlib import Path
from backend.ingestion.loader import extract_text_from_pdf
pdf_path = Path("documents/crop_guides/ICAR En-Kharif Agro-Advisories for Farmers 2025.pdf")
pages = extract_text_from_pdf(pdf_path)

print("Total pages:", len(pages))

for page in pages[:3]:
    print("\n--- Page", page["page_number"], "---")
    print(page["text"][:1000])