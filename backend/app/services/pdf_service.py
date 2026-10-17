import math
import os
import re
import shutil
from collections import Counter

import pymupdf
import pytesseract
from PIL import Image, ImageFilter, ImageOps
from pytesseract import Output


# =========================================================
# OCR / PDF SETTINGS
# =========================================================

MIN_MEANINGFUL_TEXT_LENGTH = 50
MIN_PAGE_TEXT_LENGTH = 20
OCR_DPI = 300
OCR_LANGUAGE = "eng"
LOW_OCR_CONFIDENCE_THRESHOLD = 60.0
MAX_PDF_PAGES = 60
MAX_OCR_PAGES = 25

WINDOWS_TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# =========================================================
# CUSTOM ERRORS
# =========================================================

class PDFProcessingError(RuntimeError):
    pass


class PDFPageLimitError(PDFProcessingError):
    pass


class OCRPageLimitError(PDFProcessingError):
    pass


class OCRUnavailableError(PDFProcessingError):
    pass


# =========================================================
# TESSERACT CONFIGURATION
# =========================================================

def configure_tesseract():
    system_tesseract = shutil.which("tesseract")

    if system_tesseract:
        pytesseract.pytesseract.tesseract_cmd = system_tesseract
        return system_tesseract

    if os.path.exists(WINDOWS_TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = (
            WINDOWS_TESSERACT_PATH
        )
        return WINDOWS_TESSERACT_PATH

    raise OCRUnavailableError(
        "Tesseract OCR was not found. Install Tesseract "
        "or add it to PATH."
    )


# =========================================================
# TEXT HELPERS
# =========================================================

def remove_page_markers(text):
    if not text:
        return ""

    return re.sub(
        r"---\s*PAGE\s+\d+\s*---",
        " ",
        text,
        flags=re.IGNORECASE,
    )


def get_meaningful_text(text):
    if not text:
        return ""

    cleaned = remove_page_markers(text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def count_meaningful_characters(text):
    return len(get_meaningful_text(text))


def requires_ocr(text):
    return (
        count_meaningful_characters(text)
        < MIN_MEANINGFUL_TEXT_LENGTH
    )


# =========================================================
# OCR TEXT NORMALIZATION
# =========================================================

def normalize_ocr_requirement_ids(text):
    """
    Correct a small set of common OCR mistakes in requirement IDs.

    Example:
        Rt Product type ...
    becomes:
        R1 Product type ...

    The correction is intentionally conservative:
    - R2 must also exist on the same page.
    - Only a Product type row is corrected.
    - Normal document text is not globally modified.

    Returns:
        normalized_text, corrections
    """

    if not text:
        return "", []

    lines = text.splitlines()

    has_r2_row = any(
        re.match(
            r"^\s*R2\b",
            line,
            flags=re.IGNORECASE,
        )
        for line in lines
    )

    if not has_r2_row:
        return text, []

    corrected_lines = []
    corrections = []

    suspicious_r1_pattern = re.compile(
        r"^(\s*)R[tTlLiI|!](\s+Product\s+type\b.*)$"
    )

    for line in lines:
        match = suspicious_r1_pattern.match(line)

        if match:
            corrected_line = (
                f"{match.group(1)}R1{match.group(2)}"
            )

            corrections.append(
                {
                    "from": line.strip(),
                    "to": corrected_line.strip(),
                    "reason": (
                        "Common OCR confusion for requirement ID R1"
                    ),
                }
            )

            corrected_lines.append(corrected_line)

        else:
            corrected_lines.append(line)

    return "\n".join(corrected_lines), corrections


# =========================================================
# NATIVE TEXT EXTRACTION
# =========================================================

def extract_pdf_text(pdf_path):
    """
    Native text-only PDF extraction helper.
    """

    try:
        document = pymupdf.open(pdf_path)

    except Exception as exc:
        raise PDFProcessingError(
            f"Unable to open PDF: {exc}"
        ) from exc

    try:
        if document.page_count <= 0:
            raise PDFProcessingError(
                "PDF contains no pages."
            )

        if document.page_count > MAX_PDF_PAGES:
            raise PDFPageLimitError(
                f"PDF has {document.page_count} pages. "
                f"Maximum supported pages: {MAX_PDF_PAGES}."
            )

        parts = []

        for page_number, page in enumerate(
            document,
            start=1,
        ):
            page_text = page.get_text("text") or ""

            parts.append(
                f"--- PAGE {page_number} ---\n"
                f"{page_text.strip()}"
            )

        return "\n\n".join(parts)

    finally:
        document.close()


# =========================================================
# IMAGE RENDERING
# =========================================================

def render_page_to_image(page):
    zoom = OCR_DPI / 72.0

    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(
            zoom,
            zoom,
        ),
        alpha=False,
    )

    return Image.frombytes(
        "RGB",
        [
            pixmap.width,
            pixmap.height,
        ],
        pixmap.samples,
    )


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image):
    """
    Conservative preprocessing.

    Steps:
    - grayscale
    - automatic contrast
    - light sharpening

    This avoids aggressive thresholding which can damage small text
    and table structures.
    """

    image = image.convert("L")

    image = ImageOps.autocontrast(
        image,
        cutoff=1,
    )

    image = image.filter(
        ImageFilter.UnsharpMask(
            radius=1,
            percent=140,
            threshold=3,
        )
    )

    return image


