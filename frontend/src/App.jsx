import { useEffect, useMemo, useRef, useState } from "react";
import { jsPDF } from "jspdf";
import "./App.css";

import {
  checkBackendStatus,
  deleteReport,
  getReport,
  getReports,
  getStandards,
  uploadPdf,
} from "./services/api";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const REPORTS_PER_PAGE = 8;
function generateAnalysisPdf(report) {
  if (!report) {
    throw new Error("Report data is unavailable.");
  }

  const doc = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });

  const pageWidth =
    doc.internal.pageSize.getWidth();

  const pageHeight =
    doc.internal.pageSize.getHeight();

  const margin = 15;
  const contentWidth =
    pageWidth - margin * 2;

  let y = 18;

  function safeValue(
    value,
    fallback = "Not available"
  ) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return fallback;
    }

    if (Array.isArray(value)) {
      return value.length > 0
        ? value.join(", ")
        : fallback;
    }

    return String(value);
  }

  function cleanPdfLabel(value) {
    if (!value) {
      return "Not available";
    }

    return String(value)
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      );
  }

  function pdfScore(value) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "N/A";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return safeValue(value);
    }

    return `${number.toFixed(1)}%`;
  }

  function pdfDate(value) {
    if (!value) {
      return "Not available";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return safeValue(value);
    }

    return date.toLocaleString();
  }

  function ensureSpace(
    requiredHeight = 12
  ) {
    if (
      y + requiredHeight >
      pageHeight - 18
    ) {
      doc.addPage();
      y = 18;

      doc.setFont(
        "helvetica",
        "bold"
      );

      doc.setFontSize(9);

      doc.setTextColor(
        90,
        103,
        128
      );

      doc.text(
        "PROCURAI - Procurement Standards Intelligence",
        margin,
        y
      );

      y += 10;
    }
  }

  function addParagraph(
    text,
    options = {}
  ) {
    const {
      fontSize = 10,
      bold = false,
      color = [70, 82, 105],
      spacing = 5,
    } = options;

    const value =
      safeValue(text);

    doc.setFont(
      "helvetica",
      bold
        ? "bold"
        : "normal"
    );

    doc.setFontSize(
      fontSize
    );

    doc.setTextColor(
      ...color
    );

    const lines =
      doc.splitTextToSize(
        value,
        contentWidth
      );

    const lineHeight =
      fontSize * 0.42 + 1.2;

    ensureSpace(
      lines.length *
        lineHeight +
        spacing
    );

    doc.text(
      lines,
      margin,
      y
    );

    y +=
      lines.length *
        lineHeight +
      spacing;
  }
  function addLabelValue(label, value) {
  const labelText = `${label}:`;
  const valueText = safeValue(value);

  const labelColumnWidth = 42;
  const gap = 3;

  const valueWidth =
    contentWidth -
    labelColumnWidth -
    gap;

  doc.setFont(
    "helvetica",
    "normal"
  );

  doc.setFontSize(9);

  const valueLines =
    doc.splitTextToSize(
      valueText,
      valueWidth
    );

  const lineHeight = 4.5;

  const requiredHeight =
    Math.max(
      lineHeight,
      valueLines.length *
        lineHeight
    ) + 2;

  ensureSpace(
    requiredHeight
  );

  doc.setFont(
    "helvetica",
    "bold"
  );

  doc.setFontSize(9);

  doc.setTextColor(
    37,
    50,
    74
  );

  doc.text(
    labelText,
    margin,
    y
  );

  doc.setFont(
    "helvetica",
    "normal"
  );

  doc.setTextColor(
    85,
    99,
    124
  );

  doc.text(
    valueLines,
    margin +
      labelColumnWidth +
      gap,
    y
  );

  y += requiredHeight;
}

  

  function addSectionTitle(
    title
  ) {
    ensureSpace(15);

    y += 2;

    doc.setFillColor(
      242,
      245,
      252
    );

    doc.roundedRect(
      margin,
      y - 5,
      contentWidth,
      10,
      2,
      2,
      "F"
    );

    doc.setFont(
      "helvetica",
      "bold"
    );

    doc.setFontSize(11);

    doc.setTextColor(
      43,
      64,
      112
    );

    doc.text(
      title,
      margin + 4,
      y + 1.5
    );

    y += 11;
  }

  // =====================================================
  // COVER / HEADER
  // =====================================================

  doc.setFont(
    "helvetica",
    "bold"
  );

  doc.setFontSize(22);

  doc.setTextColor(
    42,
    64,
    120
  );

  doc.text(
    "PROCURAI",
    margin,
    y
  );

  y += 8;

  doc.setFontSize(14);

  doc.setTextColor(
    32,
    45,
    70
  );

  doc.text(
    "AI Procurement Standards Analysis Report",
    margin,
    y
  );

  y += 7;

  doc.setFont(
    "helvetica",
    "normal"
  );

  doc.setFontSize(9);

  doc.setTextColor(
    100,
    112,
    135
  );

  doc.text(
    "Hybrid Keyword + Semantic AI | Explainable Recommendation & Human Review",
    margin,
    y
  );

  y += 10;

  doc.setDrawColor(
    220,
    225,
    235
  );

  doc.line(
    margin,
    y,
    pageWidth - margin,
    y
  );

  y += 9;

  // =====================================================
  // DOCUMENT OVERVIEW
  // =====================================================

  addSectionTitle(
    "Document Overview"
  );

  addLabelValue(
    "Document",
    report?.filename
  );

  addLabelValue(
    "Analysis ID",
    report?.analysis_id
  );

  addLabelValue(
    "Analysis Date",
    pdfDate(
      report?.analysis_timestamp
    )
  );

  addLabelValue(
    "Matching Engine",
    report?.matching_engine ||
      report?.matcher_version
  );

  addLabelValue(
    "Document Status",
    cleanPdfLabel(
      report?.document_status
    )
  );

  addLabelValue(
    "Review Risk",
    cleanPdfLabel(
      report?.review_risk_level
    )
  );

  if (
    report?.review_risk_score !==
      undefined &&
    report?.review_risk_score !== null
  ) {
    addLabelValue(
      "Risk Score",
      report.review_risk_score
    );
  }

  // =====================================================
  // EXTRACTION / OCR
  // =====================================================

  addSectionTitle(
    "Document Extraction"
  );

  addLabelValue(
    "Total Pages",
    report?.total_pages
  );

  addLabelValue(
    "Extraction Mode",
    cleanPdfLabel(
      report?.extraction_mode
    )
  );

  addLabelValue(
    "OCR Used",
    report?.ocr_used
      ? "Yes"
      : "No"
  );

  if (
    report?.ocr_confidence !==
      null &&
    report?.ocr_confidence !==
      undefined
  ) {
    addLabelValue(
      "OCR Confidence",
      pdfScore(
        report.ocr_confidence
      )
    );
  }

  if (
    report?.ocr_quality_status
  ) {
    addLabelValue(
      "OCR Quality",
      cleanPdfLabel(
        report.ocr_quality_status
      )
    );
  }

  // =====================================================
  // ANALYSIS SUMMARY
  // =====================================================

  const summary =
    report?.summary || {};

  addSectionTitle(
    "Analysis Summary"
  );

  addLabelValue(
    "Total Requirements",
    summary?.total_requirements ??
      report?.results?.length ??
      0
  );

  addLabelValue(
    "Human Review Required",
    summary?.human_review_required ??
      0
  );

  addLabelValue(
    "Needs Clarification",
    summary?.needs_clarification ??
      0
  );

  addLabelValue(
    "High Priority",
    summary?.high_priority ??
      0
  );

  addLabelValue(
    "Medium Priority",
    summary?.medium_priority ??
      0
  );

  if (
    Array.isArray(
      report?.document_review_reasons
    ) &&
    report.document_review_reasons
      .length > 0
  ) {
    addSectionTitle(
      "Document Review Reasons"
    );

    report.document_review_reasons.forEach(
      (reason, index) => {
        addParagraph(
          `${index + 1}. ${reason}`,
          {
            fontSize: 9,
          }
        );
      }
    );
  }

  // =====================================================
  // REQUIREMENTS
  // =====================================================

  const results =
    Array.isArray(
      report?.results
    )
      ? report.results
      : [];

  addSectionTitle(
    `Requirement Analysis (${results.length})`
  );

  results.forEach(
    (item, index) => {
      const requirement =
        item?.requirement ||
        {};

      const bestMatch =
        item?.best_match ||
        null;

      const candidates =
        Array.isArray(
          item?.all_matches
        )
          ? item.all_matches.slice(
              0,
              3
            )
          : bestMatch
            ? [bestMatch]
            : [];

      ensureSpace(35);

      doc.setFont(
        "helvetica",
        "bold"
      );

      doc.setFontSize(12);

      doc.setTextColor(
        38,
        55,
        88
      );

      doc.text(
        `Requirement ${index + 1}: ${safeValue(
          requirement?.requirement,
          "Unnamed Requirement"
        )}`,
        margin,
        y
      );

      y += 7;

      addLabelValue(
        "Value",
        requirement?.value
      );

      addLabelValue(
        "Category",
        cleanPdfLabel(
          requirement?.category ||
            requirement?.type
        )
      );

      addLabelValue(
        "Status",
        cleanPdfLabel(
          requirement?.status
        )
      );

      addLabelValue(
        "Decision",
        cleanPdfLabel(
          item?.decision
        )
      );

      addLabelValue(
        "Review Priority",
        cleanPdfLabel(
          item?.review_priority
        )
      );

      if (
        item?.decision_reason
      ) {
        addLabelValue(
          "Decision Reason",
          item.decision_reason
        );
      }

      if (
        item?.recommended_action
      ) {
        addLabelValue(
          "Recommended Action",
          item.recommended_action
        );
      }

      if (
        Array.isArray(
          item?.review_flags
        ) &&
        item.review_flags.length >
          0
      ) {
        addLabelValue(
          "Review Flags",
          item.review_flags
            .map(
              cleanPdfLabel
            )
            .join(", ")
        );
      }

      if (bestMatch) {
        addParagraph(
          "Recommended Standard",
          {
            fontSize: 10,
            bold: true,
            color: [
              55,
              76,
              135,
            ],
            spacing: 3,
          }
        );

        addLabelValue(
          "Standard Number",
          bestMatch?.standard_number ||
            bestMatch?.standard_id
        );

        addLabelValue(
          "Title",
          bestMatch?.title
        );

        addLabelValue(
          "Source",
          bestMatch?.source_name
        );

        addLabelValue(
          "Source Status",
          bestMatch?.verified
            ? "Verified BIS Source"
            : "Synthetic Test Dataset"
        );

        addLabelValue(
          "Keyword Score",
          pdfScore(
            bestMatch?.keyword_score
          )
        );

        addLabelValue(
          "Semantic Score",
          pdfScore(
            bestMatch?.semantic_score
          )
        );

        addLabelValue(
          "Hybrid Score",
          pdfScore(
            bestMatch?.hybrid_score ??
              bestMatch?.confidence
          )
        );

        if (
          Array.isArray(
            bestMatch?.matched_keywords
          ) &&
          bestMatch
            .matched_keywords.length >
            0
        ) {
          addLabelValue(
            "Matched Keywords",
            bestMatch
              .matched_keywords
              .join(", ")
          );
        }
      }

      if (
        candidates.length > 0
      ) {
        addParagraph(
          "Top Candidate Standards",
          {
            fontSize: 10,
            bold: true,
            color: [
              55,
              76,
              135,
            ],
            spacing: 3,
          }
        );

        candidates.forEach(
          (
            candidate,
            candidateIndex
          ) => {
            const sourceStatus =
              candidate?.verified
                ? "Verified BIS"
                : "Synthetic";

            addParagraph(
              `#${candidateIndex + 1} ${safeValue(
                candidate?.standard_number ||
                  candidate?.standard_id,
                "Standard"
              )} | ${pdfScore(
                candidate?.hybrid_score ??
                  candidate?.confidence ??
                  candidate?.match_score
              )} | ${sourceStatus}`,
              {
                fontSize: 9,
                bold:
                  candidateIndex ===
                  0,
                spacing: 2,
              }
            );

            addParagraph(
              safeValue(
                candidate?.title,
                "Title unavailable"
              ),
              {
                fontSize: 8,
                color: [
                  105,
                  115,
                  135,
                ],
                spacing: 3,
              }
            );
          }
        );
      }

      y += 4;

      ensureSpace(4);

      doc.setDrawColor(
        228,
        232,
        240
      );

      doc.line(
        margin,
        y,
        pageWidth - margin,
        y
      );

      y += 8;
    }
  );

  // =====================================================
  // DISCLAIMER
  // =====================================================

  addSectionTitle(
    "Important Verification Notice"
  );

  addParagraph(
    "PROCURAI provides AI-assisted candidate standard recommendations based on requirement relevance, keyword similarity and semantic similarity. A recommendation is not a final legal or compliance determination. Verified BIS metadata indicates that the referenced standard metadata was obtained from an official source; final applicability must still be checked against the latest official Bureau of Indian Standards information and reviewed by an appropriate human expert.",
    {
      fontSize: 9,
      color: [
        85,
        95,
        115,
      ],
      spacing: 5,
    }
  );

  // =====================================================
  // PAGE NUMBERS
  // =====================================================

  const totalPdfPages =
    doc.getNumberOfPages();

  for (
    let page = 1;
    page <= totalPdfPages;
    page += 1
  ) {
    doc.setPage(page);

    doc.setFont(
      "helvetica",
      "normal"
    );

    doc.setFontSize(8);

    doc.setTextColor(
      125,
      135,
      150
    );

    doc.text(
      `PROCURAI | Page ${page} of ${totalPdfPages}`,
      pageWidth - margin,
      pageHeight - 8,
      {
        align: "right",
      }
    );
  }

  // =====================================================
  // SAVE FILE
  // =====================================================

  const originalName =
    safeValue(
      report?.filename,
      "procurement-analysis"
    )
      .replace(/\.pdf$/i, "")
      .replace(
        /[^a-zA-Z0-9-_]+/g,
        "_"
      );

  doc.save(
    `${originalName}_PROCURAI_Report.pdf`
  );
}

