GENERIC_KEYWORDS = [
    "cable",
    "electrical",
    "testing",
    "product"
]


def get_confidence_level(confidence):

    if confidence >= 70:
        return "HIGH"

    if confidence >= 40:
        return "MEDIUM"

    return "LOW"


def match_requirement_to_standards(requirement, standards):

    requirement_text = (
        f"{requirement['requirement']} "
        f"{requirement['value']}"
    ).lower()

    matches = []

    for standard in standards:

        matched_keywords = []

        for keyword in standard["keywords"]:

            if keyword.lower() in requirement_text:
                matched_keywords.append(keyword)

        if not matched_keywords:
            continue

        # Check whether match is only based on weak generic words
        only_generic = all(
            keyword.lower() in GENERIC_KEYWORDS
            for keyword in matched_keywords
        )

        # Ignore weak generic-only match
        if only_generic and len(matched_keywords) == 1:
            continue

        match_score = len(matched_keywords)

        total_keywords = len(standard["keywords"])

        confidence = round(
            (match_score / total_keywords) * 100,
            2
        )

        confidence_level = get_confidence_level(
            confidence
        )

        matches.append({
            "standard_id": standard["id"],
            "standard_number": standard["standard_number"],
            "title": standard["title"],
            "match_score": match_score,
            "matched_keywords": matched_keywords,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "verified": standard["verified"]
        })

    matches.sort(
        key=lambda item: item["confidence"],
        reverse=True
    )

    return matches