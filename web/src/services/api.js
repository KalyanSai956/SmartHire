const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

import { retryRequest } from "./apiRetry";
async function request(
  path,
  { token, ...options } = {}
) {
  const headers = new Headers(
    options.headers || {}
  );

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    }
  );

  const contentType =
    response.headers.get("content-type") || "";


  if (!response.ok) {
    let message =
      `Request failed (${response.status})`;

    if (
      contentType.includes(
        "application/json"
      )
    ) {
      const data =
        await response
          .json()
          .catch(() => null);

      if (typeof data?.detail === "string") {
        message = data.detail;
      } else if (data?.detail && typeof data.detail === "object") {
        message =
          data.detail.message ||
          data.detail.code ||
          message;
      } else if (data?.error && typeof data.error === "object") {
        message =
          data.error.message ||
          data.error.code ||
          message;
      } else if (typeof data?.message === "string") {
        message = data.message;
      }

    } else {
      const text =
        await response
          .text()
          .catch(() => "");

      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }


  if (
    contentType.includes(
      "application/json"
    )
  ) {
    return response.json();
  }


  return response.text();
}

export async function retryInterviewRequest(
  operation,
  options = {},
) {
  return retryRequest(operation, {
    retries: 3,
    baseDelay: 700,
    ...options,
  });
}
/* =====================================================
   HEALTH
   ===================================================== */

export function healthCheck() {
  return request(
    "/api/v1/health"
  );
}


/* =====================================================
   HISTORY
   ===================================================== */

export function getHistory(token) {
  return request(
    "/api/v1/history",
    {
      token,
    }
  );
}


/* =====================================================
   DELETE HISTORY
   ===================================================== */

export function deleteHistoryEntry(
  id,
  token
) {
  return request(
    `/api/v1/history/${id}`,
    {
      method: "DELETE",
      token,
    }
  );
}


/*
 * Keep this alias because your History.jsx
 * currently imports deleteHistory.
 */
export function deleteHistory(
  id,
  token
) {
  return deleteHistoryEntry(
    id,
    token
  );
}


/* =====================================================
   RESUME ANALYSIS
   ===================================================== */

export function analyzeResume({
  file,
  jobDescription,
  provider,
  token,
}) {
  const formData = new FormData();

  formData.append(
    "resume",
    file
  );

  formData.append(
    "job_description",
    jobDescription || ""
  );

  if (provider) {
    formData.append(
      "provider",
      provider
    );
  }

  return request(
    "/api/v1/analyze-resume",
    {
      method: "POST",
      body: formData,
      token,
    }
  );
}
/* =====================================================
   HISTORY PDF
   ===================================================== */

export async function getHistoryPdf(
  id,
  token
) {
  const response =
    await fetch(
      `${API_BASE_URL}/api/v1/history/${id}/pdf`,
      {
        headers: token
          ? {
              Authorization:
                `Bearer ${token}`,
            }
          : {},
      }
    );


  if (!response.ok) {
    const data =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      data?.detail ||
        `PDF request failed (${response.status})`
    );
  }


  return response.blob();
}


/* =====================================================
   GENERATE PDF
   ===================================================== */

export async function generatePdfBlob(
  data,
  token
) {
  const response =
    await fetch(
      `${API_BASE_URL}/api/v1/generate-pdf`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          ...(token
            ? {
                Authorization:
                  `Bearer ${token}`,
              }
            : {}),
        },

        body: JSON.stringify(data),
      }
    );


  if (!response.ok) {
    const result =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      result?.detail ||
        `PDF request failed (${response.status})`
    );
  }


  return response.blob();
}

/* =====================================================
   CAREER PROFILE
   ===================================================== */

export function getProfile(token) {
  return request("/api/v1/profile", {
    token,
  });
}
export function saveOnboardingProgress({
  step,
  username,
  careerInterests,
  specializations,
  skills,
  targetRoles,
  experience,
  graduationYear,
  token,
}) {
  return request("/api/v1/profile/onboarding-progress", {
    method: "PATCH",
    token,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      step,
      username,
      career_interests: careerInterests,
      specializations,
      skills,
      target_roles: targetRoles,
      experience,
      graduation_year:
        graduationYear === "" || graduationYear == null
          ? null
          : Number(graduationYear),
    }),
  });
}