// =========================================================
// SAFE HELPERS
// =========================================================

function safeText(value, fallback = "-") {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return fallback;
  }

  if (typeof value === "string") {
    return value;
  }

  if (
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => safeText(item, ""))
      .filter(Boolean)
      .join(", ");
  }

  return fallback;
}

function cleanLabel(value) {
  const text = safeText(value, "-");

  if (text === "-") {
    return text;
  }

  return text
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatScore(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "-";
  }

  const numberValue = Number(value);

  if (Number.isNaN(numberValue)) {
    return safeText(value);
  }

  const percentage =
    numberValue <= 1
      ? numberValue * 100
      : numberValue;

  return `${percentage.toFixed(1)}%`;
}

function normalizeReports(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.reports)) {
    return data.reports;
  }

  return [];
}

function normalizeStandards(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.standards)) {
    return data.standards;
  }

  return [];
}

function formatDateTime(value) {
  if (!value) {
    return "Date unavailable";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return safeText(value, "Date unavailable");
  }

  return date.toLocaleString([], {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getReportDate(report) {
  return (
    report?.timestamp ||
    report?.uploaded_at ||
    report?.created_at ||
    report?.analysis_timestamp ||
    null
  );
}

function getRequirementCount(report) {
  if (Array.isArray(report?.results)) {
    return report.results.length;
  }

  return (
    report?.requirements_count ??
    report?.total_requirements ??
    report?.summary?.total_requirements ??
    "-"
  );
}

function getOcrLabel(report) {
  if (report?.ocr_used === true) {
    return "OCR Used";
  }

  if (report?.ocr_used === false) {
    return "Native Text";
  }

  return "Extraction Info N/A";
}

function getStatusType(status) {
  const normalized = String(status || "").toUpperCase();

  if (normalized === "READY") {
    return "success";
  }

  if (
    normalized === "REVIEW_REQUIRED" ||
    normalized === "INCOMPLETE_MATCHING"
  ) {
    return "warning";
  }

  return "neutral";
}

// =========================================================
// MAIN APP
// =========================================================

function App() {
  const [activePage, setActivePage] = useState("dashboard");

  const [backendOnline, setBackendOnline] = useState(false);
  const [backendChecking, setBackendChecking] = useState(true);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [analysisResult, setAnalysisResult] = useState(null);

  const [reports, setReports] = useState([]);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportsError, setReportsError] = useState("");

  const [standards, setStandards] = useState([]);
  const [standardsLoading, setStandardsLoading] = useState(false);
  const [standardsError, setStandardsError] = useState("");

  const fileInputRef = useRef(null);

  // =======================================================
  // BACKEND STATUS
  // =======================================================

  useEffect(() => {
    async function checkBackend() {
      try {
        const data = await checkBackendStatus();

        setBackendOnline(
          data?.status === "Backend is running"
        );
      } catch (error) {
        console.error(
          "Backend connection failed:",
          error
        );

        setBackendOnline(false);
      } finally {
        setBackendChecking(false);
      }
    }

    checkBackend();
  }, []);

  // =======================================================
  // AUTO LOAD PAGE DATA
  // =======================================================

  useEffect(() => {
    if (!backendOnline) {
      return;
    }

    if (
      activePage === "dashboard" ||
      activePage === "reports"
    ) {
      loadReports();
    }

    if (
      activePage === "dashboard" ||
      activePage === "standards"
    ) {
      loadStandards();
    }
  }, [activePage, backendOnline]);

  // =======================================================
  // REPORTS
  // =======================================================

  async function loadReports() {
    setReportsLoading(true);
    setReportsError("");

    try {
      const data = await getReports();

      setReports(
        normalizeReports(data)
      );
    } catch (error) {
      console.error(
        "Unable to load reports:",
        error
      );

      setReportsError(
        error?.message ||
          "Unable to load reports."
      );
    } finally {
      setReportsLoading(false);
    }
  }

  async function handleViewReport(analysisId) {
    if (!analysisId) {
      return;
    }

    try {
      const report =
        await getReport(analysisId);

      setAnalysisResult(report);
      setSelectedFile(null);
      setUploadError("");
      setActivePage("analyze");

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    } catch (error) {
      window.alert(
        error?.message ||
          "Unable to open report."
      );
    }
  }
 async function handleDownloadReport(analysisId) {
  if (!analysisId) {
    return;
  }

  try {
    const report =
      await getReport(analysisId);

    generateAnalysisPdf(report);
  } catch (error) {
    console.error(
      "Unable to download report:",
      error
    );

    window.alert(
      error?.message ||
        "Unable to generate PDF report."
    );
  }
}

  async function handleDeleteReport(analysisId) {
    if (!analysisId) {
      return;
    }

    const confirmed =
      window.confirm(
        "Are you sure you want to delete this report?"
      );

    if (!confirmed) {
      return;
    }

    try {
      await deleteReport(analysisId);
      await loadReports();
    } catch (error) {
      window.alert(
        error?.message ||
          "Unable to delete report."
      );
    }
  }

  // =======================================================
  // STANDARDS
  // =======================================================

  async function loadStandards() {
    setStandardsLoading(true);
    setStandardsError("");

    try {
      const data =
        await getStandards();

      setStandards(
        normalizeStandards(data)
      );
    } catch (error) {
      console.error(
        "Unable to load standards:",
        error
      );

      setStandardsError(
        error?.message ||
          "Unable to load standards."
      );
    } finally {
      setStandardsLoading(false);
    }
  }

  // =======================================================
  // FILE HELPERS
  // =======================================================

  function formatFileSize(bytes) {
    if (!bytes) {
      return "0 KB";
    }

    const mb =
      bytes / (1024 * 1024);

    if (mb >= 1) {
      return `${mb.toFixed(2)} MB`;
    }

    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  function validateAndSelectFile(file) {
    setUploadError("");
    setAnalysisResult(null);

    if (!file) {
      return;
    }

    const isPdf =
      file.type === "application/pdf" ||
      file.name
        .toLowerCase()
        .endsWith(".pdf");

    if (!isPdf) {
      setSelectedFile(null);
      setUploadError(
        "Only PDF files are allowed."
      );
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setSelectedFile(null);
      setUploadError(
        "PDF size must be 10 MB or less."
      );
      return;
    }

    setSelectedFile(file);
  }

  function handleFileChange(event) {
    validateAndSelectFile(
      event.target.files?.[0]
    );
  }

  function handleDragOver(event) {
    event.preventDefault();
  }

  function handleDrop(event) {
    event.preventDefault();

    validateAndSelectFile(
      event.dataTransfer.files?.[0]
    );
  }

  function handleRemoveFile() {
    setSelectedFile(null);
    setAnalysisResult(null);
    setUploadError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  // =======================================================
  // ANALYZE
  // =======================================================

  async function handleAnalyzeDocument() {
    if (!selectedFile) {
      setUploadError(
        "Please select a PDF document first."
      );
      return;
    }

    if (!backendOnline) {
      setUploadError(
        "Backend is offline. Start the FastAPI server first."
      );
      return;
    }

    setUploading(true);
    setUploadError("");
    setAnalysisResult(null);

    try {
      const result =
        await uploadPdf(selectedFile);

      setAnalysisResult(result);

      await loadReports();
    } catch (error) {
      console.error(
        "Document analysis failed:",
        error
      );

      setUploadError(
        error?.message ||
          "Unable to analyze document."
      );
    } finally {
      setUploading(false);
    }
  }

  // =======================================================
  // RESULT HELPERS
  // =======================================================

  function getRequirementText(item) {
    return safeText(
      item?.requirement?.requirement ||
        item?.requirement?.requirement_text ||
        item?.requirement?.source_text,
      "Requirement"
    );
  }

  function getRequirementValue(item) {
    return safeText(
      item?.requirement?.value,
      "Not specified"
    );
  }

  function getRequirementCategory(item) {
    return cleanLabel(
      item?.requirement?.category ||
        item?.requirement?.type
    );
  }

  function getRequirementStatus(item) {
    return (
      item?.requirement?.status ||
      "clear"
    );
  }

  function getReviewFlags(item) {
    const flags = item?.review_flags;

    if (!flags) {
      return [];
    }

    if (Array.isArray(flags)) {
      return flags;
    }

    return [flags];
  }

  const reviewRequiredCount =
    reports.filter(
      (report) =>
        report?.document_status ===
          "REVIEW_REQUIRED" ||
        report?.status ===
          "REVIEW_REQUIRED"
    ).length;

  return (
    <div className="app">
      {/* =====================================================
          SIDEBAR
          ===================================================== */}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            P
          </div>

          <div>
            <h2>PROCURAI</h2>
            <p>Standards Intelligence</p>
          </div>
        </div>

        <nav className="nav-menu">
          <SidebarButton
            icon="⌂"
            label="Dashboard"
            active={activePage === "dashboard"}
            onClick={() =>
              setActivePage("dashboard")
            }
          />

          <SidebarButton
            icon="＋"
            label="Analyze Document"
            active={activePage === "analyze"}
            onClick={() =>
              setActivePage("analyze")
            }
          />

          <SidebarButton
            icon="▤"
            label="Reports"
            active={activePage === "reports"}
            onClick={() =>
              setActivePage("reports")
            }
          />

          <SidebarButton
            icon="◎"
            label="Standards"
            active={activePage === "standards"}
            onClick={() =>
              setActivePage("standards")
            }
          />
        </nav>

        <div className="sidebar-footer">
          <p>AI Procurement Intelligence</p>
          <span>PROCURAI v1.0</span>
        </div>
      </aside>

      {/* =====================================================
          MAIN
          ===================================================== */}

      <main className="main-content">
        <BackendHeader
          backendOnline={backendOnline}
          backendChecking={backendChecking}
          activePage={activePage}
        />

        {activePage === "dashboard" && (
          <DashboardPage
            reports={reports}
            standards={standards}
            reviewRequiredCount={
              reviewRequiredCount
            }
            setActivePage={
              setActivePage
            }
            handleViewReport={
              handleViewReport
            }
          />
        )}

        {activePage === "analyze" && (
          <AnalyzePage
            selectedFile={selectedFile}
            fileInputRef={fileInputRef}
            uploading={uploading}
            uploadError={uploadError}
            analysisResult={analysisResult}
            formatFileSize={formatFileSize}
            handleFileChange={handleFileChange}
            handleDragOver={handleDragOver}
            handleDrop={handleDrop}
            handleRemoveFile={handleRemoveFile}
            handleAnalyzeDocument={
              handleAnalyzeDocument
            }
            getRequirementText={
              getRequirementText
            }
            getRequirementValue={
              getRequirementValue
            }
            getRequirementCategory={
              getRequirementCategory
            }
            getRequirementStatus={
              getRequirementStatus
            }
            getReviewFlags={
              getReviewFlags
            }
          />
        )}

        {activePage === "reports" && (
          <ReportsPage
            reports={reports}
            loading={reportsLoading}
            error={reportsError}
            handleViewReport={
              handleViewReport
            }
            handleDownloadReport={
              handleDownloadReport
            }
            handleDeleteReport={
              handleDeleteReport
            }
          />
        )}

        {activePage === "standards" && (
          <StandardsPage
            standards={standards}
            loading={standardsLoading}
            error={standardsError}
          />
        )}
      </main>
    </div>
  );
}

// =========================================================
// SIDEBAR BUTTON
// =========================================================

function SidebarButton({
  icon,
  label,
  active,
  onClick,
}) {
  return (
    <button
      className={`nav-item ${
        active ? "active" : ""
      }`}
      onClick={onClick}
    >
      <span>{icon}</span>
      {label}
    </button>
  );
}

// =========================================================
// HEADER
// =========================================================

function BackendHeader({
  backendOnline,
  backendChecking,
  activePage,
}) {
  const pages = {
    dashboard: {
      label: "PROCUREMENT INTELLIGENCE",
      title: "Dashboard",
      subtitle:
        "Monitor analyses, review activity and available standards.",
    },

    analyze: {
      label: "AI DOCUMENT ANALYSIS",
      title: "Analyze Document",
      subtitle:
        "Upload procurement specifications and generate AI-assisted standard recommendations.",
    },

    reports: {
      label: "ANALYSIS HISTORY",
      title: "Reports",
      subtitle:
        "Search, inspect and manage previously processed procurement analyses.",
    },

    standards: {
      label: "STANDARDS DATASET",
      title: "Standards",
      subtitle:
        "View the standards currently available to the recommendation engine.",
    },
  };

  const current =
    pages[activePage] ||
    pages.dashboard;

  return (
    <header className="topbar">
      <div>
        <p className="page-label">
          {current.label}
        </p>

        <h1>
          {current.title}
        </h1>

        <p className="subtitle">
          {current.subtitle}
        </p>
      </div>

      <div
        className={`status-badge ${
          backendOnline
            ? "online"
            : "offline"
        }`}
      >
        <span className="status-dot" />

        {backendChecking
          ? "Checking Backend..."
          : backendOnline
            ? "Backend Connected"
            : "Backend Offline"}
      </div>
    </header>
  );
}

// =========================================================
// DASHBOARD
// =========================================================

function DashboardPage({
  reports,
  standards,
  reviewRequiredCount,
  setActivePage,
  handleViewReport,
}) {
  const recentReports =
    reports.slice(0, 3);

  return (
    <>
      <section className="stats-grid">
        <StatCard
          icon="📄"
          label="Total Analyses"
          value={reports.length}
          description="Saved analysis reports"
        />

        <StatCard
          icon="⚠"
          label="Review Required"
          value={reviewRequiredCount}
          description="Need human verification"
        />

        <StatCard
          icon="✓"
          label="Test Standards"
          value={standards.length}
          description="Prototype dataset records"
        />

        <StatCard
          icon="AI"
          label="Matching Engine"
          value="Hybrid AI"
          description="Keyword + Semantic"
          small
        />
      </section>

      <section className="dashboard-grid">
        <div className="upload-card">
          <p className="small-label">
            QUICK ACTION
          </p>

          <h2>
            Analyze New Procurement Document
          </h2>

          <div className="upload-zone">
            <div className="upload-icon">
              ⇧
            </div>

            <h3>
              Start a new analysis
            </h3>

            <p>
              Upload a procurement PDF and let
              PROCURAI extract technical
              requirements, detect OCR needs and
              recommend candidate standards.
            </p>

            <button
              className="primary-button"
              onClick={() =>
                setActivePage("analyze")
              }
            >
              Analyze Document
            </button>
          </div>
        </div>

        <div className="workflow-card">
          <p className="small-label">
            AI WORKFLOW
          </p>

          <h2>
            How PROCURAI Works
          </h2>

          <div className="workflow-list">
            <WorkflowItem
              number="01"
              title="Document Extraction"
              text="Native text extraction with automatic OCR fallback."
            />

            <WorkflowItem
              number="02"
              title="Requirement Analysis"
              text="Technical procurement requirements are identified and structured."
            />

            <WorkflowItem
              number="03"
              title="Hybrid AI Matching"
              text="Keyword and semantic similarity scores are combined."
            />

            <WorkflowItem
              number="04"
              title="Explainable Review"
              text="Confidence, evidence and human-review flags are generated."
            />
          </div>
        </div>
      </section>

      <section className="recent-section">
        <div className="section-heading">
          <div>
            <p className="small-label">
              HISTORY
            </p>

            <h2>
              Recent Analyses
            </h2>
          </div>

          <button
            className="secondary-button"
            onClick={() =>
              setActivePage("reports")
            }
          >
            View All Reports
          </button>
        </div>

        {recentReports.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              ▤
            </div>

            <h3>
              No reports available
            </h3>

            <p>
              Analyze your first procurement
              document to create a report.
            </p>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gap: "14px",
              marginTop: "22px",
            }}
          >
            {recentReports.map(
              (report, index) => (
                <RecentReportCard
                  key={
                    report?.analysis_id ||
                    index
                  }
                  report={report}
                  onView={() =>
                    handleViewReport(
                      report?.analysis_id
                    )
                  }
                />
              )
            )}
          </div>
        )}
      </section>
    </>
  );
}

function RecentReportCard({
  report,
  onView,
}) {
  return (
    <div
      className="stat-card"
      style={{
        alignItems: "flex-start",
      }}
    >
      <div className="stat-icon">
        📄
      </div>

      <div
        style={{
          minWidth: 0,
          flex: 1,
        }}
      >
        <p className="small-label">
          RECENT ANALYSIS
        </p>

        <h3
          className="engine-text"
          style={{
            marginBottom: "8px",
          }}
        >
          {safeText(
            report?.filename,
            "Procurement Analysis"
          )}
        </h3>

        <div
          style={{
            display: "flex",
            gap: "8px",
            flexWrap: "wrap",
            marginBottom: "10px",
          }}
        >
          <Badge
            text={cleanLabel(
              report?.document_status ||
                report?.status
            )}
            type={getStatusType(
              report?.document_status ||
                report?.status
            )}
          />

          <Badge
            text={`${getRequirementCount(
              report
            )} Requirements`}
            type="info"
          />

          <Badge
            text={getOcrLabel(report)}
            type="neutral"
          />
        </div>

        <span>
          {formatDateTime(
            getReportDate(report)
          )}
        </span>
      </div>

      <button
        className="secondary-button"
        onClick={onView}
      >
        View
      </button>
    </div>
  );
}

// =========================================================
// ANALYZE PAGE
// =========================================================

function AnalyzePage({
  selectedFile,
  fileInputRef,
  uploading,
  uploadError,
  analysisResult,
  formatFileSize,
  handleFileChange,
  handleDragOver,
  handleDrop,
  handleRemoveFile,
  handleAnalyzeDocument,
  getRequirementText,
  getRequirementValue,
  getRequirementCategory,
  getRequirementStatus,
  getReviewFlags,
}) {
  return (
    <>
      <section className="dashboard-grid">
        <div className="upload-card">
          <p className="small-label">
            NEW ANALYSIS
          </p>

          <h2>
            Upload Procurement PDF
          </h2>

          <div
            className="upload-zone"
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              style={{
                display: "none",
              }}
            />

            {!selectedFile ? (
              <>
                <div className="upload-icon">
                  ⇧
                </div>

                <h3>
                  Upload procurement specification
                </h3>

                <p>
                  Drag and drop your PDF or select
                  a document from your computer.
                </p>

                <button
                  className="primary-button"
                  onClick={() =>
                    fileInputRef.current?.click()
                  }
                >
                  Select PDF Document
                </button>

                <span className="upload-note">
                  PDF only • Maximum 10 MB
                </span>
              </>
            ) : (
              <>
                <div className="upload-icon">
                  ✓
                </div>

                <h3>
                  Document Selected
                </h3>

                <p>
                  <strong>
                    {selectedFile.name}
                  </strong>
                </p>

                <span className="upload-note">
                  {formatFileSize(
                    selectedFile.size
                  )}
                </span>

                <div
                  style={{
                    display: "flex",
                    gap: "12px",
                    marginTop: "20px",
                    flexWrap: "wrap",
                    justifyContent: "center",
                  }}
                >
                  <button
                    className="secondary-button"
                    disabled={uploading}
                    onClick={() =>
                      fileInputRef.current?.click()
                    }
                  >
                    Change PDF
                  </button>

                  <button
                    className="secondary-button"
                    disabled={uploading}
                    onClick={handleRemoveFile}
                  >
                    Remove
                  </button>

                  <button
                    className="primary-button"
                    disabled={uploading}
                    onClick={
                      handleAnalyzeDocument
                    }
                  >
                    {uploading
                      ? "Analyzing..."
                      : "Analyze Document"}
                  </button>
                </div>
              </>
            )}

            {uploadError && (
              <p
                style={{
                  color: "#c0392b",
                  fontWeight: "700",
                  marginTop: "18px",
                }}
              >
                {uploadError}
              </p>
            )}

            {uploading && (
              <p
                style={{
                  color: "#53657d",
                  marginTop: "18px",
                }}
              >
                Extracting text, checking OCR,
                identifying requirements and
                matching standards...
              </p>
            )}
          </div>
        </div>

        <div className="workflow-card">
          <p className="small-label">
            PROCESS
          </p>

          <h2>
            Analysis Pipeline
          </h2>

          <div className="workflow-list">
            <WorkflowItem
              number="01"
              title="PDF Extraction"
              text="Extract native text and identify scanned pages."
            />

            <WorkflowItem
              number="02"
              title="OCR Fallback"
              text="Tesseract processes image-based pages when needed."
            />

            <WorkflowItem
              number="03"
              title="Requirement Extraction"
              text="Technical requirements are converted into structured data."
            />

            <WorkflowItem
              number="04"
              title="Hybrid Matching"
              text="Keyword and semantic AI scores identify candidate standards."
            />
          </div>
        </div>
      </section>

      {analysisResult && (
        <AnalysisResults
          analysisResult={
            analysisResult
          }
          selectedFile={selectedFile}
          getRequirementText={
            getRequirementText
          }
          getRequirementValue={
            getRequirementValue
          }
          getRequirementCategory={
            getRequirementCategory
          }
          getRequirementStatus={
            getRequirementStatus
          }
          getReviewFlags={
            getReviewFlags
          }
        />
      )}
    </>
  );
}

// =========================================================
// ANALYSIS RESULTS
// =========================================================

function AnalysisResults({
  analysisResult,
  selectedFile,
  getRequirementText,
  getRequirementValue,
  getRequirementCategory,
  getRequirementStatus,
  getReviewFlags,
}) {
  return (
    <>
      <section className="recent-section">
        <div className="section-heading">
          <div>
            <p className="small-label">
              ANALYSIS COMPLETE
            </p>

            <h2>
              Document Analysis Summary
            </h2>
          </div>

          <Badge
            text={cleanLabel(
              analysisResult?.document_status ||
                analysisResult?.status
            )}
            type={getStatusType(
              analysisResult?.document_status ||
                analysisResult?.status
            )}
          />
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "16px",
            marginTop: "22px",
          }}
        >
          <ResultSummaryCard
            label="Document"
            value={
              analysisResult?.filename ||
              selectedFile?.name
            }
            small
          />

          <ResultSummaryCard
            label="Total Pages"
            value={
              analysisResult?.total_pages ??
              "-"
            }
          />

          <ResultSummaryCard
            label="Requirements"
            value={
              analysisResult?.results?.length ??
              0
            }
          />

          <ResultSummaryCard
            label="OCR Used"
            value={
              analysisResult?.ocr_used
                ? "Yes"
                : "No"
            }
            small
          />

          <ResultSummaryCard
            label="OCR Confidence"
            value={
              analysisResult?.ocr_used
                ? formatScore(
                    analysisResult?.ocr_confidence
                  )
                : "Not Required"
            }
            small
          />

          <ResultSummaryCard
            label="Extraction Mode"
            value={cleanLabel(
              analysisResult?.extraction_mode
            )}
            small
          />

          <ResultSummaryCard
            label="Matcher"
            value={
              analysisResult?.matching_engine ||
              "Hybrid AI"
            }
            small
          />
        </div>
      </section>

      <section
        className="recent-section"
        style={{
          marginTop: "24px",
        }}
      >
        <div className="section-heading">
          <div>
            <p className="small-label">
              TRACEABLE RESULTS
            </p>

            <h2>
              Requirement → Standard Mapping
            </h2>

            <p className="subtitle">
              Each requirement is mapped to its
              strongest candidate standard with
              confidence, evidence and review
              information.
            </p>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "20px",
            marginTop: "24px",
          }}
        >
          {analysisResult?.results?.map(
            (item, index) => (
              <RequirementCard
                key={
                  item?.requirement?.id ||
                  index
                }
                item={item}
                index={index}
                getRequirementText={
                  getRequirementText
                }
                getRequirementValue={
                  getRequirementValue
                }
                getRequirementCategory={
                  getRequirementCategory
                }
                getRequirementStatus={
                  getRequirementStatus
                }
                getReviewFlags={
                  getReviewFlags
                }
              />
            )
          )}
        </div>
      </section>
    </>
  );
}

