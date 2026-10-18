# PROCURAI

## AI-Powered Procurement Standards Intelligence System

PROCURAI is an AI-assisted procurement specification analysis system that extracts technical requirements from procurement PDF documents and recommends relevant standards using a hybrid keyword and semantic matching approach.

The system is designed to reduce the manual effort involved in reading lengthy procurement specifications and identifying applicable technical standards.

> **Important:** The current prototype uses a synthetic test standards dataset for development and demonstration. It does not use authoritative BIS standards and should not be treated as an official compliance decision system.

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

PROCURAI automates the initial analysis process by converting procurement documents into structured requirements and generating explainable standard recommendations.

---

## Problem Statement

Procurement documents may contain long and complex technical specifications.

Identifying the correct applicable standard manually requires:

- Reading complete procurement documents
- Extracting technical requirements
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
PDF Text Extraction
       ↓
OCR Fallback for Scanned Pages
       ↓
Technical Requirement Extraction
       ↓
Requirement Classification
       ↓
Hybrid Standard Matching
       ↓
Keyword Score + Semantic Score
       ↓
Confidence Evaluation
       ↓
Evidence & Explainability
       ↓
Human Review Flags
       ↓
Saved Analysis Report