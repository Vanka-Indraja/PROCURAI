import re


# =========================================================
# COMMERCIAL / NON-TECHNICAL KEYWORDS
# =========================================================

COMMERCIAL_KEYWORDS = [
    "quantity",
    "commercial detail",
    "unit price",
    "total price",
    "payment terms",
    "delivery period",
    "delivery schedule",
    "bid security",
    "earnest money",
    "emd",
    "gst",
    "tax",
    "freight",
    "invoice",
]


# =========================================================
# TECHNICAL SECTION NAMES
# =========================================================

TECHNICAL_SECTION_NAMES = [
    "technical requirements",
    "technical requirement",
    "technical specifications",
    "technical specification",
    "specifications",
    "technical details",
    "technical parameters",
]


# =========================================================
# COMMON DOCUMENT SECTION HEADINGS
# =========================================================

SECTION_HEADINGS = [
    "procurement overview",
    "technical requirements",
    "technical requirement",
    "technical specifications",
    "technical specification",
    "specifications",
    "technical details",
    "technical parameters",
    "additional notes",
    "expected procurai output",
    "expected procurai processing behaviour",
    "expected processing",
    "commercial details",
    "commercial requirements",
    "terms and conditions",
]


# =========================================================
# CATEGORY PATTERNS
# =========================================================

CATEGORY_PATTERNS = {
    "voltage": [
        r"\brated voltage\b",
        r"\bvoltage rating\b",
        r"\bvoltage\b",
        r"\bkv\b",
        r"\bvolt(?:age)?\b",
    ],

    "insulation": [
        r"\binsulation\b",
        r"\bxlpe\b",
        r"\bpvc insulation\b",
    ],

    "fire_safety": [
        r"\bfire performance\b",
        r"\bfire safety\b",
        r"\bfire-safety\b",
        r"\bflame retardant\b",
        r"\bflame\b",
        r"\bfire resistant\b",
    ],

    "testing": [
        r"\btesting\b",
        r"\btest documentation\b",
        r"\btest certificate\b",
        r"\btest report\b",
        r"\btype test\b",
        r"\broutine test\b",
        r"\binspection\b",
    ],

    "certification": [
        r"\bcertification\b",
        r"\bcertificate\b",
        r"\bcertified\b",
        r"\bcompliance certificate\b",
        r"\bconformity\b",
    ],

    "material": [
        r"\bmaterial\b",
        r"\bcopper\b",
        r"\baluminium\b",
        r"\baluminum\b",
        r"\bpolymer\b",
    ],

    "construction": [
        r"\bconstruction\b",
        r"\barmoured\b",
        r"\barmored\b",
        r"\bsheath\b",
        r"\bjacket\b",
    ],

    "conductor": [
        r"\bconductor\b",
        r"\bconductors\b",
    ],

    "dimensions": [
        r"\bdimension",
        r"\bdiameter\b",
        r"\bthickness\b",
        r"\bsize\b",
        r"\bcross[- ]section",
        r"\bmm2\b",
        r"\bmm²\b",
    ],

    "temperature": [
        r"\btemperature\b",
        r"\bdegrees?\s*c\b",
        r"\b°c\b",
    ],

    "frequency": [
        r"\bfrequency\b",
        r"\bhz\b",
    ],

    "power": [
        r"\bpower\b",
        r"\bwatt",
        r"\bkw\b",
    ],

    "current": [
        r"\bcurrent\b",
        r"\bampere",
        r"\bamps?\b",
    ],

    "efficiency": [
        r"\befficiency\b",
    ],

    "mechanical": [
        r"\bmechanical\b",
        r"\btensile\b",
        r"\bbending\b",
        r"\bimpact\b",
    ],

    "environmental": [
        r"\benvironment",
        r"\bhumidity\b",
        r"\bweather",
        r"\buv resistant\b",
    ],

    "ingress_protection": [
        r"\bingress\b",
        r"\bip\s*\d{2}\b",
        r"\bwaterproof\b",
        r"\bdustproof\b",
    ],

    "product": [
        r"\bproduct type\b",
        r"\bproduct category\b",
        r"\belectrical cable\b",
        r"\bcable for building installation\b",
        r"\bbuilding installation\b",
    ],
}