# =========================================================
# PAGE ROTATION / ORIENTATION
# =========================================================

def detect_rotation(image):
    """
    Detect page orientation using Tesseract OSD.

    OSD can fail for short or sparse text, therefore failure safely
    returns rotation 0.
    """

    try:
        osd = pytesseract.image_to_osd(image)

        match = re.search(
            r"Rotate:\s*(\d+)",
            osd,
        )

        if not match:
            return 0

        rotation = int(
            match.group(1)
        ) % 360

        if rotation in {
            0,
            90,
            180,
            270,
        }:
            return rotation

        return 0

    except Exception:
        return 0


def apply_rotation(
    image,
    clockwise_rotation,
):
    if clockwise_rotation not in {
        90,
        180,
        270,
    }:
        return image

    # Pillow positive rotation is counter-clockwise.
    # Tesseract reports clockwise correction.
    return image.rotate(
        -clockwise_rotation,
        expand=True,
        fillcolor=255,
    )


# =========================================================
# OCR HELPERS
# =========================================================

def _safe_float(value):
    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return -1.0


def ocr_image(image):
    """
    Run Tesseract once using image_to_data.

    This gives:
    - recognized words
    - line information
    - confidence values

    The words are reconstructed back into text lines.
    """

    data = pytesseract.image_to_data(
        image,
        lang=OCR_LANGUAGE,
        config="--oem 3 --psm 3",
        output_type=Output.DICT,
    )

    lines = {}
    confidence_values = []
    word_count = 0

    texts = data.get(
        "text",
        [],
    )

    total_items = len(texts)

    block_numbers = data.get(
        "block_num",
        [0] * total_items,
    )

    paragraph_numbers = data.get(
        "par_num",
        [0] * total_items,
    )

    line_numbers = data.get(
        "line_num",
        [0] * total_items,
    )

    confidences = data.get(
        "conf",
        [-1] * total_items,
    )

    for index, raw_word in enumerate(texts):
        word = (
            raw_word
            or ""
        ).strip()

        if not word:
            continue

        block_num = block_numbers[index]
        par_num = paragraph_numbers[index]
        line_num = line_numbers[index]

        key = (
            block_num,
            par_num,
            line_num,
        )

        lines.setdefault(
            key,
            [],
        ).append(word)

        confidence = _safe_float(
            confidences[index]
        )

        if confidence >= 0:
            confidence_values.append(
                confidence
            )

        word_count += 1

    text_lines = []

    for words in lines.values():
        if words:
            text_lines.append(
                " ".join(words)
            )

    text = "\n".join(
        text_lines
    ).strip()

    if confidence_values:
        average_confidence = round(
            sum(confidence_values)
            / len(confidence_values),
            2,
        )

    else:
        average_confidence = 0.0

    return (
        text,
        average_confidence,
        word_count,
    )


