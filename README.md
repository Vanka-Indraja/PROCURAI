# PROCURAI

## AI-Powered Procurement Standards Intelligence System

PROCURAI is an AI-assisted procurement specification analysis system that extracts technical requirements from procurement PDF documents and recommends relevant standards using a hybrid keyword and semantic matching approach.

The system is designed to reduce the manual effort involved in reading lengthy procurement specifications and identifying potentially applicable technical standards.

> **Important:** PROCURAI is a decision-support system, not an automatic compliance certification system. User-facing recommendations are generated from source-verified BIS catalogue metadata available in the current dataset. Final applicability must still be verified using the official Bureau of Indian Standards source.

---

## Project Overview

Procurement specifications often contain many technical requirements such as:

- Product type
- Rated voltage
- Insulation requirements
- Fire-safety requirements
- Testing requirements
- Certification requirements

Manually identifying the most relevant standard for every requirement can be time-consuming and error-prone.

PROCURAI automates the initial analysis process by converting procurement documents into structured technical requirements and generating explainable candidate standard recommendations.

---

## Problem Statement

Procurement documents may contain long and complex technical specifications.

Identifying suitable standards manually requires:

- Reading complete procurement documents
- Extracting technical requirements
- Separating technical and commercial information
- Searching relevant standards
- Comparing requirements with standards
- Checking incomplete or ambiguous requirements
- Performing manual compliance review

This process can consume significant time and may lead to inconsistent results.

---

## Proposed Solution

PROCURAI provides an AI-assisted workflow:

```text
Procurement PDF
        ↓
Native PDF Text Extraction
        ↓
OCR Fallback for Scanned Pages
        ↓
Technical Requirement Extraction
        ↓
Commercial Information Filtering
        ↓
Requirement Classification
        ↓
Requirement Clarity Check
        ↓
Keyword Matching
        +
Semantic AI Matching
        ↓
Hybrid Score Calculation
        ↓
Verified BIS Candidate Ranking
        ↓
Confidence + Evidence
        ↓
Human Review
        ↓
No Suitable Match Handling
        ↓
Official BIS Verification
        ↓
Saved Analysis Report
        ↓
PDF Report Download