from sentence_transformers import SentenceTransformer, util


# =========================================================
# SEMANTIC MODEL CONFIGURATION
# =========================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None


# =========================================================
# LOAD MODEL ONLY WHEN REQUIRED
# =========================================================

def get_semantic_model():
    global _model

    if _model is None:
        print(
            f"Loading semantic model: {MODEL_NAME}"
        )

        _model = SentenceTransformer(
            MODEL_NAME
        )

        print(
            "Semantic model loaded successfully"
        )

    return _model


# =========================================================
# BUILD REQUIREMENT TEXT
# =========================================================

def build_requirement_text(
    requirement
):
    requirement_name = (
        requirement.get(
            "requirement",
            "",
        )
    )

    value = (
        requirement.get(
            "value",
            "",
        )
    )

    notes = (
        requirement.get(
            "notes",
            "",
        )
    )

    text = (
        f"{requirement_name}. "
        f"{value}. "
        f"{notes}"
    )

    return text.strip()


# =========================================================
# BUILD STANDARD TEXT
# =========================================================

def build_standard_text(
    standard
):
    title = (
        standard.get(
            "title",
            "",
        )
    )

    standard_number = (
        standard.get(
            "standard_number",
            "",
        )
    )

    keywords = (
        standard.get(
            "keywords",
            [],
        )
    )

    keyword_text = " ".join(
        keywords
    )

    text = (
        f"{standard_number}. "
        f"{title}. "
        f"{keyword_text}"
    )

    return text.strip()


# =========================================================
# SEMANTIC CONFIDENCE LEVEL
# =========================================================

def get_semantic_confidence_level(
    score
):
    if score >= 70:
        return "HIGH"

    if score >= 45:
        return "MEDIUM"

    return "LOW"


# =========================================================
# SEMANTIC MATCHING
# =========================================================

def semantic_match_requirement(
    requirement,
    standards,
    top_k=3,
):
    if not standards:
        return []


    model = get_semantic_model()


    # -----------------------------------------------------
    # REQUIREMENT TEXT
    # -----------------------------------------------------

    requirement_text = (
        build_requirement_text(
            requirement
        )
    )


    # -----------------------------------------------------
    # STANDARD TEXTS
    # -----------------------------------------------------

    standard_texts = [
        build_standard_text(
            standard
        )
        for standard in standards
    ]


    # -----------------------------------------------------
    # CREATE EMBEDDINGS
    # -----------------------------------------------------

    requirement_embedding = (
        model.encode(
            requirement_text,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )
    )


    standard_embeddings = (
        model.encode(
            standard_texts,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )
    )


    # -----------------------------------------------------
    # COSINE SIMILARITY
    # -----------------------------------------------------

    similarity_scores = (
        util.cos_sim(
            requirement_embedding,
            standard_embeddings,
        )[0]
    )


    scores = (
        similarity_scores
        .cpu()
        .tolist()
    )


    # -----------------------------------------------------
    # BUILD RESULTS
    # -----------------------------------------------------

    results = []


    for index, raw_score in enumerate(
        scores
    ):
        normalized_score = max(
            0.0,
            min(
                1.0,
                float(raw_score),
            ),
        )


        semantic_score = round(
            normalized_score * 100,
            2,
        )


        standard = standards[
            index
        ]


        result = {
            "standard_id": (
                standard.get(
                    "standard_id"
                )
                or standard.get(
                    "id"
                )
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

            "semantic_score": (
                semantic_score
            ),

            "semantic_confidence_level": (
                get_semantic_confidence_level(
                    semantic_score
                )
            ),

            "verified": (
                standard.get(
                    "verified",
                    False,
                )
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

            "match_method": (
                "SEMANTIC_EMBEDDING"
            ),

            "model_name": (
                MODEL_NAME
            ),

            "evidence": {
                "requirement_text": (
                    requirement_text
                ),

                "standard_text": (
                    standard_texts[
                        index
                    ]
                ),
            },
        }


        results.append(
            result
        )


    # -----------------------------------------------------
    # SORT HIGHEST SCORE FIRST
    # -----------------------------------------------------

    results.sort(
        key=lambda item: (
            item[
                "semantic_score"
            ]
        ),
        reverse=True,
    )


    # -----------------------------------------------------
    # RETURN TOP K MATCHES
    # -----------------------------------------------------

    return results[
        :top_k
    ]