// =========================================================
// REQUIREMENT CARD
// =========================================================

function RequirementCard({
  item,
  index,
  getRequirementText,
  getRequirementValue,
  getRequirementCategory,
  getRequirementStatus,
  getReviewFlags,
}) {
  const bestMatch =
    item?.best_match;

  const status =
    getRequirementStatus(item);

  const reviewFlags =
    getReviewFlags(item);

  const topCandidates =
    Array.isArray(item?.all_matches) &&
    item.all_matches.length > 0
      ? item.all_matches.slice(0, 3)
      : bestMatch
        ? [bestMatch]
        : [];

  return (
    <div
      style={{
        border: "1px solid #e2e8f2",
        borderRadius: "18px",
        overflow: "hidden",
        background: "#ffffff",
        boxShadow:
          "0 8px 25px rgba(31,45,75,0.05)",
      }}
    >
      <div
        style={{
          padding: "20px 22px",
          background: "#f8faff",
          borderBottom:
            "1px solid #e8edf5",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent:
              "space-between",
            gap: "18px",
            flexWrap: "wrap",
          }}
        >
          <div
            style={{
              flex: 1,
              minWidth: "230px",
            }}
          >
            <p className="small-label">
              REQUIREMENT {index + 1}
            </p>

            <h3
              style={{
                margin: "5px 0 8px",
                color: "#17233d",
                fontSize: "18px",
              }}
            >
              {getRequirementText(item)}
            </h3>

            <p
              style={{
                margin: 0,
                color: "#66738b",
              }}
            >
              Value:{" "}
              <strong>
                {getRequirementValue(item)}
              </strong>
            </p>
          </div>

          <div
            style={{
              display: "flex",
              gap: "10px",
              flexWrap: "wrap",
              alignItems: "flex-start",
            }}
          >
            <Badge
              text={getRequirementCategory(
                item
              )}
              type="info"
            />

            <Badge
              text={cleanLabel(status)}
              type={
                status ===
                "needs_clarification"
                  ? "warning"
                  : "success"
              }
            />
          </div>
        </div>
      </div>

      <div
        style={{
          padding: "22px",
        }}
      >
        {bestMatch ? (
          <>
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "minmax(0, 1.5fr) minmax(210px, 0.5fr)",
                gap: "20px",
              }}
            >
              <div>
                <p className="small-label">
                  RECOMMENDED STANDARD
                </p>

                <h3
                  style={{
                    margin: "5px 0 7px",
                    color: "#17233d",
                    fontSize: "19px",
                  }}
                >
                  {safeText(
                    bestMatch?.standard_number ||
                      bestMatch?.standard_id,
                    "Standard"
                  )}
                </h3>

                <p
                  style={{
                    margin:
                      "0 0 14px",
                    color: "#66738b",
                    lineHeight: 1.6,
                  }}
                >
                  {safeText(
                    bestMatch?.title,
                    "Standard title unavailable"
                  )}
                </p>

                <div
                  style={{
                    display: "flex",
                    gap: "10px",
                    flexWrap: "wrap",
                  }}
                >
                  <Badge
                    text={`Confidence: ${cleanLabel(
                      bestMatch?.confidence_level
                    )}`}
                    type="info"
                  />

                  <Badge
                    text={
                      bestMatch?.verified
                        ? "Verified Source"
                        : "Test Dataset"
                    }
                    type={
                      bestMatch?.verified
                        ? "success"
                        : "warning"
                    }
                  />

                  {bestMatch?.needs_human_review && (
                    <Badge
                      text="Human Review"
                      type="warning"
                    />
                  )}
                </div>
              </div>

              <div
                style={{
                  padding: "18px",
                  background:
                    "#f6f8ff",
                  border:
                    "1px solid #dde5fb",
                  borderRadius:
                    "15px",
                }}
              >
                <p className="small-label">
                  HYBRID MATCH SCORE
                </p>

                <div
                  style={{
                    fontSize: "31px",
                    fontWeight: "800",
                    color: "#4c6be7",
                    marginTop: "5px",
                  }}
                >
                  {formatScore(
                    bestMatch?.hybrid_score ??
                      bestMatch?.match_score ??
                      bestMatch?.confidence
                  )}
                </div>

                <div
                  style={{
                    marginTop: "13px",
                    color: "#66738b",
                    fontSize: "12px",
                    lineHeight: 1.8,
                  }}
                >
                  <div>
                    Keyword:{" "}
                    <strong>
                      {formatScore(
                        bestMatch?.keyword_score
                      )}
                    </strong>
                  </div>

                  <div>
                    Semantic:{" "}
                    <strong>
                      {formatScore(
                        bestMatch?.semantic_score
                      )}
                    </strong>
                  </div>
                </div>
              </div>
            </div>

            <EvidenceBox
              evidence={
                bestMatch?.evidence
              }
              bestMatch={bestMatch}
              decisionReason={
                item?.decision_reason
              }
            />

            {topCandidates.length > 0 && (
              <div
                style={{
                  marginTop: "20px",
                  padding: "18px",
                  border:
                    "1px solid #e4e9f3",
                  borderRadius: "15px",
                  background: "#fbfcff",
                }}
              >
                <div
                  style={{
                    marginBottom: "15px",
                  }}
                >
                  <p className="small-label">
                    TOP CANDIDATE STANDARDS
                  </p>

                  <p
                    style={{
                      margin: "5px 0 0",
                      color: "#6b7890",
                      fontSize: "12px",
                      lineHeight: 1.6,
                    }}
                  >
                    Ranked by hybrid keyword and
                    semantic similarity. Official
                    source verification is shown
                    separately from relevance.
                  </p>
                </div>

                <div
                  style={{
                    display: "grid",
                    gap: "12px",
                  }}
                >
                  {topCandidates.map(
                    (candidate, candidateIndex) => (
                      <div
                        key={
                          candidate?.traceability_id ||
                          candidate?.standard_id ||
                          candidateIndex
                        }
                        style={{
                          display: "flex",
                          justifyContent:
                            "space-between",
                          alignItems: "center",
                          gap: "16px",
                          padding: "14px 16px",
                          border:
                            candidateIndex === 0
                              ? "1px solid #cfdafe"
                              : "1px solid #e6eaf1",
                          borderRadius: "13px",
                          background:
                            candidateIndex === 0
                              ? "#f5f7ff"
                              : "#ffffff",
                          flexWrap: "wrap",
                        }}
                      >
                        <div
                          style={{
                            flex: 1,
                            minWidth: "220px",
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                              flexWrap: "wrap",
                              marginBottom: "6px",
                            }}
                          >
                            <Badge
                              text={`#${candidateIndex + 1}`}
                              type={
                                candidateIndex === 0
                                  ? "info"
                                  : "neutral"
                              }
                            />

                            <strong
                              style={{
                                color: "#24324a",
                              }}
                            >
                              {safeText(
                                candidate?.standard_number ||
                                  candidate?.standard_id,
                                "Standard"
                              )}
                            </strong>

                            {candidate?.verified ? (
                              <Badge
                                text="Verified BIS"
                                type="success"
                              />
                            ) : (
                              <Badge
                                text="Synthetic"
                                type="warning"
                              />
                            )}
                          </div>

                          <p
                            style={{
                              margin: 0,
                              color: "#66738b",
                              fontSize: "12px",
                              lineHeight: 1.55,
                            }}
                          >
                            {safeText(
                              candidate?.title,
                              "Standard title unavailable"
                            )}
                          </p>

                          <p
                            style={{
                              margin:
                                "6px 0 0",
                              color: "#8993a5",
                              fontSize: "11px",
                            }}
                          >
                            Source:{" "}
                            <strong>
                              {safeText(
                                candidate?.source_name,
                                candidate?.verified
                                  ? "Bureau of Indian Standards"
                                  : "Synthetic Test Dataset"
                              )}
                            </strong>
                          </p>
                        </div>

                        <div
                          style={{
                            textAlign: "right",
                            minWidth: "100px",
                          }}
                        >
                          <p
                            className="small-label"
                            style={{
                              marginBottom: "4px",
                            }}
                          >
                            MATCH SCORE
                          </p>

                          <strong
                            style={{
                              fontSize: "20px",
                              color:
                                candidateIndex === 0
                                  ? "#4c6be7"
                                  : "#36445d",
                            }}
                          >
                            {formatScore(
                              candidate?.hybrid_score ??
                                candidate?.confidence ??
                                candidate?.match_score
                            )}
                          </strong>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </>
        ) : (
          <InfoBox
            title="Standard Match"
            value="No suitable standard match was found."
          />
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "14px",
            marginTop: "18px",
          }}
        >
          <InfoBox
            title="Decision"
            value={cleanLabel(
              item?.decision
            )}
          />

          <InfoBox
            title="Review Priority"
            value={cleanLabel(
              item?.review_priority
            )}
          />

          <InfoBox
            title="Recommended Action"
            value={safeText(
              item?.recommended_action,
              "No additional action"
            )}
          />
        </div>

        {reviewFlags.length > 0 && (
          <div
            style={{
              marginTop: "18px",
            }}
          >
            <p className="small-label">
              REVIEW FLAGS
            </p>

            <div
              style={{
                display: "flex",
                gap: "10px",
                flexWrap: "wrap",
              }}
            >
              {reviewFlags.map(
                (flag, flagIndex) => (
                  <Badge
                    key={flagIndex}
                    text={cleanLabel(flag)}
                    type="warning"
                  />
                )
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// =========================================================
// EVIDENCE
// =========================================================

function EvidenceBox({
  evidence,
  bestMatch,
  decisionReason,
}) {
  const isObject =
    evidence &&
    typeof evidence === "object" &&
    !Array.isArray(evidence);

  const keywords =
    isObject
      ? evidence?.matched_keywords
      : bestMatch?.matched_keywords;

  return (
    <div
      style={{
        marginTop: "20px",
        padding: "18px",
        borderRadius: "14px",
        background: "#f9fafc",
        border: "1px solid #edf0f5",
      }}
    >
      <p className="small-label">
        EVIDENCE & EXPLANATION
      </p>

      {isObject ? (
        <>
          <EvidenceRow
            label="Requirement"
            value={
              evidence?.requirement_text
            }
          />

          <EvidenceRow
            label="Standard Evidence"
            value={
              evidence?.standard_text
            }
          />

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(150px, 1fr))",
              gap: "12px",
              marginTop: "16px",
            }}
          >
            <MiniMetric
              label="Keyword Score"
              value={formatScore(
                evidence?.keyword_score
              )}
            />

            <MiniMetric
              label="Semantic Score"
              value={formatScore(
                evidence?.semantic_score
              )}
            />

            <MiniMetric
              label="Hybrid Score"
              value={formatScore(
                evidence?.hybrid_score
              )}
            />
          </div>
        </>
      ) : (
        <p
          style={{
            margin: "8px 0 0",
            color: "#56647d",
          }}
        >
          {safeText(
            evidence ||
              decisionReason,
            "No evidence available."
          )}
        </p>
      )}

      {Array.isArray(keywords) &&
        keywords.length > 0 && (
          <div
            style={{
              marginTop: "16px",
            }}
          >
            <p className="small-label">
              MATCHED KEYWORDS
            </p>

            <div
              style={{
                display: "flex",
                gap: "10px",
                flexWrap: "wrap",
              }}
            >
              {keywords.map(
                (keyword, index) => (
                  <Badge
                    key={index}
                    text={safeText(keyword)}
                    type="neutral"
                  />
                )
              )}
            </div>
          </div>
        )}
    </div>
  );
}

// =========================================================
// REPORTS PAGE
// =========================================================

function ReportsPage({
  reports,
  loading,
  error,
  handleViewReport,
  handleDownloadReport,
  handleDeleteReport,
}) {
  const [search, setSearch] =
    useState("");

  const [statusFilter, setStatusFilter] =
    useState("ALL");

  const [currentPage, setCurrentPage] =
    useState(1);

  const filteredReports =
    useMemo(() => {
      return reports.filter(
        (report) => {
          const filename =
            safeText(
              report?.filename,
              ""
            ).toLowerCase();

          const status =
            String(
              report?.document_status ||
                report?.status ||
                ""
            ).toUpperCase();

          const matchesSearch =
            filename.includes(
              search
                .trim()
                .toLowerCase()
            );

          const matchesStatus =
            statusFilter === "ALL" ||
            status === statusFilter;

          return (
            matchesSearch &&
            matchesStatus
          );
        }
      );
    }, [
      reports,
      search,
      statusFilter,
    ]);

  useEffect(() => {
    setCurrentPage(1);
  }, [search, statusFilter]);

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        filteredReports.length /
          REPORTS_PER_PAGE
      )
    );

  const start =
    (currentPage - 1) *
    REPORTS_PER_PAGE;

  const visibleReports =
    filteredReports.slice(
      start,
      start + REPORTS_PER_PAGE
    );

  return (
    <section className="recent-section">
      <div className="section-heading">
        <div>
          <p className="small-label">
            SAVED ANALYSES
          </p>

          <h2>
            Report History
          </h2>
        </div>

        <Badge
          text={`${reports.length} Total Reports`}
          type="info"
        />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "minmax(220px, 1fr) minmax(180px, 240px)",
          gap: "12px",
          marginTop: "22px",
        }}
      >
        <input
          type="text"
          placeholder="Search by document name..."
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value
            )
          }
          style={inputStyle}
        />

        <select
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(
              event.target.value
            )
          }
          style={inputStyle}
        >
          <option value="ALL">
            All Statuses
          </option>

          <option value="READY">
            Ready
          </option>

          <option value="REVIEW_REQUIRED">
            Review Required
          </option>

          <option value="INCOMPLETE_MATCHING">
            Incomplete Matching
          </option>
        </select>
      </div>

      {loading && (
        <div className="empty-state">
          <h3>
            Loading reports...
          </h3>
        </div>
      )}

      {error && !loading && (
        <div className="empty-state">
          <h3>
            Unable to load reports
          </h3>

          <p>{error}</p>
        </div>
      )}

      {!loading &&
        !error &&
        visibleReports.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">
              ▤
            </div>

            <h3>
              No matching reports
            </h3>

            <p>
              Change your search or status
              filter.
            </p>
          </div>
        )}

      {!loading &&
        !error &&
        visibleReports.length > 0 && (
          <>
            <div
              style={{
                display: "grid",
                gap: "15px",
                marginTop: "22px",
              }}
            >
              {visibleReports.map(
                (report, index) => (
                  <ReportCard
                    key={
                      report?.analysis_id ||
                      index
                    }
                    report={report}
                    onView={() =>
                      handleViewReport(
                        report?.analysis_id
                      )
                    }
                    onDownload={() =>
                      handleDownloadReport(
                        report?.analysis_id
                      )
                    }
                    onDelete={() =>
                      handleDeleteReport(
                        report?.analysis_id
                      )
                    }
                  />
                )
              )}
            </div>

            <div
              style={{
                marginTop: "22px",
                display: "flex",
                justifyContent:
                  "space-between",
                alignItems: "center",
                gap: "12px",
                flexWrap: "wrap",
              }}
            >
              <span
                style={{
                  fontSize: "12px",
                  color: "#7b879b",
                }}
              >
                Showing{" "}
                {start + 1}–
                {Math.min(
                  start +
                    REPORTS_PER_PAGE,
                  filteredReports.length
                )}{" "}
                of{" "}
                {
                  filteredReports.length
                }{" "}
                reports
              </span>

              <div
                style={{
                  display: "flex",
                  gap: "10px",
                }}
              >
                <button
                  className="secondary-button"
                  disabled={
                    currentPage === 1
                  }
                  onClick={() =>
                    setCurrentPage(
                      (page) =>
                        Math.max(
                          1,
                          page - 1
                        )
                    )
                  }
                >
                  Previous
                </button>

                <Badge
                  text={`Page ${currentPage} of ${totalPages}`}
                  type="neutral"
                />

                <button
                  className="secondary-button"
                  disabled={
                    currentPage >=
                    totalPages
                  }
                  onClick={() =>
                    setCurrentPage(
                      (page) =>
                        Math.min(
                          totalPages,
                          page + 1
                        )
                    )
                  }
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
    </section>
  );
}