# =========================================================
# VAGUE / INCOMPLETE PHRASES
# =========================================================

VAGUE_PHRASES = [
    "suitable",
    "adequate",
    "appropriate",
    "good quality",
    "standard quality",
    "as required",
    "as necessary",
    "necessary",
    "sufficient",
    "proper",
    "best quality",
    "to be specified",
    "to be decided",
    "as applicable",
    "vague wording",
    "missing test method",
]


# =========================================================
# REQUIREMENT SIGNALS
# =========================================================

REQUIREMENT_SIGNALS = [
    "shall",
    "must",
    "should",
    "required",
    "requirement",
    "comply",
    "compliance",
    "conform",
    "conformance",
    "withstand",
    "rated",
    "rating",
    "provide",
    "meet",
    "specified",
]


# =========================================================
# DISPLAY NAMES
# =========================================================

CATEGORY_DISPLAY_NAMES = {
    "product": "Product type",
    "voltage": "Rated voltage",
    "insulation": "Insulation",
    "fire_safety": "Fire performance",
    "testing": "Testing",
    "certification": "Certification",
    "material": "Material",
    "construction": "Construction",
    "conductor": "Conductor",
    "dimensions": "Dimensions",
    "temperature": "Temperature",
    "frequency": "Frequency",
    "power": "Power",
    "current": "Current",
    "efficiency": "Efficiency",
    "mechanical": "Mechanical requirement",
    "environmental": "Environmental requirement",
    "ingress_protection": "Ingress protection",
    "general_technical": "Technical requirement",
}


# =========================================================
# OCR INLINE TABLE SUPPORT
# =========================================================

INLINE_REQUIREMENT_LABELS = [
    "fire performance",
    "rated voltage",
    "voltage rating",
    "product type",
    "product category",
    "cable insulation",
    "insulation",
    "testing",
    "certification",
    "material",
    "construction",
    "conductor",
    "dimensions",
    "temperature",
    "frequency",
    "efficiency",
    "current",
    "power",
    "quantity",
]


INLINE_NOTE_STARTS = [
    "identify",
    "preserve",
    "wording",
    "no test",
    "commercial detail",
    "flag for",
]


# =========================================================
# BASIC TEXT CLEANING
# =========================================================

def clean_line(line):
    if not line:
        return ""

    line = line.replace("\u2022", " ")
    line = line.replace("\u2013", "-")
    line = line.replace("\u2014", "-")

    line = re.sub(
        r"\s+",
        " ",
        line,
    )

    return line.strip()


# =========================================================
# PAGE MARKER CHECK
# =========================================================

def is_page_marker(line):
    return bool(
        re.match(
            r"^---\s*PAGE\s+\d+\s*---$",
            line.strip(),
            flags=re.IGNORECASE,
        )
    )


# =========================================================
# REMOVE LIST / NUMBER PREFIX
# =========================================================

def remove_list_prefix(text):
    text = clean_line(text)

    text = re.sub(
        r"^[•*\-]+\s*",
        "",
        text,
    )

    text = re.sub(
        r"^\(?\d+\)?[.)]\s*",
        "",
        text,
    )

    return text.strip()


# =========================================================
# NORMALIZE HEADING
# =========================================================

def normalize_heading(text):
    text = clean_line(text)

    text = re.sub(
        r"^\d+\.\s*",
        "",
        text,
    )

    return (
        text.strip()
        .rstrip(":")
        .lower()
    )


# =========================================================
# MEASUREMENT CHECK
# =========================================================

def looks_like_measurement(text):
    text = clean_line(text)

    return bool(
        re.match(
            r"^\d+(?:\.\d+)?\s*"
            r"(?:v|kv|mv|a|ma|ka|w|kw|mw|hz|khz|mhz|"
            r"mm|cm|m|kg|g|°c|c)\b",
            text,
            flags=re.IGNORECASE,
        )
    )


