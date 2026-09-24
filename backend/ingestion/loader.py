import pymupdf


def extract_text_from_pdf(pdf_path):
    """
    Extract text from every page of a PDF.

    Returns:
        list of dictionaries containing:
        - page_number
        - text
    """

    pages = []

    with pymupdf.open(pdf_path) as document:

        for page_number, page in enumerate(document, start=1):

            text = page.get_text(
                "text",
                sort=True
            )

            pages.append({
                "page_number": page_number,
                "text": text
            })

    return pages