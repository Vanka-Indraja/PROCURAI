import re


# =========================================================
# COMMERCIAL KEYWORDS
# =========================================================

COMMERCIAL_KEYWORDS = {
    "quantity",
    "qty",
    "price",
    "cost",
    "rate",
    "amount",
    "payment",
    "delivery period",
    "delivery date",
    "bid price",
    "emd",
    "earnest money",
    "tender fee",
    "tax",
    "gst",
}


# =========================================================
# TECHNICAL SECTION NAMES
# =========================================================

TECHNICAL_SECTION_NAMES = {
    "technical requirements",
    "technical requirement",
    "technical specifications",
    "technical specification",
    "technical specs",
    "technical data",
    "specifications",
}


# =========================================================
# OTHER SECTION HEADINGS
# =========================================================

SECTION_HEADINGS = {
    "procurement overview",
    "overview",
    "additional notes",
    "notes",
    "expected procurai processing behaviour",
    "expected processing behaviour",
    "commercial terms",
    "terms and conditions",
    "price schedule",
    "bid details",
    "introduction",
    "scope",
    "scope of work",
}


# =========================================================
# TECHNICAL CATEGORY PATTERNS
# =========================================================

TECHNICAL_CATEGORY_PATTERNS = {

    "voltage": [
        r"\bvoltage\b",
        r"\bkv\b",
        r"\bvolts?\b",
    ],

    "current": [
        r"\bcurrent\b",
        r"\bampere\b",
        r"\bamps?\b",
        r"\d+(\.\d+)?\s*a\b",
    ],

    "power": [
        r"\bpower\b",
        r"\bkw\b",
        r"\bwatts?\b",
    ],

    "insulation": [
        r"\binsulation\b",
        r"\binsulated\b",
        r"\bxlpe\b",
        r"\bpvc\b",
    ],

    "fire_safety": [
        r"\bfire\b",
        r"\bflame\b",
        r"\bflame retardant\b",
        r"\bfire resistant\b",
        r"\bfrls\b",
    ],

    "testing": [
        r"\btest\b",
        r"\btesting\b",
        r"\btested\b",
        r"\btest certificates?\b",
        r"\btest reports?\b",
        r"\binspection\b",
        r"\bverification\b",
    ],

    "certification": [
        r"\bcertificates?\b",
        r"\bcertification\b",
        r"\bcertified\b",
        r"\bcompliance\b",
        r"\bconformity\b",
        r"\bapproval\b",
    ],

    "dimensions": [
        r"\bdimension\b",
        r"\bdiameter\b",
        r"\blength\b",
        r"\bwidth\b",
        r"\bheight\b",
        r"\bthickness\b",
        r"\bmm\b",
        r"\bcm\b",
    ],

    "temperature": [
        r"\btemperature\b",
        r"\bdegrees?\b",
        r"\b°c\b",
        r"\bcelsius\b",
    ],

    "material": [
        r"\bmaterial\b",
        r"\bcopper\b",
        r"\baluminium\b",
        r"\baluminum\b",
        r"\bsteel\b",
        r"\bpolymer\b",
    ],

    "performance": [
        r"\bperformance\b",
        r"\befficiency\b",
        r"\brating\b",
        r"\bcapacity\b",
        r"\btolerance\b",
    ],

    "safety": [
        r"\bsafety\b",
        r"\bprotection\b",
        r"\bprotective\b",
        r"\bhazard\b",
        r"\bshock\b",
    ],

    "environmental": [
        r"\benvironment\b",
        r"\benvironmental\b",
        r"\bhumidity\b",
        r"\bweather\b",
        r"\bcorrosion\b",
        r"\bwater resistant\b",
        r"\bip\d{2}\b",
    ],

    "product": [
        r"\bproduct\b",
        r"\bitem\b",
        r"\bequipment\b",
        r"\bcable\b",
        r"\bdevice\b",
        r"\bsystem\b",
    ],
}


# =========================================================
# VAGUE WORDING
# =========================================================

VAGUE_PHRASES = [
    "suitable",
    "adequate",
    "appropriate",
    "proper",
    "good quality",
    "high quality",
    "as required",
    "as necessary",
    "if required",
    "where required",
    "standard quality",
    "sufficient",
    "acceptable",
    "best quality",
    "relevant standard",
    "applicable standard",
    "to be specified",
    "not specified",
    "unspecified",
]


# =========================================================
# REQUIREMENT SIGNAL WORDS
# =========================================================

REQUIREMENT_SIGNAL_WORDS = [
    "shall",
    "must",
    "should",
    "required",
    "requirement",
    "rated",
    "rating",
    "comply",
    "compliance",
    "conform",
    "tested",
    "testing",
    "certificate",
    "minimum",
    "maximum",
    "not less than",
    "not more than",
]


# =========================================================
# DISPLAY NAMES
# =========================================================

