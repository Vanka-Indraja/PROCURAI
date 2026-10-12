import fitz


def extract_pdf_text(pdf_path):
    document = fitz.open(pdf_path)

    full_text = ""

    for page_number, page in enumerate(document):
        text = page.get_text()

        full_text += f"\n--- PAGE {page_number + 1} ---\n"
        full_text += text

    document.close()

    return full_text