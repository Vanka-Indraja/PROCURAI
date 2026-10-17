import os
import re
import shutil

import pymupdf
import pytesseract

from PIL import Image


# =========================================================
# SETTINGS
# =========================================================

MIN_MEANINGFUL_TEXT_LENGTH = 50

MIN_PAGE_TEXT_LENGTH = 20

OCR_DPI = 300

OCR_LANGUAGE = "eng"


# =========================================================
# TESSERACT CONFIGURATION
# =========================================================

WINDOWS_TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def configure_tesseract():

    # First preference:
    # normal system PATH

    system_tesseract = shutil.which(
        "tesseract"
    )

    if system_tesseract:

        pytesseract.pytesseract.tesseract_cmd = (
            system_tesseract
        )

        return system_tesseract


    # Windows fallback

    if os.path.exists(
        WINDOWS_TESSERACT_PATH
    ):

        pytesseract.pytesseract.tesseract_cmd = (
            WINDOWS_TESSERACT_PATH
        )

        return WINDOWS_TESSERACT_PATH


    raise RuntimeError(
        "Tesseract OCR was not found. "
        "Install Tesseract or add it to PATH."
    )


# =========================================================
# REMOVE INTERNAL PAGE MARKERS
# =========================================================

def remove_page_markers(text):

    if not text:
        return ""

    cleaned = re.sub(
        r"---\s*PAGE\s+\d+\s*---",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    return cleaned


# =========================================================
# NORMALIZE MEANINGFUL TEXT
# =========================================================

def get_meaningful_text(text):

    if not text:
        return ""

    cleaned = remove_page_markers(
        text
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    )

    return cleaned.strip()


# =========================================================
# COUNT MEANINGFUL CHARACTERS
# =========================================================

def count_meaningful_characters(
    extracted_text,
):

    return len(
        get_meaningful_text(
            extracted_text
        )
    )


# =========================================================
# CHECK WHETHER DOCUMENT NEEDS OCR
# =========================================================

def requires_ocr(
    extracted_text,
    minimum_length=MIN_MEANINGFUL_TEXT_LENGTH,
):

    return (
        count_meaningful_characters(
            extracted_text
        )
        <
        minimum_length
    )


# =========================================================
# NORMAL PDF TEXT EXTRACTION
# =========================================================

def extract_pdf_text(
    pdf_path,
):

    document = pymupdf.open(
        pdf_path
    )

    full_text = ""

    try:

        for page_number, page in enumerate(
            document,
            start=1,
        ):

            page_text = (
                page.get_text(
                    "text"
                )
                or ""
            )

            full_text += (
                f"\n--- PAGE {page_number} ---\n"
            )

            full_text += (
                page_text
            )

    finally:

        document.close()


    return full_text


# =========================================================
# CONVERT PDF PAGE TO PIL IMAGE
# =========================================================

def render_page_to_image(
    page,
):

    zoom = (
        OCR_DPI
        /
        72
    )

    matrix = pymupdf.Matrix(
        zoom,
        zoom,
    )

    pixmap = page.get_pixmap(
        matrix=matrix,
        alpha=False,
    )

    image = Image.frombytes(
        "RGB",
        (
            pixmap.width,
            pixmap.height,
        ),
        pixmap.samples,
    )

    return image


# =========================================================
# OCR ONE PDF PAGE
# =========================================================

def ocr_page(
    page,
):

    configure_tesseract()

    image = render_page_to_image(
        page
    )

    try:

        text = (
            pytesseract.image_to_string(
                image,
                lang=OCR_LANGUAGE,
                config="--oem 3 --psm 3",
            )
            or ""
        )

    finally:

        image.close()


    return text


# =========================================================
# SMART PDF EXTRACTION
#
# NORMAL PAGE:
#   PyMuPDF text extraction
#
# SCANNED PAGE:
#   Tesseract OCR
# =========================================================

def extract_pdf_text_with_ocr(
    pdf_path,
):

    document = pymupdf.open(
        pdf_path
    )

    full_text = ""

    ocr_used = False

    ocr_pages = []

    native_text_pages = []


    try:

        for page_number, page in enumerate(
            document,
            start=1,
        ):

            native_text = (
                page.get_text(
                    "text"
                )
                or ""
            )

            meaningful_native_text = (
                get_meaningful_text(
                    native_text
                )
            )


            # =============================================
            # NORMAL SELECTABLE TEXT PAGE
            # =============================================

            if (
                len(
                    meaningful_native_text
                )
                >=
                MIN_PAGE_TEXT_LENGTH
            ):

                page_text = (
                    native_text
                )

                native_text_pages.append(
                    page_number
                )


            # =============================================
            # SCANNED / IMAGE PAGE
            # =============================================

            else:

                page_text = (
                    ocr_page(
                        page
                    )
                )

                ocr_used = True

                ocr_pages.append(
                    page_number
                )


            full_text += (
                f"\n--- PAGE {page_number} ---\n"
            )

            full_text += (
                page_text
            )


    finally:

        document.close()


    extraction_info = {

        "ocr_used": (
            ocr_used
        ),

        "ocr_pages": (
            ocr_pages
        ),

        "native_text_pages": (
            native_text_pages
        ),

        "total_pages": (
            len(
                ocr_pages
            )
            +
            len(
                native_text_pages
            )
        ),
    }


    return (
        full_text,
        extraction_info,
    )