# =========================================================
# REQUIREMENT SIGNAL CHECK
# =========================================================

def contains_requirement_signal(text):
    lower_text = clean_line(text).lower()

    for signal in REQUIREMENT_SIGNALS:
        if re.search(
            r"\b" + re.escape(signal) + r"\b",
            lower_text,
        ):
            return True

    return False


# =========================================================
# NUMBERED SECTION HEADING CHECK
# =========================================================

def is_numbered_section_heading(line):
    line = clean_line(line)

    if not re.match(
        r"^\d+\.\s+",
        line,
    ):
        return False

    if looks_like_measurement(line):
        return False

    content = re.sub(
        r"^\d+\.\s+",
        "",
        line,
    ).strip()

    if ":" in content:
        return False

    if contains_requirement_signal(content):
        return False

    if len(content.split()) > 10:
        return False

    return True


# =========================================================
# FIND TECHNICAL SECTION
# =========================================================

def find_technical_section(text):
    lines = [
        clean_line(line)
        for line in text.splitlines()
    ]

    start_index = None

    for index, line in enumerate(lines):
        if not line:
            continue

        normalized = normalize_heading(line)

        if normalized in TECHNICAL_SECTION_NAMES:
            start_index = index + 1
            break

    if start_index is None:
        return text

    collected = []

    for line in lines[start_index:]:
        if (
            line
            and is_numbered_section_heading(line)
        ):
            break

        collected.append(line)

    return "\n".join(collected)


# =========================================================
# COMMERCIAL REQUIREMENT CHECK
# =========================================================

def is_commercial_requirement(text):
    lower_text = clean_line(text).lower()

    for keyword in COMMERCIAL_KEYWORDS:
        if re.search(
            r"\b" + re.escape(keyword) + r"\b",
            lower_text,
        ):
            return True

    return False


# =========================================================
# CLASSIFY REQUIREMENT
# =========================================================

def classify_requirement(text):
    lower_text = clean_line(text).lower()

    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(
                pattern,
                lower_text,
                flags=re.IGNORECASE,
            ):
                return category

    return "general_technical"


# =========================================================
# STRUCTURED CLASSIFICATION
# =========================================================

def classify_structured_requirement(
    requirement_name,
    value,
):
    name_category = classify_requirement(
        requirement_name
    )

    if name_category != "general_technical":
        return name_category

    return classify_requirement(value)


# =========================================================
# TECHNICAL SIGNAL CHECK
# =========================================================

def has_technical_signal(text):
    if contains_requirement_signal(text):
        return True

    category = classify_requirement(text)

    return category != "general_technical"


# =========================================================
# VAGUE REQUIREMENT DETECTION
# =========================================================

def detect_vague_requirement(text):
    lower_text = clean_line(text).lower()

    detected = []

    for phrase in VAGUE_PHRASES:
        if phrase in lower_text:
            detected.append(phrase)

    if (
        "rating" in lower_text
        and not re.search(r"\d", lower_text)
    ):
        detected.append(
            "rating value missing"
        )

    if (
        "no test method" in lower_text
        and "missing test method" not in detected
    ):
        detected.append(
            "missing test method"
        )

    return list(
        dict.fromkeys(detected)
    )


# =========================================================
# NORMALIZE REQUIREMENT NAME
# =========================================================

def normalize_requirement_name(
    requirement_name,
    category,
):
    requirement_name = clean_line(
        requirement_name
    )

    if (
        requirement_name
        and requirement_name.lower()
        not in [
            "technical requirement",
            "requirement",
        ]
    ):
        if len(requirement_name.split()) <= 6:
            category_display = (
                CATEGORY_DISPLAY_NAMES.get(
                    category
                )
            )

            if category_display:
                return category_display

    return CATEGORY_DISPLAY_NAMES.get(
        category,
        "Technical requirement",
    )


# =========================================================
# CREATE REQUIREMENT
# =========================================================

