export function normalizeHistoryItem(item) {
  const nestedResult =
    item?.analysis_result ??
    item?.analysisResult ??
    item?.analysis ??
    item?.result;

  const result =
    nestedResult &&
    typeof nestedResult === "object"
      ? nestedResult
      : item;

  const id =
    item?.id ??
    item?.analysis_id ??
    item?.analysisId;

  return {
    ...item,

    id,
    result,

    filename:
      item?.filename ??
      item?.file_name ??
      item?.resume_filename ??
      item?.resume_name ??
      "Resume analysis",

    createdAt:
      item?.created_at ??
      item?.createdAt ??
      item?.timestamp ??
      null,
  };
}

export function normalizeHistory(data) {
  if (Array.isArray(data)) {
    return data.map(normalizeHistoryItem);
  }

  if (Array.isArray(data?.data)) {
    return data.data.map(normalizeHistoryItem);
  }

  if (Array.isArray(data?.history)) {
    return data.history.map(normalizeHistoryItem);
  }

  return [];
}


export function getAtsScore(result) {
  const candidates = [
    result?.ats_score,
    result?.ATS_score,
    result?.advanced_ats?.ats_score,
    result?.advanced_ats?.atsScore,
    result?.advancedATS?.ats_score,
    result?.advancedATS?.atsScore,
  ];

  for (const value of candidates) {
    if (
      value !== null &&
      value !== undefined &&
      value !== "" &&
      Number.isFinite(Number(value))
    ) {
      return Number(value);
    }
  }

  return 0;
}

export function getJdMatch(result) {
  const candidates = [
    result?.jd_comparison?.match_percentage,
    result?.jd_match_analysis?.match_percentage,
    result?.advanced_ats?.jd_match,
    result?.advanced_ats?.jdMatch,
    result?.advancedATS?.jd_match,
    result?.advancedATS?.jdMatch,
    result?.keyword_match,
  ];

  for (const value of candidates) {
    if (
      value !== null &&
      value !== undefined &&
      value !== "" &&
      Number.isFinite(Number(value))
    ) {
      return Number(value);
    }
  }

  return 0;
}


export function getSkills(result) {
  return Array.isArray(result?.skills) ? result.skills : [];
}

export function scoreStatus(score) {
  if (score >= 85) return "excellent";
  if (score >= 75) return "good";
  if (score >= 65) return "average";
  return "low";
}

export function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric"
  });
}

export function shortDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric"
  });
}