function ReportCard({
  report,
  onView,
  onDownload,
  onDelete,
}) {
  const status =
    report?.document_status ||
    report?.status;

  return (
    <div
      className="stat-card"
      style={{
        alignItems: "flex-start",
      }}
    >
      <div className="stat-icon">
        📄
      </div>

      <div
        style={{
          flex: 1,
          minWidth: 0,
        }}
      >
        <p className="small-label">
          DOCUMENT
        </p>

        <h3
          className="engine-text"
          style={{
            marginBottom: "10px",
          }}
        >
          {safeText(
            report?.filename,
            "Procurement Analysis"
          )}
        </h3>

        <div
          style={{
            display: "flex",
            gap: "9px",
            flexWrap: "wrap",
            marginBottom: "11px",
          }}
        >
          <Badge
            text={cleanLabel(status)}
            type={getStatusType(status)}
          />

          <Badge
            text={`${getRequirementCount(
              report
            )} Requirements`}
            type="info"
          />

          <Badge
            text={getOcrLabel(report)}
            type="neutral"
          />
        </div>

        <span>
          {formatDateTime(
            getReportDate(report)
          )}
        </span>
      </div>

      <div
        style={{
          display: "flex",
          gap: "10px",
          flexWrap: "wrap",
        }}
      >
        <button
          className="primary-button"
          onClick={onView}
        >
          View Report
        </button>
        <button
    className="secondary-button"
    onClick={onDownload}
  >
    Download PDF
  </button>

        <button
          className="secondary-button"
          onClick={onDelete}
          style={{
            color: "#b34444",
          }}
        >
          Delete
        </button>
      </div>
    </div>
  );
}