def create_requirement(
    requirement_id,
    requirement_name,
    value,
    notes="",
    category=None,
    source_text=None,
):
    requirement_name = clean_line(
        requirement_name
    )

    value = clean_line(value)
    notes = clean_line(notes)

    if category is None:
        category = (
            classify_structured_requirement(
                requirement_name,
                value,
            )
        )

    normalized_name = (
        normalize_requirement_name(
            requirement_name,
            category,
        )
    )

    if source_text is None:
        if requirement_name and value:
            source_text = (
                f"{requirement_name}. "
                f"{value}"
            )
        else:
            source_text = (
                value
                or requirement_name
            )

    source_text = clean_line(
        source_text
    )

    vague_phrases = (
        detect_vague_requirement(
            " ".join(
                [
                    source_text,
                    notes,
                ]
            )
        )
    )

    if vague_phrases:
        status = "needs_clarification"
    else:
        status = "clear"

    if not notes:
        if vague_phrases:
            notes = (
                "Potentially vague wording detected: "
                + ", ".join(vague_phrases)
            )
        else:
            notes = (
                "Extracted from procurement specification"
            )

    return {
        "id": requirement_id,
        "requirement": normalized_name,
        "value": value,
        "notes": notes,
        "type": "technical",
        "status": status,
        "category": category,
        "source_text": source_text,
    }


# =========================================================
# REQUIREMENT ID CHECK
# =========================================================

def is_requirement_id(line):
    return bool(
        re.fullmatch(
            r"R\d+",
            clean_line(line),
            flags=re.IGNORECASE,
        )
    )


# =========================================================
# OCR INLINE ROW NORMALIZER
# =========================================================

def normalize_inline_ocr_rows(text):
    if not text:
        return text

    lines = text.splitlines()

    output_lines = []

    current_row = None

    def flush_row(row_text):
        if not row_text:
            return

        row_text = re.sub(
            r"\s+",
            " ",
            row_text,
        ).strip()

        match = re.match(
            r"^(R\d+)\s+(.+)$",
            row_text,
            flags=re.IGNORECASE,
        )

        if not match:
            output_lines.append(
                row_text
            )
            return

        requirement_id = (
            match.group(1).upper()
        )

        body = (
            match.group(2).strip()
        )

        body_lower = body.lower()

        detected_label = None

        for label in sorted(
            INLINE_REQUIREMENT_LABELS,
            key=len,
            reverse=True,
        ):
            if (
                body_lower == label
                or body_lower.startswith(
                    label + " "
                )
            ):
                detected_label = label
                break

        if detected_label is None:
            output_lines.append(
                row_text
            )
            return

        remaining_text = (
            body[
                len(detected_label):
            ].strip()
        )

        value = remaining_text
        notes = ""

        remaining_lower = (
            remaining_text.lower()
        )

        note_position = None

        for marker in INLINE_NOTE_STARTS:
            marker_match = re.search(
                r"\b"
                + re.escape(marker)
                + r"\b",
                remaining_lower,
            )

            if marker_match:
                position = marker_match.start()

                if (
                    note_position is None
                    or position < note_position
                ):
                    note_position = position

        if note_position is not None:
            value = (
                remaining_text[
                    :note_position
                ].strip(
                    " |;-"
                )
            )

            notes = (
                remaining_text[
                    note_position:
                ].strip()
            )

        label_display = {
            "product type": "Product type",
            "product category": "Product type",
            "rated voltage": "Rated voltage",
            "voltage rating": "Rated voltage",
            "insulation": "Insulation",
            "cable insulation": "Insulation",
            "fire performance": "Fire performance",
            "testing": "Testing",
            "quantity": "Quantity",
        }.get(
            detected_label,
            detected_label.title(),
        )

        output_lines.append(
            requirement_id
        )

        output_lines.append(
            label_display
        )

        if value:
            output_lines.append(
                value
            )

        if notes:
            output_lines.append(
                notes
            )

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            if current_row:
                flush_row(
                    current_row
                )

                current_row = None

            output_lines.append("")
            continue

        # R1 Product type ...
        if re.match(
            r"^R\d+\s+\S",
            line,
            flags=re.IGNORECASE,
        ):
            if current_row:
                flush_row(
                    current_row
                )

            current_row = line
            continue

        # New numbered document section
        if re.match(
            r"^\d+\.\s+",
            line,
        ):
            if current_row:
                flush_row(
                    current_row
                )

                current_row = None

            output_lines.append(
                line
            )

            continue

        # Continuation line from OCR table
        if current_row:
            current_row += (
                " " + line
            )

            continue

        output_lines.append(
            line
        )

    if current_row:
        flush_row(
            current_row
        )

    return "\n".join(
        output_lines
    )


