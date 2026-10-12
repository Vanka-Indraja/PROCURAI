import re


COMMERCIAL_FIELDS = [
    "quantity",
    "price",
    "payment",
    "delivery"
]


KNOWN_NOTES = [
    "Identify product category and intended use",
    "Preserve value and unit exactly",
    "Wording is vague; flag for clarification if needed",
    "No test method or rating supplied",
    "Identify what evidence is actually stated",
    "Commercial detail; likely not a standards-matching requirement"
]


def split_value_and_notes(details):

    for note in KNOWN_NOTES:
        if note in details:
            value = details.replace(note, "").strip()
            return value, note

    return details.strip(), ""


def detect_requirement_status(value, notes):

    text = f"{value} {notes}".lower()

    vague_words = [
        "suitable",
        "to be specified",
        "vague",
        "clarification",
        "no test method",
        "no rating",
        "not specified"
    ]

    if any(word in text for word in vague_words):
        return "needs_clarification"

    return "clear"


def extract_requirements(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    requirements = []

    try:
        start_index = lines.index("2. Technical Requirements")
    except ValueError:
        start_index = 0

    try:
        end_index = lines.index("3. Additional Notes")
    except ValueError:
        end_index = len(lines)

    section = lines[start_index:end_index]

    current_id = None
    current_data = []

    for line in section:

        if re.fullmatch(r"R\d+", line):

            if current_id and current_data:

                requirement_name = current_data[0]
                details = " ".join(current_data[1:])

                value, notes = split_value_and_notes(details)

                req_type = "technical"

                if requirement_name.lower() in COMMERCIAL_FIELDS:
                    req_type = "commercial"

                status = detect_requirement_status(
                    value,
                    notes
                )

                requirements.append({
                    "id": current_id,
                    "requirement": requirement_name,
                    "value": value,
                    "notes": notes,
                    "type": req_type,
                    "status": status
                })

            current_id = line
            current_data = []

        elif current_id:
            current_data.append(line)

    # Save last requirement
    if current_id and current_data:

        requirement_name = current_data[0]
        details = " ".join(current_data[1:])

        value, notes = split_value_and_notes(details)

        req_type = "technical"

        if requirement_name.lower() in COMMERCIAL_FIELDS:
            req_type = "commercial"

        status = detect_requirement_status(
            value,
            notes
        )

        requirements.append({
            "id": current_id,
            "requirement": requirement_name,
            "value": value,
            "notes": notes,
            "type": req_type,
            "status": status
        })

    technical_requirements = [
        req for req in requirements
        if req["type"] == "technical"
    ]

    return technical_requirements