// =========================================================
// STANDARDS PAGE
// =========================================================

function StandardsPage({
  standards,
  loading,
  error,
}) {
  const [search, setSearch] =
    useState("");

  const filteredStandards =
    standards.filter(
      (standard) => {
        const searchable =
          `${safeText(
            standard?.standard_number ||
              standard?.standard_id,
            ""
          )} ${safeText(
            standard?.title,
            ""
          )}`.toLowerCase();

        return searchable.includes(
          search
            .trim()
            .toLowerCase()
        );
      }
    );

  function openBisVerificationPortal() {
    window.open(
      "https://standards.bis.gov.in/",
      "_blank",
      "noopener,noreferrer"
    );
  }

  return (
    <section className="recent-section">
      <div className="section-heading">
        <div>
          <p className="small-label">
            CURRENT DATASET
          </p>

          <h2>
            Available Test Standards
          </h2>

          <p className="subtitle">
            Current prototype uses synthetic
            test standards for development and
            demonstration. These are not
            authoritative BIS records.
          </p>
        </div>

        <Badge
          text={`${standards.length} Test Records`}
          type="warning"
        />
      </div>

      <div
        style={{
          marginTop: "22px",
          padding: "22px",
          borderRadius: "16px",
          border: "1px solid #dce5f5",
          background: "#f8faff",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "20px",
          flexWrap: "wrap",
        }}
      >
        <div
          style={{
            flex: 1,
            minWidth: "260px",
          }}
        >
          <p className="small-label">
            OFFICIAL VERIFICATION SOURCE
          </p>

          <h3
            style={{
              margin: "5px 0 8px",
              fontSize: "18px",
            }}
          >
            Bureau of Indian Standards (BIS)
          </h3>

          <p
            className="subtitle"
            style={{
              margin: 0,
              maxWidth: "720px",
            }}
          >
            PROCURAI currently uses synthetic
            test records for AI matching.
            Final standard applicability should
            be verified using the official
            Bureau of Indian Standards source
            before procurement or compliance
            acceptance.
          </p>

          <div
            style={{
              display: "flex",
              gap: "8px",
              flexWrap: "wrap",
              marginTop: "14px",
            }}
          >
            <Badge
              text="AI Recommendation"
              type="info"
            />

            <Badge
              text="Human Verification Required"
              type="warning"
            />

            <Badge
              text="Official Source: BIS"
              type="success"
            />
          </div>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={openBisVerificationPortal}
        >
          Open BIS Verification Portal
        </button>
      </div>

      <div
        style={{
          marginTop: "22px",
          maxWidth: "460px",
        }}
      >
        <input
          type="text"
          placeholder="Search standard number or title..."
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value
            )
          }
          style={inputStyle}
        />
      </div>

      {loading && (
        <div className="empty-state">
          <h3>
            Loading standards...
          </h3>
        </div>
      )}

      {error && !loading && (
        <div className="empty-state">
          <h3>
            Unable to load standards
          </h3>

          <p>{error}</p>
        </div>
      )}

      {!loading &&
        !error &&
        filteredStandards.length ===
          0 && (
          <div className="empty-state">
            <h3>
              No matching standards
            </h3>

            <p>
              Try another search term.
            </p>
          </div>
        )}

      {!loading &&
        !error &&
        filteredStandards.length >
          0 && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "18px",
              marginTop: "22px",
            }}
          >
            {filteredStandards.map(
              (standard, index) => (
                <StandardCard
                  key={
                    standard?.id ||
                    standard?.standard_id ||
                    index
                  }
                  standard={standard}
                />
              )
            )}
          </div>
        )}
    </section>
  );
}