# =========================================================
# EXTRACT STRUCTURED R-BLOCKS
# =========================================================

def extract_structured_blocks(text):
    lines = [
        clean_line(line)
        for line in text.splitlines()
    ]

    blocks = []

    current = None

    for line in lines:
        if not line:
            continue

        if is_page_marker(line):
            continue

        if is_requirement_id(line):
            if current:
                blocks.append(
                    current
                )

            current = {
                "id": line.upper(),
                "lines": [],
            }

            continue

        if current:
            current["lines"].append(
                line
            )

    if current:
        blocks.append(
            current
        )

    requirements = []

    for block in blocks:
        block_lines = (
            block["lines"]
        )

        if len(block_lines) < 2:
            continue

        requirement_name = (
            block_lines[0]
        )

        value = (
            block_lines[1]
        )

        notes = ""

        if len(block_lines) >= 3:
            notes = " ".join(
                block_lines[2:]
            )

        # =================================================
        # NORMAL PDF / OCR LINE-WRAP REPAIR
        #
        # These two layouts are both supported:
        #
        # Layout A:
        # Supplier shall provide test
        # documentation
        # Identify what evidence...
        #
        # Layout B:
        # Supplier shall provide test
        # Identify what evidence...
        # documentation
        # =================================================

        if (
            requirement_name.strip().lower()
            == "testing"
            and value.strip().lower().endswith(
                "test"
            )
        ):
            cleaned_notes = (
                notes.strip()
            )

            # ---------------------------------------------
            # documentation appears at START of notes
            # ---------------------------------------------
            if re.match(
                r"^documentation\b",
                cleaned_notes,
                flags=re.IGNORECASE,
            ):
                value = (
                    value.strip()
                    + " documentation"
                )

                notes = re.sub(
                    r"^documentation\b[\s|;:,-]*",
                    "",
                    cleaned_notes,
                    count=1,
                    flags=re.IGNORECASE,
                ).strip()

            # ---------------------------------------------
            # documentation appears at END of notes
            # ---------------------------------------------
            elif re.search(
                r"\bdocumentation\s*$",
                cleaned_notes,
                flags=re.IGNORECASE,
            ):
                value = (
                    value.strip()
                    + " documentation"
                )

                notes = re.sub(
                    r"\s*documentation\s*$",
                    "",
                    cleaned_notes,
                    flags=re.IGNORECASE,
                ).strip()

        combined_text = " ".join(
            [
                requirement_name,
                value,
                notes,
            ]
        )

        if is_commercial_requirement(
            combined_text
        ):
            continue

        category = (
            classify_structured_requirement(
                requirement_name,
                value,
            )
        )

        source_text = (
            f"{requirement_name}. "
            f"{value}"
        )

        requirement = (
            create_requirement(
                requirement_id=block["id"],
                requirement_name=(
                    requirement_name
                ),
                value=value,
                notes=notes,
                category=category,
                source_text=source_text,
            )
        )

        requirements.append(
            requirement
        )

    return requirements


# =========================================================
# KEY VALUE PARSER
# =========================================================

def parse_key_value_line(line):
    line = remove_list_prefix(
        line
    )

    # LABEL : VALUE
    match = re.match(
        r"^([^:]{2,80})\s*:\s*(.+)$",
        line,
    )

    if match:
        return (
            clean_line(
                match.group(1)
            ),
            clean_line(
                match.group(2)
            ),
        )

    # LABEL - VALUE
    match = re.match(
        r"^([A-Za-z][A-Za-z0-9 /()&]{1,60})"
        r"\s+-\s+(.+)$",
        line,
    )

    if match:
        return (
            clean_line(
                match.group(1)
            ),
            clean_line(
                match.group(2)
            ),
        )

    return None