CATEGORY_DISPLAY_NAMES = {
    "product": "Product type",
    "voltage": "Rated voltage",
    "current": "Current rating",
    "power": "Power requirement",
    "insulation": "Insulation",
    "fire_safety": "Fire performance",
    "testing": "Testing",
    "certification": "Certification",
    "dimensions": "Dimensions",
    "temperature": "Temperature requirement",
    "material": "Material",
    "performance": "Performance",
    "safety": "Safety requirement",
    "environmental": "Environmental requirement",
    "general_technical": "Technical requirement",
}


# =========================================================
# CLEAN LINE
# =========================================================

def clean_line(line):

    if not line:
        return ""

    line = re.sub(
        r"\s+",
        " ",
        line.strip(),
    )

    line = re.sub(
        r"^[•●▪■►➢➤✓✔]+\s*",
        "",
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
            line,
            flags=re.IGNORECASE,
        )
    )


# =========================================================
# REMOVE LIST PREFIX
# =========================================================

def remove_list_prefix(line):

    line = re.sub(
        r"^\s*\d+(\.\d+)*[\.\)]?\s*",
        "",
        line,
    )

    line = re.sub(
        r"^\s*[A-Za-z][\.\)]\s+",
        "",
        line,
    )

    return line.strip()


# =========================================================
# NORMALIZE HEADING
# =========================================================

def normalize_heading(line):

    return (
        remove_list_prefix(
            clean_line(line)
        )
        .lower()
        .strip(" :.-")
    )


# =========================================================
# MEASUREMENT CHECK
# =========================================================

def looks_like_measurement(line):

    lowered = clean_line(
        line
    ).lower()

    unit_pattern = (
        r"^\d+(\.\d+)?\s*"
        r"(kv|v|volt|volts|amp|amps|ampere|a|"
        r"kw|w|watt|watts|mm|cm|m|metre|meter|"
        r"hz|mhz|ghz|kg|g|°c|celsius|%)\b"
    )

    return bool(
        re.search(
            unit_pattern,
            lowered,
            flags=re.IGNORECASE,
        )
    )


# =========================================================
# NUMBERED SECTION HEADING CHECK
# =========================================================

def is_numbered_section_heading(line):

    cleaned = clean_line(
        line
    )

    if looks_like_measurement(
        cleaned
    ):
        return False

    if not re.match(
        r"^\d+(\.\d+)*[\.\)]?\s+[A-Za-z]",
        cleaned,
    ):
        return False

    body = remove_list_prefix(
        cleaned
    )

    if ":" in body:
        return False

    lowered = body.lower()

    for signal in REQUIREMENT_SIGNAL_WORDS:

        if signal in lowered:
            return False

    if len(
        body.split()
    ) > 10:
        return False

    return True


# =========================================================
# FIND TECHNICAL SECTION
# =========================================================

def find_technical_section(lines):

    start = None

    for index, line in enumerate(
        lines
    ):

        heading = normalize_heading(
            line
        )

        if heading in TECHNICAL_SECTION_NAMES:

            start = index + 1

            break


    # No technical section found.
    # Use complete document as fallback.
    if start is None:

        return lines, False


    end = len(
        lines
    )


    for index in range(
        start,
        len(lines),
    ):

        line = lines[
            index
        ]


        if is_numbered_section_heading(
            line
        ):

            heading = normalize_heading(
                line
            )

            if heading not in TECHNICAL_SECTION_NAMES:

                end = index

                break


        elif (
            normalize_heading(
                line
            )
            in SECTION_HEADINGS
        ):

            end = index

            break


    return (
        lines[start:end],
        True,
    )


# =========================================================
# COMMERCIAL REQUIREMENT CHECK
# =========================================================

def is_commercial_requirement(text):

    lowered = text.lower().strip()

    for keyword in COMMERCIAL_KEYWORDS:

        pattern = (
            r"\b"
            + re.escape(keyword)
            + r"\b"
        )

        if re.search(
            pattern,
            lowered,
            flags=re.IGNORECASE,
        ):
            return True

    return False


# =========================================================
# CATEGORY CLASSIFICATION
# =========================================================

def classify_requirement(text):

    lowered = text.lower()

    scores = {}

    for (
        category,
        patterns,
    ) in TECHNICAL_CATEGORY_PATTERNS.items():

        score = 0

        for pattern in patterns:

            if re.search(
                pattern,
                lowered,
                flags=re.IGNORECASE,
            ):

                score += 1


        if score > 0:

            scores[
                category
            ] = score


    if not scores:

        return (
            "general_technical"
        )


    return max(
        scores,
        key=scores.get,
    )


# =========================================================
# STRUCTURED CATEGORY CLASSIFICATION
# =========================================================

