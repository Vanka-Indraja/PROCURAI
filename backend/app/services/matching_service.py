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


def get_evidence_strength(confidence):
    if confidence >= 70:
        return "STRONG"

    if confidence >= 40:
        return "MODERATE"

    return "WEAK"


def get_decision(best_match):
    if best_match is None:
        return "NO_MATCH_FOUND"

    if best_match["needs_human_review"]:
        return "HUMAN_REVIEW_REQUIRED"

    return "MATCH_FOUND"


def get_decision_reason(best_match, requirement):
    if best_match is None:
        return "No matching standard was found for this requirement."

    reasons = []

    if best_match["verified"] is False:
        reasons.append(
            "The matched standard is not yet verified."
        )

    if best_match["confidence_level"] == "LOW":
        reasons.append(
            "The current match confidence is low."
        )

    if requirement["status"] == "needs_clarification":
        reasons.append(
            "The procurement requirement is vague or incomplete."
        )

    if not reasons:
        return "A suitable standard match was found."

    return " ".join(reasons)


def get_review_flags(best_match, requirement):
    flags = []

    if best_match is None:
        flags.append("NO_STANDARD_MATCH")
        return flags

    if best_match["verified"] is False:
        flags.append("UNVERIFIED_STANDARD")

    if best_match["confidence_level"] == "LOW":
        flags.append("LOW_CONFIDENCE")

    if requirement["status"] == "needs_clarification":
        flags.append("NEEDS_CLARIFICATION")

    return flags


def get_recommended_action(review_flags):
    if "NO_STANDARD_MATCH" in review_flags:
        return (
            "Search for an applicable standard manually "
            "or expand the standards dataset."
        )

    if "NEEDS_CLARIFICATION" in review_flags:
        return (
            "Clarify the procurement requirement before "
            "final standard selection."
        )

    if "LOW_CONFIDENCE" in review_flags:
        return (
            "Review the suggested standard manually because "
            "the match confidence is low."
        )

    if "UNVERIFIED_STANDARD" in review_flags:
        return (
            "Verify the matched standard from an authoritative "
            "source before acceptance."
        )

    return "No additional review action is required."


def get_review_priority(review_flags):
    if "NO_STANDARD_MATCH" in review_flags:
        return "HIGH"

    if (
        "NEEDS_CLARIFICATION" in review_flags
        or "LOW_CONFIDENCE" in review_flags
    ):
        return "HIGH"

    if "UNVERIFIED_STANDARD" in review_flags:
        return "MEDIUM"

    return "LOW"


def match_requirement_to_standards(
    requirement,
    standards
):
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

        only_generic = all(
            keyword.lower() in GENERIC_KEYWORDS
            for keyword in matched_keywords
        )

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

        evidence_strength = get_evidence_strength(
            confidence
        )

        needs_human_review = (
            confidence_level == "LOW"
            or requirement["status"] == "needs_clarification"
            or standard["verified"] is False
        )

        matches.append({
            "traceability_id": (
                f"{requirement['id']}-{standard['id']}"
            ),
            "standard_id": standard["id"],
            "standard_number": standard["standard_number"],
            "title": standard["title"],
            "match_score": match_score,
            "matched_keywords": matched_keywords,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "evidence_strength": evidence_strength,
            "verified": standard["verified"],
            "needs_human_review": needs_human_review,
            "source_verification_status": (
    "VERIFIED_SOURCE"
    if standard["verified"]
    else "UNVERIFIED_SOURCE"
),"source_verification_status": (
    "VERIFIED_SOURCE"
    if standard["verified"]
    else "UNVERIFIED_SOURCE"
),
            "source_name": standard.get("source_name"),
            "source_url": standard.get("source_url"),
            "evidence_type": "KEYWORD_MATCH",
            "match_method": "baseline_keyword_v1",
            "evidence": {
                "requirement_text": requirement_text,
                "matched_keywords": matched_keywords
            }
        })

    matches.sort(
        key=lambda item: item["confidence"],
        reverse=True
    )

    best_match = matches[0] if matches else None

    decision = get_decision(
        best_match
    )

    decision_reason = get_decision_reason(
        best_match,
        requirement
    )

    review_flags = get_review_flags(
        best_match,
        requirement
    )

    recommended_action = get_recommended_action(
        review_flags
    )

    review_priority = get_review_priority(
        review_flags
    )

    return {
        "decision": decision,
        "decision_reason": decision_reason,
        "review_flags": review_flags,
        "recommended_action": recommended_action,
        "review_priority": review_priority,
        "best_match": best_match,
        "all_matches": matches
    }