# =========================================================
# SPLIT SENTENCES
# =========================================================

def split_sentences(text):
    text = clean_line(
        text
    )

    if not text:
        return []

    parts = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    return [
        clean_line(part)
        for part in parts
        if clean_line(part)
    ]


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicate_requirements(
    requirements,
):
    unique = []

    seen = set()

    for requirement in requirements:
        signature = (
            clean_line(
                requirement.get(
                    "source_text",
                    "",
                )
            ).lower()
        )

        if not signature:
            signature = (
                clean_line(
                    requirement.get(
                        "value",
                        "",
                    )
                ).lower()
            )

        if signature in seen:
            continue

        seen.add(signature)
        unique.append(
            requirement
        )

    return unique


# =========================================================
# GENERIC FALLBACK EXTRACTION
# =========================================================

def extract_generic_requirements(text):
    section_text = (
        find_technical_section(
            text
        )
    )

    lines = [
        clean_line(line)
        for line in section_text.splitlines()
    ]

    requirements = []

    next_id = 1

    for line in lines:
        if not line:
            continue

        if is_page_marker(line):
            continue

        normalized_heading = (
            normalize_heading(
                line
            )
        )

        if (
            normalized_heading
            in SECTION_HEADINGS
        ):
            continue

        if is_numbered_section_heading(
            line
        ):
            continue

        cleaned_candidate = (
            remove_list_prefix(
                line
            )
        )

        if not cleaned_candidate:
            continue

        if is_commercial_requirement(
            cleaned_candidate
        ):
            continue

        # =================================================
        # LABEL : VALUE
        # =================================================

        key_value = (
            parse_key_value_line(
                line
            )
        )

        if key_value:
            label, value = (
                key_value
            )

            combined = (
                f"{label} {value}"
            )

            if is_commercial_requirement(
                combined
            ):
                continue

            category = (
                classify_structured_requirement(
                    label,
                    value,
                )
            )

            if (
                category
                == "general_technical"
                and not has_technical_signal(
                    combined
                )
            ):
                continue

            requirements.append(
                create_requirement(
                    requirement_id=(
                        f"R{next_id}"
                    ),
                    requirement_name=(
                        label
                    ),
                    value=value,
                    category=category,
                    source_text=(
                        f"{label}. {value}"
                    ),
                )
            )

            next_id += 1
            continue

        # =================================================
        # NORMAL SENTENCES
        # =================================================

        sentences = (
            split_sentences(
                cleaned_candidate
            )
        )

        for sentence in sentences:
            if is_commercial_requirement(
                sentence
            ):
                continue

            if not has_technical_signal(
                sentence
            ):
                continue

            category = (
                classify_requirement(
                    sentence
                )
            )

            requirement_name = (
                CATEGORY_DISPLAY_NAMES.get(
                    category,
                    "Technical requirement",
                )
            )

            requirements.append(
                create_requirement(
                    requirement_id=(
                        f"R{next_id}"
                    ),
                    requirement_name=(
                        requirement_name
                    ),
                    value=sentence,
                    category=category,
                    source_text=sentence,
                )
            )

            next_id += 1

    return remove_duplicate_requirements(
        requirements
    )


# =========================================================
# MAIN EXTRACTION FUNCTION
# =========================================================

def extract_requirements(text):
    if not text:
        return []

    # OCR table rows:
    # R1 Product type ...
    # ->
    # R1
    # Product type
    # ...
    text = normalize_inline_ocr_rows(
        text
    )

    # Work primarily inside technical section.
    technical_text = (
        find_technical_section(
            text
        )
    )

    # First try R1 / R2 / R3 structured format.
    structured_requirements = (
        extract_structured_blocks(
            technical_text
        )
    )

    if structured_requirements:
        return remove_duplicate_requirements(
            structured_requirements
        )

    # Fallback for generic procurement specifications.
    return extract_generic_requirements(
        text
    )