function StandardCard({
  standard,
}) {
  return (
    <div
      className="stat-card"
      style={{
        alignItems: "flex-start",
        minHeight: "180px",
      }}
    >
      <div className="stat-icon">
        ◎
      </div>

      <div
        style={{
          minWidth: 0,
          flex: 1,
        }}
      >
        <p className="small-label">
          {safeText(
            standard?.standard_number ||
              standard?.standard_id,
            "STANDARD"
          )}
        </p>

        <h3
          className="engine-text"
          style={{
            fontSize: "18px",
            lineHeight: 1.45,
          }}
        >
          {safeText(
            standard?.title,
            "Untitled Standard"
          )}
        </h3>

        <p
          style={{
            margin: "10px 0",
            color: "#758299",
            fontSize: "12px",
          }}
        >
          Source:{" "}
          <strong>
            {safeText(
              standard?.source_name,
              "Synthetic Test Dataset"
            )}
          </strong>
        </p>

        <Badge
          text={
            standard?.verified
              ? "Verified Source"
              : "Synthetic Test Dataset"
          }
          type={
            standard?.verified
              ? "success"
              : "warning"
          }
        />
      </div>
    </div>
  );
}

// =========================================================
// SMALL COMPONENTS
// =========================================================

function StatCard({
  icon,
  label,
  value,
  description,
  small = false,
}) {
  return (
    <div className="stat-card">
      <div className="stat-icon">
        {icon}
      </div>

      <div
        style={{
          minWidth: 0,
        }}
      >
        <p>{label}</p>

        <h3
          className={
            small
              ? "engine-text"
              : ""
          }
        >
          {safeText(value)}
        </h3>

        <span>{description}</span>
      </div>
    </div>
  );
}

