const API_BASE_URL = "http://127.0.0.1:8001";

async function handleResponse(response) {
  if (!response.ok) {
    let message = "Something went wrong";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        message = errorData.detail;
      }
    } catch {
      message = `Request failed with status ${response.status}`;
    }

    throw new Error(message);
  }

  return response.json();
}


// =========================================================
// BACKEND STATUS
// =========================================================

export async function checkBackendStatus() {
  const response = await fetch(`${API_BASE_URL}/`);
  return handleResponse(response);
}


// =========================================================
// STANDARDS
// =========================================================

export async function getStandards() {
  const response = await fetch(`${API_BASE_URL}/standards`);
  return handleResponse(response);
}


// =========================================================
// REPORTS
// =========================================================

export async function getReports() {
  const response = await fetch(`${API_BASE_URL}/reports`);
  return handleResponse(response);
}


export async function getReport(analysisId) {
  const response = await fetch(
    `${API_BASE_URL}/reports/${analysisId}`
  );

  return handleResponse(response);
}


export async function deleteReport(analysisId) {
  const response = await fetch(
    `${API_BASE_URL}/reports/${analysisId}`,
    {
      method: "DELETE",
    }
  );

  return handleResponse(response);
}


// =========================================================
// PDF ANALYSIS
// =========================================================

export async function uploadPdf(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  return handleResponse(response);
}


export { API_BASE_URL };