def ocr_page(page):
    """
    Render one PDF page and run OCR.
    """

    configure_tesseract()

    image = render_page_to_image(
        page
    )

    image = preprocess_image(
        image
    )

    rotation = detect_rotation(
        image
    )

    image = apply_rotation(
        image,
        rotation,
    )

    (
        text,
        confidence,
        word_count,
    ) = ocr_image(image)

    return {
        "text": text,
        "confidence": confidence,
        "word_count": word_count,
        "rotation_correction": rotation,
        "preprocessing": [
            "grayscale",
            "autocontrast",
            "unsharp_mask",
            "orientation_check",
        ],
    }


# =========================================================
# HEADER / FOOTER CLEANING
# =========================================================

def _normalize_margin_line(line):
    line = re.sub(
        r"\s+",
        " ",
        (
            line
            or ""
        ).strip().lower(),
    )

    line = re.sub(
        r"\b\d+\b",
        "#",
        line,
    )

    return line


def _nonempty_lines(text):
    return [
        line.strip()
        for line in (
            text
            or ""
        ).splitlines()
        if line.strip()
    ]


def remove_repeated_headers_footers(
    page_texts,
):
    """
    Conservatively remove repeated header/footer lines.

    Cleaning is applied only for PDFs with at least 3 pages.
    """

    if len(page_texts) < 3:
        return page_texts

    candidate_counts = Counter()

    for text in page_texts:
        lines = _nonempty_lines(
            text
        )

        margin_lines = (
            lines[:3]
            + lines[-3:]
        )

        for line in margin_lines:
            normalized = (
                _normalize_margin_line(
                    line
                )
            )

            if (
                3
                <= len(normalized)
                <= 160
            ):
                candidate_counts[
                    normalized
                ] += 1

    threshold = max(
        2,
        math.ceil(
            len(page_texts)
            * 0.60
        ),
    )

    repeated = {
        line
        for (
            line,
            count,
        ) in candidate_counts.items()
        if count >= threshold
    }

    cleaned_pages = []

    for text in page_texts:
        lines = (
            text
            or ""
        ).splitlines()

        nonempty_positions = [
            index
            for (
                index,
                line,
            ) in enumerate(lines)
            if line.strip()
        ]

        top_positions = set(
            nonempty_positions[:3]
        )

        bottom_positions = set(
            nonempty_positions[-3:]
        )

        margin_positions = (
            top_positions
            | bottom_positions
        )

        cleaned_lines = []

        for (
            index,
            line,
        ) in enumerate(lines):

            normalized = (
                _normalize_margin_line(
                    line
                )
            )

            is_simple_page_number = bool(
                re.fullmatch(
                    r"page\s+\d+"
                    r"(?:\s+of\s+\d+)?",
                    line.strip(),
                    flags=re.IGNORECASE,
                )
            )

            should_remove = (
                index
                in margin_positions
                and (
                    normalized
                    in repeated
                    or is_simple_page_number
                )
            )

            if should_remove:
                continue

            cleaned_lines.append(
                line
            )

        cleaned_pages.append(
            "\n".join(
                cleaned_lines
            ).strip()
        )

    return cleaned_pages


# =========================================================
# SMART PDF EXTRACTION WITH OCR
# =========================================================