def classify_structured_requirement(
    name,
    value,
):

    # Requirement name receives priority.
    #
    # Example:
    # Product type
    # Low-voltage cable
    #
    # should remain PRODUCT,
    # not become VOLTAGE.

    name_category = (
        classify_requirement(
            name
        )
    )


    if (
        name_category
        != "general_technical"
    ):

        return name_category


    return classify_requirement(
        f"{name} {value}"
    )


# =========================================================
# TECHNICAL SIGNAL CHECK
# =========================================================

def has_technical_signal(text):

    lowered = text.lower()


    for patterns in (
        TECHNICAL_CATEGORY_PATTERNS.values()
    ):

        for pattern in patterns:

            if re.search(
                pattern,
                lowered,
                flags=re.IGNORECASE,
            ):

                return True


    for signal in REQUIREMENT_SIGNAL_WORDS:

        if signal in lowered:

            return True


    unit_pattern = (
        r"\b\d+(\.\d+)?\s*"
        r"(kv|v|volt|volts|amp|amps|ampere|"
        r"kw|w|watt|watts|mm|cm|hz|mhz|ghz|"
        r"kg|g|°c|celsius|%)\b"
    )


    if re.search(
        unit_pattern,
        lowered,
        flags=re.IGNORECASE,
    ):

        return True


    return False


# =========================================================
# VAGUE REQUIREMENT DETECTION
# =========================================================

def detect_vague_requirement(text):

    lowered = text.lower()

    found = []


    for phrase in VAGUE_PHRASES:

        if phrase in lowered:

            found.append(
                phrase
            )


    if (
        "rating" in lowered
        and not re.search(
            r"\d",
            lowered,
        )
    ):

        found.append(
            "rating without value"
        )


    if (
        "no test method"
        in lowered
    ):

        found.append(
            "missing test method"
        )


    if (
        "no rating"
        in lowered
    ):

        found.append(
            "missing rating"
        )


    if "vague" in lowered:

        found.append(
            "vague wording"
        )


    return list(
        dict.fromkeys(
            found
        )
    )


# =========================================================
# NORMALIZE REQUIREMENT NAME
# =========================================================

def normalize_requirement_name(
    raw_name,
    category,
):

    raw_name = (
        remove_list_prefix(
            clean_line(
                raw_name
            )
        )
        .strip(" :-")
    )


    if (
        raw_name
        and len(
            raw_name
        ) <= 80
    ):

        return raw_name


    return CATEGORY_DISPLAY_NAMES.get(
        category,
        "Technical requirement",
    )


# =========================================================
# CREATE REQUIREMENT OBJECT
# =========================================================

def create_requirement(
    requirement_id,
    name,
    value,
    category,
    source_text,
    source_note="",
):

    evaluation_text = (
        f"{source_text} "
        f"{source_note}"
    ).strip()


    vague_terms = (
        detect_vague_requirement(
            evaluation_text
        )
    )


    if vague_terms:

        status = (
            "needs_clarification"
        )

    else:

        status = "clear"


    if source_note:

        notes = (
            source_note.strip()
        )

    elif vague_terms:

        notes = (
            "Potentially vague wording detected: "
            + ", ".join(
                vague_terms
            )
        )

    else:

        notes = (
            "Extracted from procurement specification"
        )


    return {

        "id": (
            f"R{requirement_id}"
        ),

        "requirement": (
            normalize_requirement_name(
                name,
                category,
            )
        ),

        "value": (
            value.strip()
            if value
            else source_text.strip()
        ),

        "notes": (
            notes
        ),

        "type": (
            "technical"
        ),

        "status": (
            status
        ),

        "category": (
            category
        ),

        "source_text": (
            source_text.strip()
        ),
    }


# =========================================================
# REQUIREMENT ID CHECK
# =========================================================

def is_requirement_id(line):

    return bool(
        re.fullmatch(
            r"(?:R|REQ|TR)[-_ ]?\d+",
            clean_line(
                line
            ),
            flags=re.IGNORECASE,
        )
    )


# =========================================================
# EXTRACT STRUCTURED R1 / R2 / R3 BLOCKS
# =========================================================

