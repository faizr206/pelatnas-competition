import type {
  Competition,
  Dataset,
  Job,
  LeaderboardEntry,
  LeaderboardVisibility,
  Submission,
  User,
} from "@/lib/competition-types";

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const apiOrigin = apiBaseUrl.replace(/\/api\/v1$/, "");

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