def extract_pdf_text_with_ocr(
    pdf_path,
):
    """
    Smart PDF extractor.

    Per page:
    - use native text when usable text exists
    - otherwise run OCR

    Supports:
    - native PDFs
    - scanned PDFs
    - mixed native + scanned PDFs
    """

    try:
        document = pymupdf.open(
            pdf_path
        )

    except Exception as exc:
        raise PDFProcessingError(
            f"Unable to open PDF: {exc}"
        ) from exc

    try:
        total_pages = (
            document.page_count
        )

        if total_pages <= 0:
            raise PDFProcessingError(
                "PDF contains no pages."
            )

        if total_pages > MAX_PDF_PAGES:
            raise PDFPageLimitError(
                f"PDF has {total_pages} pages. "
                f"Maximum supported pages: "
                f"{MAX_PDF_PAGES}."
            )

        page_texts = []

        ocr_pages = []
        native_text_pages = []
        low_confidence_pages = []

        page_details = []
        warnings = []

        weighted_confidence_total = 0.0
        weighted_confidence_words = 0

        ocr_page_count = 0

        for (
            page_number,
            page,
        ) in enumerate(
            document,
            start=1,
        ):

            # =============================================
            # TRY NATIVE TEXT FIRST
            # =============================================

            native_text = (
                page.get_text(
                    "text"
                )
                or ""
            )

            native_chars = (
                count_meaningful_characters(
                    native_text
                )
            )

            if (
                native_chars
                >= MIN_PAGE_TEXT_LENGTH
            ):

                native_text_pages.append(
                    page_number
                )

                page_texts.append(
                    native_text.strip()
                )

                page_details.append(
                    {
                        "page": page_number,
                        "source": "native_text",
                        "characters": native_chars,
                        "ocr_confidence": None,
                        "low_confidence": False,
                        "rotation_correction": 0,
                        "preprocessing": [],
                        "id_corrections": [],
                    }
                )

                continue

            # =============================================
            # OCR REQUIRED FOR THIS PAGE
            # =============================================

            ocr_page_count += 1

            if (
                ocr_page_count
                > MAX_OCR_PAGES
            ):
                raise OCRPageLimitError(
                    "OCR page limit exceeded. "
                    f"Maximum OCR pages per PDF: "
                    f"{MAX_OCR_PAGES}."
                )

            try:
                ocr_result = ocr_page(
                    page
                )

            except OCRUnavailableError:
                raise

            except Exception as exc:
                raise PDFProcessingError(
                    f"OCR failed on page "
                    f"{page_number}: {exc}"
                ) from exc

            # =============================================
            # OCR TEXT
            # =============================================

            ocr_text = (
                ocr_result["text"]
            )

            (
                ocr_text,
                id_corrections,
            ) = normalize_ocr_requirement_ids(
                ocr_text
            )

            if id_corrections:
                warnings.append(
                    {
                        "code": (
                            "OCR_REQUIREMENT_ID_NORMALIZED"
                        ),
                        "page": page_number,
                        "message": (
                            "A likely OCR error in a "
                            "structured requirement row "
                            "ID was normalized."
                        ),
                        "corrections": (
                            id_corrections
                        ),
                    }
                )

            ocr_chars = (
                count_meaningful_characters(
                    ocr_text
                )
            )

            confidence = (
                ocr_result[
                    "confidence"
                ]
            )

            word_count = (
                ocr_result[
                    "word_count"
                ]
            )

            ocr_pages.append(
                page_number
            )

            page_texts.append(
                ocr_text.strip()
            )

            # =============================================
            # OCR CONFIDENCE
            # =============================================

            if word_count > 0:
                weighted_confidence_total += (
                    confidence
                    * word_count
                )

                weighted_confidence_words += (
                    word_count
                )

            low_confidence = (
                word_count == 0
                or confidence
                < LOW_OCR_CONFIDENCE_THRESHOLD
            )

            if low_confidence:
                low_confidence_pages.append(
                    page_number
                )

            # =============================================
            # WARNINGS
            # =============================================

            if (
                ocr_chars
                < MIN_PAGE_TEXT_LENGTH
            ):
                warnings.append(
                    {
                        "code": (
                            "LOW_TEXT_AFTER_OCR"
                        ),
                        "page": page_number,
                        "message": (
                            "Very little usable text "
                            "was recovered from this "
                            "OCR page."
                        ),
                    }
                )

            if low_confidence:
                warnings.append(
                    {
                        "code": (
                            "LOW_OCR_CONFIDENCE"
                        ),
                        "page": page_number,
                        "message": (
                            "OCR confidence is below "
                            "the review threshold."
                        ),
                    }
                )

            # =============================================
            # PAGE METADATA
            # =============================================

            page_details.append(
                {
                    "page": page_number,
                    "source": "ocr",
                    "characters": (
                        ocr_chars
                    ),
                    "ocr_confidence": (
                        confidence
                    ),
                    "low_confidence": (
                        low_confidence
                    ),
                    "rotation_correction": (
                        ocr_result[
                            "rotation_correction"
                        ]
                    ),
                    "preprocessing": (
                        ocr_result[
                            "preprocessing"
                        ]
                    ),
                    "id_corrections": (
                        id_corrections
                    ),
                }
            )

        # =================================================
        # HEADER / FOOTER CLEANUP
        # =================================================

        cleaned_page_texts = (
            remove_repeated_headers_footers(
                page_texts
            )
        )

        # =================================================
        # COMBINE PAGES
        # =================================================

        full_text_parts = []

        for (
            page_number,
            text,
        ) in enumerate(
            cleaned_page_texts,
            start=1,
        ):

            full_text_parts.append(
                f"--- PAGE {page_number} ---\n"
                f"{text.strip()}"
            )

        full_text = "\n\n".join(
            full_text_parts
        )

        # =================================================
        # OVERALL OCR CONFIDENCE
        # =================================================

        if (
            weighted_confidence_words
            > 0
        ):
            overall_ocr_confidence = round(
                weighted_confidence_total
                / weighted_confidence_words,
                2,
            )

        else:
            overall_ocr_confidence = None

        # =================================================
        # EXTRACTION MODE
        # =================================================

        ocr_used = bool(
            ocr_pages
        )

        if (
            ocr_pages
            and native_text_pages
        ):
            extraction_mode = (
                "mixed_native_and_ocr"
            )

        elif ocr_pages:
            extraction_mode = (
                "ocr_only"
            )

        else:
            extraction_mode = (
                "native_text_only"
            )

        # =================================================
        # OCR QUALITY STATUS
        # =================================================

        if not ocr_used:
            ocr_quality_status = (
                "NOT_APPLICABLE"
            )

        elif low_confidence_pages:
            ocr_quality_status = (
                "REVIEW_REQUIRED"
            )

        else:
            ocr_quality_status = (
                "GOOD"
            )

        # =================================================
        # OCR ENGINE VERSION
        # =================================================

        tesseract_version = None

        if ocr_used:
            try:
                tesseract_version = str(
                    pytesseract.get_tesseract_version()
                ).splitlines()[0]

            except Exception:
                tesseract_version = (
                    "Tesseract OCR"
                )

        # =================================================
        # FINAL EXTRACTION METADATA
        # =================================================

        extraction_info = {
            "ocr_used": ocr_used,
            "ocr_pages": ocr_pages,
            "native_text_pages": (
                native_text_pages
            ),
            "total_pages": total_pages,
            "ocr_confidence": (
                overall_ocr_confidence
            ),
            "low_confidence_pages": (
                low_confidence_pages
            ),
            "ocr_review_required": bool(
                low_confidence_pages
            ),
            "ocr_quality_status": (
                ocr_quality_status
            ),
            "ocr_page_details": (
                page_details
            ),
            "ocr_warnings": warnings,
            "extraction_mode": (
                extraction_mode
            ),
            "ocr_engine": (
                tesseract_version
            ),
            "max_pdf_pages": (
                MAX_PDF_PAGES
            ),
            "max_ocr_pages": (
                MAX_OCR_PAGES
            ),
        }

        return (
            full_text,
            extraction_info,
        )

    finally:
        document.close()