function WorkflowItem({
  number,
  title,
  text,
}) {
  return (
    <div className="workflow-item">
      <div className="step-number">
        {number}
      </div>

      <div>
        <h4>{title}</h4>
        <p>{text}</p>
      </div>
    </div>
  );
}

function ResultSummaryCard({
  label,
  value,
  small = false,
}) {
  return (
    <div className="stat-card">
      <div
        style={{
          minWidth: 0,
          width: "100%",
        }}
      >
        <p>{label}</p>

        <h3
          style={{
            fontSize:
              small
                ? "16px"
                : "26px",
            overflowWrap: "anywhere",
          }}
        >
          {safeText(value)}
        </h3>
      </div>
    </div>
  );
}

function InfoBox({
  title,
  value,
}) {
  return (
    <div
      style={{
        padding: "15px",
        borderRadius: "13px",
        border:
          "1px solid #e7ebf2",
        background: "#fbfcfe",
      }}
    >
      <p className="small-label">
        {title}
      </p>

      <p
        style={{
          margin: 0,
          fontWeight: "600",
          color: "#263550",
          lineHeight: 1.6,
        }}
      >
        {safeText(value)}
      </p>
    </div>
  );
}

function EvidenceRow({
  label,
  value,
}) {
  if (!value) {
    return null;
  }

  return (
    <div
      style={{
        marginTop: "13px",
      }}
    >
      <strong
        style={{
          display: "block",
          marginBottom: "5px",
          fontSize: "12px",
          color: "#384661",
        }}
      >
        {label}
      </strong>

      <p
        style={{
          margin: 0,
          color: "#56647d",
          lineHeight: 1.7,
        }}
      >
        {safeText(value)}
      </p>
    </div>
  );
}

