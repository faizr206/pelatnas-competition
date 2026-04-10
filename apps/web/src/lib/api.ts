import type {
  AdminManagedUser,
  AdminTask,
  AdminWorker,
  Competition,
  CompetitionCreatePayload,
  CompetitionUpdatePayload,
  Dataset,
  Job,
  LeaderboardEntry,
  LeaderboardVisibility,
  ScoringConfig,
  RescoreSubmissionsResult,
  Submission,
  User,
} from "@/lib/competition-types";

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const apiOrigin = apiBaseUrl.replace(/\/api\/v1$/, "");

export function getSolutionFileUrl(slug: string) {
  return `${apiBaseUrl}/competitions/${slug}/solution-file`;
}

export function getTestFileUrl(slug: string) {
  return `${apiBaseUrl}/competitions/${slug}/test-file`;
}

async function readErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as
      | { detail?: string; error?: { message?: string } }
      | undefined;
    return payload?.error?.message ?? payload?.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

async function expectJson<T>(response: Response) {
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
}

export async function getOptionalSession() {
  const response = await fetch(`${apiBaseUrl}/auth/me`, {
    credentials: "include",
    cache: "no-store",
  });

  if (response.status === 401) {
    return null;
  }

  return expectJson<User>(response);
}

export async function getCompetitions() {
  const response = await fetch(`${apiBaseUrl}/competitions`, {
    cache: "no-store",
  });
  return expectJson<Competition[]>(response);
}

export async function getCompetition(slug: string) {
  const response = await fetch(`${apiBaseUrl}/competitions/${slug}`, {
    cache: "no-store",
  });
  return expectJson<Competition>(response);
}

export async function getDatasets(slug: string) {
  const response = await fetch(`${apiBaseUrl}/competitions/${slug}/datasets`, {
    credentials: "include",
    cache: "no-store",
  });
  return expectJson<Dataset[]>(response);
}

export async function getSubmissions(slug: string) {
  const response = await fetch(`${apiBaseUrl}/competitions/${slug}/submissions`, {
    credentials: "include",
    cache: "no-store",
  });
  return expectJson<Submission[]>(response);
}

export async function getLeaderboard(slug: string, visibility: LeaderboardVisibility) {
  const response = await fetch(
    `${apiBaseUrl}/competitions/${slug}/leaderboard/${visibility}`,
    {
      cache: "no-store",
    },
  );
  return expectJson<LeaderboardEntry[]>(response);
}

export async function submitCompetitionSubmission(
  slug: string,
  submissionType: string,
  file: File,
) {
  const formData = new FormData();
  formData.append("submission_type", submissionType);
  formData.append("source_file", file);

  const response = await fetch(`${apiBaseUrl}/competitions/${slug}/submissions`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  return expectJson<Job>(response);
}

export async function getJob(jobId: string) {
  const response = await fetch(`${apiBaseUrl}/jobs/${jobId}`, {
    credentials: "include",
    cache: "no-store",
  });
  return expectJson<Job>(response);
}

export async function login(email: string, password: string) {
  const response = await fetch(`${apiBaseUrl}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  return expectJson<User>(response);
}

export async function logout() {
  const response = await fetch(`${apiBaseUrl}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  return expectJson<null>(response);
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const response = await fetch(`${apiBaseUrl}/auth/change-password`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

  return expectJson<User>(response);
}

export async function getAdminUsers() {
  const response = await fetch(`${apiBaseUrl}/admin/users`, {
    credentials: "include",
    cache: "no-store",
  });

  return expectJson<AdminManagedUser[]>(response);
}

export async function getAdminWorkers() {
  const response = await fetch(`${apiBaseUrl}/admin/workers`, {
    credentials: "include",
    cache: "no-store",
  });

  return expectJson<AdminWorker[]>(response);
}

export async function updateAdminWorker(workerId: string, payload: { is_enabled: boolean }) {
  const response = await fetch(`${apiBaseUrl}/admin/workers/${workerId}`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return expectJson<AdminWorker>(response);
}

export async function getAdminTasks() {
  const response = await fetch(`${apiBaseUrl}/admin/tasks`, {
    credentials: "include",
    cache: "no-store",
  });

  return expectJson<AdminTask[]>(response);
}

export async function createAdminUser(payload: {
  email: string;
  display_name: string;
  default_password: string;
  is_admin: boolean;
  status: string;
}) {
  const response = await fetch(`${apiBaseUrl}/admin/users`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return expectJson<AdminManagedUser>(response);
}

export async function updateAdminUser(
  userId: string,
  payload: {
    display_name: string;
    is_admin: boolean;
    status: string;
  },
) {
  const response = await fetch(`${apiBaseUrl}/admin/users/${userId}`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return expectJson<AdminManagedUser>(response);
}

export async function resetAdminUserPassword(userId: string, defaultPassword: string) {
  const response = await fetch(`${apiBaseUrl}/admin/users/${userId}/reset-password`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ default_password: defaultPassword }),
  });

  return expectJson<AdminManagedUser>(response);
}

export async function createCompetition(payload: CompetitionCreatePayload) {
  const response = await fetch(`${apiBaseUrl}/competitions`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return expectJson<Competition>(response);
}

export async function updateCompetition(
  slug: string,
  payload: CompetitionUpdatePayload,
) {
  const response = await fetch(`${apiBaseUrl}/competitions/${slug}`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return expectJson<Competition>(response);
}

export async function getScoringConfig(slug: string) {
  const response = await fetch(`${apiBaseUrl}/competitions/${slug}/scoring-config`, {
    credentials: "include",
    cache: "no-store",
  });

  return expectJson<ScoringConfig>(response);
}

export async function updateScoringConfig(
  slug: string,
  payload: {
    metricName: string;
    scoringDirection: string;
    metricCode: string;
    solutionFile?: File | null;
    testFile?: File | null;
  },
) {
  const formData = new FormData();
  formData.append("metric_name", payload.metricName);
  formData.append("scoring_direction", payload.scoringDirection);
  formData.append("metric_code", payload.metricCode);
  if (payload.solutionFile) {
    formData.append("solution_file", payload.solutionFile);
  }
  if (payload.testFile) {
    formData.append("test_file", payload.testFile);
  }

  const response = await fetch(`${apiBaseUrl}/competitions/${slug}/scoring-config`, {
    method: "PUT",
    credentials: "include",
    body: formData,
  });

  return expectJson<ScoringConfig>(response);
}

export async function rescoreCompetitionSubmissions(slug: string) {
  const response = await fetch(`${apiBaseUrl}/competitions/${slug}/rescore-submissions`, {
    method: "POST",
    credentials: "include",
  });

  return expectJson<RescoreSubmissionsResult>(response);
}
