from app.services.matching_service import (
    match_requirement_to_standards,
)

from app.services.semantic_service import (
    semantic_match_requirement,
)


# =========================================================
# HYBRID MATCHING CONFIGURATION
# =========================================================

KEYWORD_WEIGHT = 0.40
SEMANTIC_WEIGHT = 0.60

# Semantic/hybrid score threshold.
# Strong keyword evidence unte score threshold kanna takkuva
# unna kuda candidate recommendation ga retain chestham.
MIN_ACCEPTABLE_SCORE = 35.0

# Below this score, human review is required.
LOW_CONFIDENCE_THRESHOLD = 45.0


# =========================================================
# CONFIDENCE LEVEL
# =========================================================

def get_hybrid_confidence_level(score):
    if score >= 70:
        return "HIGH"

    if score >= 45:
        return "MEDIUM"

    return "LOW"


# =========================================================
# EVIDENCE STRENGTH
# =========================================================

def get_evidence_strength(score):
    if score >= 70:
        return "STRONG"

    if score >= 45:
        return "MODERATE"

    return "WEAK"


# =========================================================
# BUILD DECISION
# =========================================================

def build_hybrid_decision(
    requirement,
    best_match,
):
    # -----------------------------------------------------
    # NO MATCH
    # -----------------------------------------------------

    if best_match is None:
        return {
            "decision": "NO_MATCH_FOUND",

            "decision_reason": (
                "No sufficiently relevant verified standard "
                "was identified using keyword and "
                "semantic evidence."
            ),

            "review_flags": [
                "NO_STANDARD_MATCH"
            ],

            "recommended_action": (
                "Verify this requirement using the official "
                "Bureau of Indian Standards portal."
            ),

            "review_priority": "HIGH",
        }


    flags = []
    reasons = []


    # -----------------------------------------------------
    # UNVERIFIED STANDARD
    # -----------------------------------------------------

    if not best_match.get(
        "verified",
        False,
    ):
        flags.append(
            "UNVERIFIED_STANDARD"
        )

        reasons.append(
            "The recommended standard "
            "is not yet verified."
        )


    # -----------------------------------------------------
    # LOW HYBRID CONFIDENCE
    # -----------------------------------------------------

    if (
        best_match.get(
            "hybrid_score",
            0,
        )
        < LOW_CONFIDENCE_THRESHOLD
    ):
        flags.append(
            "LOW_HYBRID_CONFIDENCE"
        )

        reasons.append(
            "The hybrid matching confidence "
            "is low."
        )


    # -----------------------------------------------------
    # REQUIREMENT NEEDS CLARIFICATION
    # -----------------------------------------------------

    if (
        requirement.get(
            "status"
        )
        == "needs_clarification"
    ):
        flags.append(
            "NEEDS_CLARIFICATION"
        )

        reasons.append(
            "The procurement requirement "
            "is vague or incomplete."
        )


    # -----------------------------------------------------
    # FINAL DECISION
    # -----------------------------------------------------

    if len(flags) == 0:

        decision = "MATCH_FOUND"

        review_priority = "LOW"

        recommended_action = (
            "The keyword and semantic evidence "
            "support this recommendation. "
            "Final compliance verification "
            "is still recommended."
        )

    else:

        decision = (
            "HUMAN_REVIEW_REQUIRED"
        )


        if (
            "NEEDS_CLARIFICATION"
            in flags
            or
            "LOW_HYBRID_CONFIDENCE"
            in flags
        ):
            review_priority = "HIGH"

        else:
            review_priority = "MEDIUM"


        if (
            "NEEDS_CLARIFICATION"
            in flags
        ):
            recommended_action = (
                "Clarify the procurement "
                "requirement before final "
                "standard selection."
            )

        elif (
            "LOW_HYBRID_CONFIDENCE"
            in flags
        ):
            recommended_action = (
                "Review the AI recommendation "
                "manually because the hybrid "
                "confidence is low."
            )

        else:
            recommended_action = (
                "Verify the recommended standard "
                "from an authoritative source "
                "before acceptance."
            )


    decision_reason = " ".join(
        reasons
    )


    if not decision_reason:
        decision_reason = (
            "Keyword and semantic evidence "
            "support this recommendation."
        )


    return {
        "decision": decision,

        "decision_reason": (
            decision_reason
        ),

        "review_flags": (
            flags
        ),

        "recommended_action": (
            recommended_action
        ),

        "review_priority": (
            review_priority
        ),
    }


