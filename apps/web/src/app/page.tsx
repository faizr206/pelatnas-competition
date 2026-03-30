"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

type User = {
  id: string;
  email: string;
  display_name: string;
  status: string;
  is_admin: boolean;
};

type CompetitionPhase = {
  id: string;
  name: string;
  starts_at: string;
  ends_at: string;
  submission_limit_per_day: number;
  scoring_version: string;
  rules_version: string;
};

type Competition = {
  id: string;
  slug: string;
  title: string;
  description: string;
  visibility: string;
  status: string;
  phases: CompetitionPhase[];
};

type Job = {
  id: string;
  submission_id: string;
  job_type: string;
  status: string;
  queued_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  worker_id: string | null;
  retry_count: number;
  failure_reason: string | null;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default function HomePage() {
  const [user, setUser] = useState<User | null>(null);
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [activeJob, setActiveJob] = useState<Job | null>(null);
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin1234");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadCompetitions = useCallback(async () => {
    const response = await fetch(`${apiBaseUrl}/competitions`, {
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error("Failed to load competitions.");
    }

    const data = (await response.json()) as Competition[];
    setCompetitions(data);
  }, []);

  const loadSession = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/auth/me`, {
        credentials: "include",
      });

      if (!response.ok) {
        setUser(null);
        setCompetitions([]);
        return;
      }

      const currentUser = (await response.json()) as User;
      setUser(currentUser);
      await loadCompetitions();
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }, [loadCompetitions]);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  useEffect(() => {
    if (!activeJob) {
      return;
    }

    if (["completed", "failed", "cancelled", "timed_out"].includes(activeJob.status)) {
      return;
    }

    const interval = window.setInterval(() => {
      void refreshJob(activeJob.id);
    }, 2500);

    return () => window.clearInterval(interval);
  }, [activeJob]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setSubmitting(true);

    try {
      const response = await fetch(`${apiBaseUrl}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = (await response.json()) as { detail?: string };
        throw new Error(data.detail ?? "Login failed.");
      }

      setMessage("Session established. Competition data is ready.");
      await loadSession();
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLogout() {
    setError(null);
    setMessage(null);

    try {
      await fetch(`${apiBaseUrl}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      setUser(null);
      setCompetitions([]);
      setActiveJob(null);
      setMessage("Session cleared.");
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    }
  }

  async function handleCreateSubmission() {
    const competition = competitions[0];
    if (!competition) {
      setError("No competition is available for the smoke test.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch(
        `${apiBaseUrl}/competitions/${competition.slug}/submissions`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            submission_type: "file",
            source_archive_path: "phase0/source.zip",
            manifest_path: "phase0/manifest.json",
          }),
        },
      );

      if (!response.ok) {
        const data = (await response.json()) as { detail?: string };
        throw new Error(data.detail ?? "Submission failed.");
      }

      const job = (await response.json()) as Job;
      setActiveJob(job);
      setMessage(`Submission accepted. Job ${job.id} is ${job.status}.`);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setSubmitting(false);
    }
  }

  async function refreshJob(jobId: string) {
    try {
      const response = await fetch(`${apiBaseUrl}/jobs/${jobId}`, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Failed to refresh job status.");
      }

      const job = (await response.json()) as Job;
      setActiveJob(job);

      if (job.status === "completed") {
        setMessage(`Job ${job.id} completed successfully.`);
      }

      if (job.status === "failed") {
        setError(job.failure_reason ?? "Job failed.");
      }
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    }
  }

  return (
    <main className="page">
      <div className="shell">
        <section className="hero">
          <p className="eyebrow">Phase 0 Foundation</p>
          <h1>Competition platform baseline, wired end to end.</h1>
          <p>
            This screen verifies the locked phase-0 decisions: session auth,
            seeded competition data, Redis-backed jobs, worker processing, and
            the local-only runtime layout.
          </p>
        </section>

        {(message || error) && (
          <section className="grid">
            {message && <div className="message success">{message}</div>}
            {error && <div className="message error">{error}</div>}
          </section>
        )}

        <section className="grid">
          <article className="card">
            <h2>Session auth</h2>
            {loading ? (
              <p className="meta">Loading current session.</p>
            ) : user ? (
              <div className="stack">
                <span className="pill">Signed in</span>
                <div className="list-item">
                  <strong>{user.display_name}</strong>
                  <div className="meta">
                    {user.email}
                    <br />
                    status: <code>{user.status}</code>
                    <br />
                    admin: <code>{String(user.is_admin)}</code>
                  </div>
                </div>
                <div className="actions">
                  <button className="button secondary" onClick={handleLogout}>
                    Logout
                  </button>
                  <button
                    className="button"
                    onClick={() => void loadSession()}
                    disabled={submitting}
                  >
                    Refresh session
                  </button>
                </div>
              </div>
            ) : (
              <form className="stack" onSubmit={handleLogin}>
                <div className="field">
                  <label htmlFor="email">Email</label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="password">Password</label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                </div>
                <div className="actions">
                  <button className="button" type="submit" disabled={submitting}>
                    {submitting ? "Signing in..." : "Login"}
                  </button>
                </div>
              </form>
            )}
          </article>

          <article className="card">
            <h2>Competitions</h2>
            {user ? (
              competitions.length > 0 ? (
                <div className="list">
                  {competitions.map((competition) => (
                    <div className="list-item" key={competition.id}>
                      <strong>{competition.title}</strong>
                      <div className="meta">
                        slug: <code>{competition.slug}</code>
                        <br />
                        status: <code>{competition.status}</code>
                        <br />
                        visibility: <code>{competition.visibility}</code>
                        <br />
                        phases: <code>{competition.phases.length}</code>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="meta">No competitions available.</p>
              )
            ) : (
              <p className="meta">
                Sign in with the seeded phase-0 admin to load the smoke-test
                competition.
              </p>
            )}
          </article>

          <article className="card">
            <h2>Queue and worker</h2>
            {user ? (
              <div className="stack">
                <p className="meta">
                  Create a placeholder file submission to verify that the API
                  writes submission and job records, then the worker pulls the
                  queued job and completes the skeleton pipeline.
                </p>
                <div className="actions">
                  <button
                    className="button"
                    onClick={handleCreateSubmission}
                    disabled={submitting || competitions.length === 0}
                  >
                    {submitting ? "Submitting..." : "Create smoke-test submission"}
                  </button>
                </div>
                {activeJob ? (
                  <div className="list-item">
                    <span className="job-title">Active job</span>
                    <div className="meta">
                      id: <code>{activeJob.id}</code>
                      <br />
                      submission: <code>{activeJob.submission_id}</code>
                      <br />
                      status: <code>{activeJob.status}</code>
                      <br />
                      worker: <code>{activeJob.worker_id ?? "pending"}</code>
                      <br />
                      failure: <code>{activeJob.failure_reason ?? "none"}</code>
                    </div>
                  </div>
                ) : (
                  <p className="meta">No submission has been created in this session.</p>
                )}
              </div>
            ) : (
              <p className="meta">Login first to exercise the queue path.</p>
            )}
          </article>
        </section>
      </div>
    </main>
  );
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Unexpected request failure.";
}