function MiniMetric({
  label,
  value,
}) {
  return (
    <div
      style={{
        background: "#ffffff",
        border:
          "1px solid #e7ebf2",
        borderRadius: "11px",
        padding: "12px",
      }}
    >
      <p
        style={{
          margin: "0 0 5px",
          fontSize: "10px",
          fontWeight: "800",
          color: "#7a879d",
          letterSpacing: "0.5px",
        }}
      >
        {label}
      </p>

      <strong
        style={{
          color: "#344563",
          fontSize: "14px",
        }}
      >
        {value}
      </strong>
    </div>
  );
}

function Badge({
  text,
  type = "neutral",
}) {
  const styles = {
    success: {
      background: "#eaf8ef",
      border: "#cbeed6",
      color: "#247844",
    },

    warning: {
      background: "#fff7e8",
      border: "#f1dfb5",
      color: "#946b1e",
    },

    info: {
      background: "#eef3ff",
      border: "#d8e2ff",
      color: "#4964bd",
    },

    neutral: {
      background: "#f3f5f8",
      border: "#e1e5ec",
      color: "#596579",
    },
  };

  const current =
    styles[type] ||
    styles.neutral;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "6px 10px",
        margin: "2px",
        borderRadius: "999px",
        background:
          current.background,
        border:
          `1px solid ${current.border}`,
        color: current.color,
        fontSize: "11px",
        fontWeight: "700",
        lineHeight: 1.2,
      }}
    >
      {safeText(text)}
    </span>
  );
}

const inputStyle = {
  width: "100%",
  minHeight: "44px",
  padding: "10px 13px",
  border: "1px solid #dbe3ef",
  borderRadius: "11px",
  background: "#ffffff",
  color: "#25324a",
  outline: "none",
};

export default App;