# =========================================================
# HYBRID MATCH REQUIREMENT
# =========================================================

def hybrid_match_requirement(
    requirement,
    standards,
    top_k=3,
):

    # -----------------------------------------------------
    # NO STANDARDS
    # -----------------------------------------------------

    if not standards:
        return {
            "decision": (
                "NO_MATCH_FOUND"
            ),

            "decision_reason": (
                "No standards are available "
                "for matching."
            ),

            "review_flags": [
                "NO_STANDARD_MATCH"
            ],

            "recommended_action": (
                "Add standards to the database."
            ),

            "review_priority": (
                "HIGH"
            ),

            "best_match": None,

            "all_matches": [],

            "match_method": (
                "HYBRID_KEYWORD_SEMANTIC_V1"
            ),
        }


    # =====================================================
    # 1. KEYWORD MATCHING
    # =====================================================

    keyword_result = (
        match_requirement_to_standards(
            requirement,
            standards,
        )
    )


    keyword_matches = (
        keyword_result.get(
            "all_matches",
            [],
        )
    )


    keyword_lookup = {}


    for match in keyword_matches:

        standard_id = (
            match.get(
                "standard_id"
            )
        )

        if standard_id:
            keyword_lookup[
                standard_id
            ] = match


    # =====================================================
    # 2. SEMANTIC AI MATCHING
    # =====================================================

    semantic_matches = (
        semantic_match_requirement(
            requirement,
            standards,
            top_k=len(standards),
        )
    )


    semantic_lookup = {}


    for match in semantic_matches:

        standard_id = (
            match.get(
                "standard_id"
            )
        )

        if standard_id:
            semantic_lookup[
                standard_id
            ] = match


    # =====================================================
    # 3. COMBINE KEYWORD + SEMANTIC SCORES
    # =====================================================

    hybrid_matches = []


    for standard in standards:

        standard_id = (
            standard.get(
                "standard_id"
            )
            or standard.get(
                "id"
            )
        )


        keyword_match = (
            keyword_lookup.get(
                standard_id
            )
        )


        semantic_match = (
            semantic_lookup.get(
                standard_id
            )
        )


        # -------------------------------------------------
        # KEYWORD SCORE
        # -------------------------------------------------

        if keyword_match:

            keyword_score = float(
                keyword_match.get(
                    "confidence",
                    0,
                )
            )


            matched_keywords = (
                keyword_match.get(
                    "matched_keywords",
                    [],
                )
            )

        else:

            keyword_score = 0.0
            matched_keywords = []


        # -------------------------------------------------
        # SEMANTIC SCORE
        # -------------------------------------------------

        if semantic_match:

            semantic_score = float(
                semantic_match.get(
                    "semantic_score",
                    0,
                )
            )

        else:

            semantic_score = 0.0


        # -------------------------------------------------
        # HYBRID SCORE
        # -------------------------------------------------

        hybrid_score = (
            keyword_score
            * KEYWORD_WEIGHT
            +
            semantic_score
            * SEMANTIC_WEIGHT
        )


        hybrid_score = round(
            hybrid_score,
            2,
        )


        # -------------------------------------------------
        # SOURCE VERIFICATION
        # -------------------------------------------------

        verified = (
            standard.get(
                "verified",
                False,
            )
        )


        if verified:

            source_verification_status = (
                "VERIFIED_SOURCE"
            )

        else:

            source_verification_status = (
                "UNVERIFIED_SOURCE"
            )


        # -------------------------------------------------
        # MODEL NAME
        # -------------------------------------------------

        model_name = None


        if semantic_match:

            model_name = (
                semantic_match.get(
                    "model_name"
                )
            )


        # -------------------------------------------------
        # SEMANTIC EVIDENCE
        # -------------------------------------------------

        requirement_text = None
        standard_text = None


        if semantic_match:

            semantic_evidence = (
                semantic_match.get(
                    "evidence",
                    {},
                )
            )


            requirement_text = (
                semantic_evidence.get(
                    "requirement_text"
                )
            )


            standard_text = (
                semantic_evidence.get(
                    "standard_text"
                )
            )


        # -------------------------------------------------
        # BUILD HYBRID RESULT
        # -------------------------------------------------

        result = {

            "traceability_id": (
                f"{requirement.get('id')}"
                f"-{standard_id}"
            ),

            "standard_id": (
                standard_id
            ),

            "standard_number": (
                standard.get(
                    "standard_number"
                )
            ),

            "title": (
                standard.get(
                    "title"
                )
            ),

            "keyword_score": round(
                keyword_score,
                2,
            ),

            "semantic_score": round(
                semantic_score,
                2,
            ),

            "hybrid_score": (
                hybrid_score
            ),

            # Database compatibility:
            # confidence field stores hybrid confidence.
            "confidence": (
                hybrid_score
            ),

            "confidence_level": (
                get_hybrid_confidence_level(
                    hybrid_score
                )
            ),

            "evidence_strength": (
                get_evidence_strength(
                    hybrid_score
                )
            ),

            "matched_keywords": (
                matched_keywords
            ),

            "verified": (
                verified
            ),

            "source_verification_status": (
                source_verification_status
            ),

            "source_name": (
                standard.get(
                    "source_name"
                )
            ),

            "source_url": (
                standard.get(
                    "source_url"
                )
            ),

            "evidence_type": (
                "HYBRID_KEYWORD_SEMANTIC"
            ),

            "match_method": (
                "HYBRID_KEYWORD_SEMANTIC_V1"
            ),

            "model_name": (
                model_name
            ),

            "evidence": {

                "requirement_text": (
                    requirement_text
                ),

                "standard_text": (
                    standard_text
                ),

                "matched_keywords": (
                    matched_keywords
                ),

                "keyword_score": (
                    round(
                        keyword_score,
                        2,
                    )
                ),

                "semantic_score": (
                    round(
                        semantic_score,
                        2,
                    )
                ),

                "hybrid_score": (
                    hybrid_score
                ),

                "keyword_weight": (
                    KEYWORD_WEIGHT
                ),

                "semantic_weight": (
                    SEMANTIC_WEIGHT
                ),
            },
        }


        hybrid_matches.append(
            result
        )


    # =====================================================
    # 4. SORT HIGHEST HYBRID SCORE FIRST
    # =====================================================

    hybrid_matches.sort(
        key=lambda item: (
            item.get(
                "hybrid_score",
                0,
            )
        ),
        reverse=True,
    )


       # =====================================================
    # 5. KEEP ONLY VERIFIED BIS CANDIDATES
    # =====================================================

    verified_matches = [
        item
        for item in hybrid_matches
        if item.get("verified") is True
    ]


    # =====================================================
    # 6. RETURN TOP K VERIFIED BIS CANDIDATES
    # =====================================================

    top_matches = (
        verified_matches[
            :top_k
        ]
    )


    # =====================================================
    # 7. SELECT BEST VERIFIED BIS MATCH
    # =====================================================

    best_match = None


    if top_matches:

        candidate = (
            top_matches[0]
        )


        matched_keywords = (
            candidate.get(
                "matched_keywords",
                [],
            )
        )


        has_keyword_evidence = (
            len(matched_keywords) > 0
        )


        has_strong_semantic_evidence = (
            candidate.get(
                "hybrid_score",
                0,
            )
            >= MIN_ACCEPTABLE_SCORE
            and
            candidate.get(
                "semantic_score",
                0,
            )
            >= 45.0
        )


        if (
            has_keyword_evidence
            or has_strong_semantic_evidence
        ):
            best_match = candidate

    # =====================================================
    # 8. BUILD FINAL DECISION
    # =====================================================

    decision_data = (
        build_hybrid_decision(
            requirement,
            best_match,
        )
    )
        # =====================================================
    # 9. FINAL RESPONSE
    # =====================================================

    return {
        "decision": (
            decision_data[
                "decision"
            ]
        ),

        "decision_reason": (
            decision_data[
                "decision_reason"
            ]
        ),

        "review_flags": (
            decision_data[
                "review_flags"
            ]
        ),

        "recommended_action": (
            decision_data[
                "recommended_action"
            ]
        ),

        "review_priority": (
            decision_data[
                "review_priority"
            ]
        ),

        "best_match": (
            best_match
        ),

        "all_matches": (
            top_matches
        ),

        "match_method": (
            "HYBRID_KEYWORD_SEMANTIC_V1"
        ),
    }