export function updateProfile({
  username,
  careerInterests,
  specializations,
  skills,
  targetRoles,
  experience,
  graduationYear,
  token,
}) {
  return request("/api/v1/profile", {
    method: "PUT",
    token,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      career_interests: careerInterests,
      specializations,
      skills,
      target_roles: targetRoles,
      experience,
      graduation_year: graduationYear,
    }),
  });
}

export function uploadProfileResume({
  file,
  token,
}) {
  const formData = new FormData();

  formData.append("resume", file);

  return request("/api/v1/profile/resume", {
    method: "POST",
    body: formData,
    token,
  });
}


export function completeOnboarding(token) {
  return request("/api/v1/profile/complete", {
    method: "POST",
    token,
  });
}



export async function getLLMSettings(accessToken) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/llm-settings`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    throw new Error(
      error.detail || "Failed to load AI settings."
    );
  }

  return response.json();
}


export async function connectLLMProvider(
  accessToken,
  provider,
  apiKey,
  model
) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/llm-settings/connect`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        provider,
        api_key: apiKey,
        model: model || null,
      }),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    throw new Error(
      error.detail || "Failed to connect AI provider."
    );
  }

  return response.json();
}


export async function disconnectLLMProvider(
  accessToken,
  provider
) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/llm-settings/${provider}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    throw new Error(
      error.detail || "Failed to disconnect AI provider."
    );
  }

  return response.json();
}


export async function getUsageQuota(accessToken) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/usage/quota`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    throw new Error(
      error.detail || "Failed to load usage information."
    );
  }

  return response.json();
}
/* =====================================================
   JOB RECOMMENDATIONS
   ===================================================== */
export function getJobRecommendations({
  token,
  matchThreshold = 0.25,
  candidateCount = 50,
  resultCount = 20,
  remoteType,
  employmentType,
}) {
  const params = new URLSearchParams();

  params.set("match_threshold", String(matchThreshold));
  params.set("candidate_count", String(candidateCount));
  params.set("result_count", String(resultCount));

  if (remoteType) {
    params.set("remote_type", remoteType);
  }

  if (employmentType) {
    params.set("employment_type", employmentType);
  }

  return request(
    `/api/v1/job-rag/recommendations?${params.toString()}`,
    {
      method: "GET",
      token,
    }
  );
}

/* =====================================================
   JOBS
   ===================================================== */

export async function getJobs({
  token,
  page = 1,
  limit = 20,
  search = "",
  location = "",
  remoteType = "",
  employmentType = "",
  experience = "",
  company = "",
  sort = "newest",
} = {}) {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
    sort,
  });

  if (search) {
    params.set("search", search);
  }

  if (location) {
    params.set("location", location);
  }

  if (remoteType) {
    params.set("remote_type", remoteType);
  }

  if (employmentType) {
    params.set("employment_type", employmentType);
  }

  if (experience) {
    params.set("experience", experience);
  }

  if (company) {
    params.set("company", company);
  }

  return request(
    `/api/v1/jobs?${params.toString()}`,
    {
      token,
    },
  );
}


/* =====================================================
   SAVED JOBS
   ===================================================== */

export async function getSavedJobs(token) {
  return request(
    "/api/v1/jobs/saved",
    {
      token,
    },
  );
}


/* =====================================================
   SAVE JOB
   ===================================================== */

export async function saveJob(
  jobId,
  token,
) {
  return request(
    `/api/v1/jobs/${jobId}/save`,
    {
      method: "POST",
      token,
    },
  );
}


/* =====================================================
   REMOVE SAVED JOB
   ===================================================== */

export async function removeSavedJob(
  jobId,
  token,
) {
  return request(
    `/api/v1/jobs/${jobId}/save`,
    {
      method: "DELETE",
      token,
    },
  );
}