def extract_structured_blocks(lines):

    blocks = []

    index = 0


    while index < len(
        lines
    ):

        if not is_requirement_id(
            lines[index]
        ):

            index += 1

            continue


        next_index = (
            index + 1
        )

        block_lines = []


        while (
            next_index
            < len(lines)
            and not is_requirement_id(
                lines[next_index]
            )
        ):

            block_lines.append(
                clean_line(
                    lines[
                        next_index
                    ]
                )
            )

            next_index += 1


        block_lines = [
            line
            for line
            in block_lines
            if line
        ]


        # Expected structure:
        #
        # R1
        # Product type
        # Electrical cable...
        # Note / explanation

        if len(
            block_lines
        ) >= 2:

            name = (
                block_lines[
                    0
                ]
            )

            value = (
                block_lines[
                    1
                ]
            )

            note = " ".join(
                block_lines[
                    2:
                ]
            ).strip()


            combined_text = (
                f"{name} "
                f"{value} "
                f"{note}"
            ).strip()


            # Exclude Quantity / price / commercial blocks.
            if (
                not is_commercial_requirement(
                    name
                )
                and
                not is_commercial_requirement(
                    combined_text
                )
            ):

                category = (
                    classify_structured_requirement(
                        name,
                        value,
                    )
                )


                if (
                    category
                    != "general_technical"
                    or
                    has_technical_signal(
                        combined_text
                    )
                ):

                    blocks.append(
                        (
                            name,
                            value,
                            note,
                            category,
                        )
                    )


        index = (
            next_index
        )


    return blocks


# =========================================================
# KEY : VALUE PARSER
# =========================================================

def parse_key_value_line(line):

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


    match = re.match(
        r"^([A-Za-z][A-Za-z0-9 /()]{2,60})"
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
# SENTENCE SPLITTER
# =========================================================

def split_sentences(text):

    parts = re.split(
        r"(?<=[.!?;])\s+",
        text,
    )


    sentences = []


    for part in parts:

        cleaned = clean_line(
            part
        )


        if len(
            cleaned
        ) >= 8:

            sentences.append(
                cleaned
            )


    return sentences


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicate_requirements(
    requirements,
):

    unique = []

    seen = set()


    for requirement in requirements:

        fingerprint = (
            requirement.get(
                "requirement",
                "",
            )
            .lower()
            .strip(),

            requirement.get(
                "value",
                "",
            )
            .lower()
            .strip(),
        )


        if fingerprint in seen:

            continue


        seen.add(
            fingerprint
        )

        unique.append(
            requirement
        )


    # Renumber after filtering.
    for index, requirement in enumerate(
        unique,
        start=1,
    ):

        requirement[
            "id"
        ] = f"R{index}"


    return unique


# =========================================================
# MAIN EXTRACTION FUNCTION
# =========================================================

def extract_requirements(text):

    if not text:

        return []


    # =====================================================
    # CLEAN DOCUMENT
    # =====================================================

    lines = []


    for raw_line in (
        text.splitlines()
    ):

        line = clean_line(
            raw_line
        )


        if not line:

            continue


        if is_page_marker(
            line
        ):

            continue


        lines.append(
            line
        )


    # =====================================================
    # FIND TECHNICAL SECTION
    # =====================================================

    (
        candidate_lines,
        technical_section_found,
    ) = find_technical_section(
        lines
    )


    # =====================================================
    # FIRST CHOICE:
    # STRUCTURED REQUIREMENT BLOCKS
    #
    # Example:
    #
    # R1
    # Product type
    # Electrical cable...
    # Notes...
    #
    # =====================================================

    structured_blocks = (
        extract_structured_blocks(
            candidate_lines
        )
    )


    if structured_blocks:

        requirements = []


        for (
            index,
            block,
        ) in enumerate(
            structured_blocks,
            start=1,
        ):

            (
                name,
                value,
                note,
                category,
            ) = block


            requirements.append(
                create_requirement(
                    index,
                    name,
                    value,
                    category,
                    f"{name}. {value}",
                    note,
                )
            )


        return (
            remove_duplicate_requirements(
                requirements
            )
        )


    # =====================================================
    # FALLBACK:
    # GENERAL TENDER TEXT
    # =====================================================

    requirements = []

    counter = 1


    for original_line in (
        candidate_lines
    ):

        line = remove_list_prefix(
            original_line
        )


        if not line:

            continue


        heading = normalize_heading(
            line
        )


        if (
            heading
            in TECHNICAL_SECTION_NAMES
            or
            heading
            in SECTION_HEADINGS
        ):

            continue


        if is_commercial_requirement(
            line
        ):

            continue


        # =================================================
        # KEY : VALUE
        # =================================================

        key_value = (
            parse_key_value_line(
                line
            )
        )


        if key_value:

            (
                key,
                value,
            ) = key_value


            combined_text = (
                f"{key}. {value}"
            )


            if has_technical_signal(
                combined_text
            ):

                category = (
                    classify_structured_requirement(
                        key,
                        value,
                    )
                )


                requirements.append(
                    create_requirement(
                        counter,
                        key,
                        value,
                        category,
                        combined_text,
                    )
                )


                counter += 1


            continue


        # =================================================
        # NORMAL SENTENCE
        # =================================================

        sentences = (
            split_sentences(
                line
            )
        )


        if not sentences:

            sentences = [
                line
            ]


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


            requirements.append(
                create_requirement(
                    counter,
                    "",
                    sentence,
                    category,
                    sentence,
                )
            )


            counter += 1


    return (
        remove_duplicate_requirements(
            requirements
        )
    )