"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";

import {
  AdminCompetitionForm,
  competitionFormFromCompetition,
  toUpdateCompetitionPayload,
  type CompetitionFormState,
} from "@/components/admin-competition-form";
import { AdminAccessState, AdminPageShell } from "@/components/admin-page-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import {
  getAdminCompetitionSubmissions,
  getAdminSubmissionSourceFileUrl,
  getSolutionFileUrl,
  getTestFileUrl,
  getCompetition,
  getOptionalSession,
  rescoreCompetitionSubmissions,
  getScoringConfig,
  updateCompetition,
  updateScoringConfig,
} from "@/lib/api";
import type { AdminTask, Competition, ScoringConfig, User } from "@/lib/competition-types";

type AdminEditCompetitionPageProps = {
  slug: string;
};

export function AdminEditCompetitionPage({ slug }: AdminEditCompetitionPageProps) {
  const [user, setUser] = useState<User | null>(null);
  const [competition, setCompetition] = useState<Competition | null>(null);
  const [form, setForm] = useState<CompetitionFormState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [scoringConfig, setScoringConfig] = useState<ScoringConfig | null>(null);
  const [scoringCode, setScoringCode] = useState("");
  const [solutionFile, setSolutionFile] = useState<File | null>(null);
  const [testFile, setTestFile] = useState<File | null>(null);
  const [scoringMessage, setScoringMessage] = useState<string | null>(null);
  const [scoringBusy, setScoringBusy] = useState(false);
  const [rescoreBusy, setRescoreBusy] = useState(false);
  const [competitionSubmissions, setCompetitionSubmissions] = useState<AdminTask[]>([]);

  useEffect(() => {
    let active = true;

    async function loadCompetition() {
      setLoading(true);
      setError(null);

      try {
        const currentUser = await getOptionalSession();
        if (!active) {
          return;
        }

        setUser(currentUser);
        if (!currentUser || !currentUser.is_admin) {
          return;
        }

        const [loadedCompetition, loadedScoringConfig, loadedSubmissions] = await Promise.all([
          getCompetition(slug),
          getScoringConfig(slug),
          getAdminCompetitionSubmissions(slug),
        ]);
        if (!active) {
          return;
        }

        setCompetition(loadedCompetition);
        setForm(competitionFormFromCompetition(loadedCompetition));
        setScoringConfig(loadedScoringConfig);
        setScoringCode(loadedScoringConfig.metric_code ?? "");
        setCompetitionSubmissions(loadedSubmissions);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setError(
          loadError instanceof Error ? loadError.message : "Failed to load competition.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadCompetition();

    return () => {
      active = false;
    };
  }, [slug]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form) {
      return;
    }

    setBusy(true);
    setMessage(null);

    try {
      const updatedCompetition = await updateCompetition(
        slug,
        toUpdateCompetitionPayload(form),
      );
      setCompetition(updatedCompetition);
      setForm(competitionFormFromCompetition(updatedCompetition));
      setMessage(`Saved ${updatedCompetition.title}.`);
    } catch (submitError) {
      setMessage(
        submitError instanceof Error ? submitError.message : "Failed to update competition.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleScoringSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form) {
      return;
    }

    setScoringBusy(true);
    setScoringMessage(null);

    try {
      const updatedScoringConfig = await updateScoringConfig(slug, {
        metricName: form.scoring_metric,
        scoringDirection: form.scoring_direction,
        metricCode: scoringCode,
        solutionFile,
        testFile,
      });
      setScoringConfig(updatedScoringConfig);
      setScoringCode(updatedScoringConfig.metric_code ?? "");
      setSolutionFile(null);
      setTestFile(null);
      setMessage(`Saved ${form.title}.`);
      setScoringMessage("Saved scoring configuration.");
    } catch (submitError) {
      setScoringMessage(
        submitError instanceof Error ? submitError.message : "Failed to save scoring configuration.",
      );
    } finally {
      setScoringBusy(false);
    }
  }

  async function handleRescoreAll() {
    setRescoreBusy(true);
    setScoringMessage(null);

    try {
      const result = await rescoreCompetitionSubmissions(slug);
      setScoringMessage(
        result.queued_submission_count === 0
          ? "No submissions were queued for rescoring."
          : `Queued ${result.queued_submission_count} submissions for rescoring.`,
      );
    } catch (submitError) {
      setScoringMessage(
        submitError instanceof Error ? submitError.message : "Failed to queue rescoring.",
      );
    } finally {
      setRescoreBusy(false);
    }
  }

  return (
    <AdminPageShell
      user={user}
      title="Edit Competition"
      description="Update one competition at a time from a dedicated screen so edits stay focused and less error-prone."
      loginHref={`/login?next=/admin/competitions/${slug}`}
    >
      {loading ? (
        <AdminAccessState kind="loading" />
      ) : !user ? (
        <div className="mt-8 rounded-2xl border border-[#ececec] bg-[#fafafa] px-5 py-5">
          <p className="text-sm text-[#555555]">
            Sign in with an admin account to edit competitions.
          </p>
          <Button
            asChild
            className="mt-4 h-9 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
          >
            <Link href={`/login?next=/admin/competitions/${slug}`}>Login</Link>
          </Button>
        </div>
      ) : !user.is_admin ? (
        <AdminAccessState kind="forbidden" />
      ) : error || !competition || !form ? (
        <div className="mt-8 rounded-2xl border border-[#f0d4d4] bg-[#fff8f8] px-5 py-4 text-sm text-[#a04141]">
          {error ?? "Competition not found."}
        </div>
      ) : (
        <div className="mt-8 rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-semibold tracking-[-0.03em] text-black">
                  {competition.title}
                </h2>
                <Badge
                  variant="secondary"
                  className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                >
                  {competition.status}
                </Badge>
              </div>
              <p className="mt-2 text-sm text-[#6f6f6f]">
                Editing slug <span className="font-medium">{competition.slug}</span>.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button
                asChild
                variant="outline"
                className="h-9 rounded-full border-[#e4e4e4] bg-white px-4 text-xs font-semibold text-[#1f1f1f] hover:bg-[#f6f6f6]"
              >
                <Link href="/admin">Back to admin</Link>
              </Button>
              <Button
                asChild
                variant="outline"
                className="h-9 rounded-full border-[#e4e4e4] bg-white px-4 text-xs font-semibold text-[#1f1f1f] hover:bg-[#f6f6f6]"
              >
                <Link href={`/competitions/${competition.slug}`}>Open competition</Link>
              </Button>
            </div>
          </div>

          <AdminCompetitionForm
            form={form}
            mode="edit"
            message={message}
            submitLabel={busy ? "Saving..." : "Save changes"}
            onChange={(field, value) =>
              setForm((current) => (current ? { ...current, [field]: value } : current))
            }
            onSubmit={handleSubmit}
          />

          <div className="mt-8 border-t border-[#efefef] pt-8">
            <div className="mb-6 flex flex-col gap-2">
              <h3 className="text-base font-semibold tracking-[-0.02em] text-black">
                Scoring Setup
              </h3>
              <p className="text-sm text-[#6f6f6f]">
                {competition.submission_mode === "code_submission"
                  ? "Save a Python metric script that imports `predict` from `participant_submission`. You can also upload an optional `solution.csv` and import `competition_solution` inside the metric to read it during `score_submission()`."
                  : "Upload a `solution.csv` with an `Id` column, then save a Python scoring script. The worker will align submission rows by `Id` and execute `score_submission(solution_rows, submission_rows)`."}
              </p>
            </div>

            <div className="mb-5 flex flex-wrap gap-3 text-xs text-[#6f6f6f]">
              <span>
                Solution:{" "}
                {scoringConfig?.solution_filename ? (
                  <a
                    href={getSolutionFileUrl(slug)}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-[#202020] underline underline-offset-4"
                  >
                    {scoringConfig.solution_filename}
                  </a>
                ) : (
                  "not uploaded"
                )}
              </span>
              <span>
                Test data:{" "}
                {scoringConfig?.test_filename ? (
                  <a
                    href={getTestFileUrl(slug)}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-[#202020] underline underline-offset-4"
                  >
                    {scoringConfig.test_filename}
                  </a>
                ) : (
                  "not uploaded"
                )}
              </span>
              <span>
                Metric file: {scoringConfig?.metric_script_filename ?? "not saved"}
              </span>
            </div>

            <div className="mb-5 flex flex-wrap gap-3">
              {scoringConfig?.templates.map((template) => (
                <Button
                  key={template.name}
                  type="button"
                  variant="outline"
                  className="h-9 rounded-full border-[#e4e4e4] bg-white px-4 text-xs font-semibold text-[#1f1f1f] hover:bg-[#f6f6f6]"
                  onClick={() => {
                    setScoringCode(template.code);
                    setForm((current) =>
                      current
                        ? {
                            ...current,
                            scoring_metric: template.default_metric_name,
                            scoring_direction: template.default_scoring_direction,
                          }
                        : current,
                    );
                  }}
                >
                  Load {template.title}
                </Button>
              ))}
            </div>

            <form className="space-y-5" onSubmit={handleScoringSubmit}>
              {competition.submission_mode === "prediction_file" ||
              competition.submission_mode === "code_submission" ? (
                <label className="block space-y-2">
                  <Label className="text-[11px] uppercase tracking-[0.14em] text-[#666666]">
                    {competition.submission_mode === "code_submission"
                      ? "solution.csv (optional)"
                      : "solution.csv"}
                  </Label>
                  <Input
                    type="file"
                    accept=".csv"
                    onChange={(event) => setSolutionFile(event.target.files?.[0] ?? null)}
                  />
                </label>
              ) : null}
              {competition.submission_mode === "code_submission" ? (
                <label className="block space-y-2">
                  <Label className="text-[11px] uppercase tracking-[0.14em] text-[#666666]">
                    test.csv (optional)
                  </Label>
                  <Input
                    type="file"
                    accept=".csv"
                    onChange={(event) => setTestFile(event.target.files?.[0] ?? null)}
                  />
                </label>
              ) : null}

              <label className="block space-y-2">
                <Label className="text-[11px] uppercase tracking-[0.14em] text-[#666666]">
                  Metric Python Code
                </Label>
                <Textarea
                  className="min-h-[360px] rounded-2xl border-[#e7e7e7] bg-white px-4 py-3 font-mono text-sm shadow-none focus-visible:ring-1"
                  value={scoringCode}
                  onChange={(event) => setScoringCode(event.target.value)}
                />
              </label>

              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                {scoringMessage ? (
                  <p className="text-sm text-[#555555]">{scoringMessage}</p>
                ) : (
                  <span className="text-sm text-[#8a8a8a]">
                    Available templates are a starting point. You can edit the Python code before saving.
                  </span>
                )}
                <div className="flex flex-wrap gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    className="h-10 rounded-full border-[#e4e4e4] bg-white px-5 text-xs font-semibold text-[#1f1f1f] hover:bg-[#f6f6f6]"
                    disabled={scoringBusy || rescoreBusy}
                    onClick={() => {
                      void handleRescoreAll();
                    }}
                  >
                    {rescoreBusy ? "Queueing rescore..." : "Rescore all submissions"}
                  </Button>
                  <Button
                    className="h-10 rounded-full bg-[#1f1f1f] px-5 text-xs font-semibold hover:bg-[#111111]"
                    disabled={scoringBusy || rescoreBusy}
                  >
                    {scoringBusy ? "Saving scoring..." : "Save scoring setup"}
                  </Button>
                </div>
              </div>
            </form>
          </div>

          <div className="mt-8 border-t border-[#efefef] pt-8">
            <div className="mb-6 flex flex-col gap-2">
              <h3 className="text-base font-semibold tracking-[-0.02em] text-black">
                Competition Submissions
              </h3>
              <p className="text-sm text-[#6f6f6f]">
                Review every uploaded source file for this competition and download the original submission directly from admin.
              </p>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead>Participant</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead>Download</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {competitionSubmissions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-sm text-[#757575]">
                      No submissions have been uploaded for this competition yet.
                    </TableCell>
                  </TableRow>
                ) : (
                  competitionSubmissions.map((submission) => (
                    <TableRow key={submission.submission_id}>
                      <TableCell>
                        <div className="font-medium text-[#111111]">
                          {submission.source_original_filename}
                        </div>
                        <div className="mt-1 text-xs text-[#7a7a7a]">
                          {submission.submission_type.toUpperCase()} · {formatBytes(submission.source_size_bytes)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium text-[#111111]">
                          {submission.participant_name}
                        </div>
                        <div className="mt-1 text-xs text-[#7a7a7a]">
                          {submission.participant_email}
                        </div>
                      </TableCell>
                      <TableCell>{submission.submission_status}</TableCell>
                      <TableCell>{formatDateTime(submission.created_at)}</TableCell>
                      <TableCell>
                        <a
                          className="text-sm font-medium text-[#111111] underline-offset-4 hover:underline"
                          href={getAdminSubmissionSourceFileUrl(submission.submission_id)}
                          rel="noreferrer"
                          target="_blank"
                        >
                          Download file
                        </a>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </AdminPageShell>
  );
}

function formatBytes(size: number) {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString();
}
