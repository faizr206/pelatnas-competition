"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import { SiteHeader } from "@/components/site-header";
import { UserChip } from "@/components/user-chip";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  apiOrigin,
  getCompetition,
  getDatasets,
  getJob,
  getLeaderboard,
  getOptionalSession,
  getSubmissions,
  submitCompetitionSubmission,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import type {
  Competition,
  CompetitionTab,
  Dataset,
  Job,
  LeaderboardEntry,
  LeaderboardVisibility,
  Submission,
  User,
} from "@/lib/competition-types";
import { activeJobStatuses, competitionTabs } from "@/lib/competition-types";

type CompetitionWorkspaceProps = {
  slug: string;
};

export function CompetitionWorkspace({ slug }: CompetitionWorkspaceProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<CompetitionTab>("overview");
  const [leaderboardVisibility, setLeaderboardVisibility] =
    useState<LeaderboardVisibility>("public");
  const [competition, setCompetition] = useState<Competition | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [publicLeaderboard, setPublicLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [privateLeaderboard, setPrivateLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [activeJob, setActiveJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [resourceMessage, setResourceMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [submissionType, setSubmissionType] = useState("csv");
  const [submissionFile, setSubmissionFile] = useState<File | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);

  const selectedPhase = competition?.phases[0] ?? null;
  const visibleLeaderboard =
    leaderboardVisibility === "public" ? publicLeaderboard : privateLeaderboard;

  useEffect(() => {
    let active = true;

    async function loadWorkspace() {
      setLoading(true);
      setError(null);
      setResourceMessage(null);

      try {
        const [competitionData, currentUser, publicEntries] = await Promise.all([
          getCompetition(slug),
          getOptionalSession(),
          getLeaderboard(slug, "public"),
        ]);

        if (!active) {
          return;
        }

        setCompetition(competitionData);
        setUser(currentUser);
        setPublicLeaderboard(publicEntries);
        setSubmissionType(
          competitionData.allow_csv_submissions
            ? "csv"
            : competitionData.allow_notebook_submissions
              ? "notebook"
              : "csv",
        );

        if (!currentUser) {
          setDatasets([]);
          setSubmissions([]);
          setPrivateLeaderboard([]);
          return;
        }

        const [datasetResult, submissionResult] = await Promise.allSettled([
          getDatasets(slug),
          getSubmissions(slug),
        ]);

        if (!active) {
          return;
        }

        if (datasetResult.status === "fulfilled") {
          setDatasets(datasetResult.value);
        } else {
          setResourceMessage(datasetResult.reason instanceof Error ? datasetResult.reason.message : "Datasets are unavailable right now.");
        }

        if (submissionResult.status === "fulfilled") {
          setSubmissions(submissionResult.value);
          setActiveJob(
            submissionResult.value.find((submission) => submission.latest_job)?.latest_job ??
              null,
          );
        } else {
          setResourceMessage(submissionResult.reason instanceof Error ? submissionResult.reason.message : "Submissions are unavailable right now.");
        }
      } catch (loadError) {
        if (!active) {
          return;
        }

        setError(
          loadError instanceof Error
            ? loadError.message
            : "Failed to load competition workspace.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadWorkspace();

    return () => {
      active = false;
    };
  }, [slug]);

  useEffect(() => {
    if (leaderboardVisibility !== "private" || privateLeaderboard.length > 0) {
      return;
    }

    let active = true;

    async function loadPrivateLeaderboard() {
      try {
        const entries = await getLeaderboard(slug, "private");
        if (active) {
          setPrivateLeaderboard(entries);
        }
      } catch (loadError) {
        if (active) {
          setResourceMessage(
            loadError instanceof Error
              ? loadError.message
              : "Private leaderboard is unavailable.",
          );
        }
      }
    }

    void loadPrivateLeaderboard();

    return () => {
      active = false;
    };
  }, [leaderboardVisibility, privateLeaderboard.length, slug]);

  useEffect(() => {
    if (!user || !activeJob || !activeJobStatuses.has(activeJob.status)) {
      return;
    }

    const timeoutId = window.setTimeout(async () => {
      try {
        const nextJob = await getJob(activeJob.id);
        setActiveJob(nextJob);

        const nextSubmissions = await getSubmissions(slug);
        setSubmissions(nextSubmissions);

        const newestJob =
          nextSubmissions.find((submission) => submission.id === nextJob.submission_id)
            ?.latest_job ?? nextJob;
        setActiveJob(newestJob);

        const refreshedPublicLeaderboard = await getLeaderboard(slug, "public");
        setPublicLeaderboard(refreshedPublicLeaderboard);

        if (leaderboardVisibility === "private") {
          const refreshedPrivateLeaderboard = await getLeaderboard(slug, "private");
          setPrivateLeaderboard(refreshedPrivateLeaderboard);
        }
      } catch {
        // Silent polling failures keep the existing state visible.
      }
    }, 4000);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [activeJob, leaderboardVisibility, slug, user]);

  async function refreshSignedInResources() {
    if (!user) {
      return;
    }

    const [datasetResult, submissionResult] = await Promise.allSettled([
      getDatasets(slug),
      getSubmissions(slug),
    ]);

    if (datasetResult.status === "fulfilled") {
      setDatasets(datasetResult.value);
    }

    if (submissionResult.status === "fulfilled") {
      setSubmissions(submissionResult.value);
      setActiveJob(
        submissionResult.value.find((submission) => submission.latest_job)?.latest_job ??
          null,
      );
    }
  }

  async function handleSubmission(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!user) {
      router.push(`/login?next=/competitions/${slug}`);
      return;
    }

    if (!submissionFile) {
      setResourceMessage("Choose a file before submitting.");
      return;
    }

    setBusy(true);
    setResourceMessage(null);

    try {
      const queuedJob = await submitCompetitionSubmission(
        slug,
        submissionType,
        submissionFile,
      );

      setActiveJob(queuedJob);
      setSubmissionFile(null);
      setFileInputKey((current) => current + 1);
      setResourceMessage("Submission accepted and queued for evaluation.");

      await refreshSignedInResources();

      const refreshedPublicLeaderboard = await getLeaderboard(slug, "public");
      setPublicLeaderboard(refreshedPublicLeaderboard);

      if (leaderboardVisibility === "private") {
        const refreshedPrivateLeaderboard = await getLeaderboard(slug, "private");
        setPrivateLeaderboard(refreshedPrivateLeaderboard);
      }
    } catch (submitError) {
      setResourceMessage(
        submitError instanceof Error
          ? submitError.message
          : "Submission failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-white text-slate-950">
        <SiteHeader
          activeNav="competitions"
          action={<div className="h-9 w-9 rounded-[10px] bg-[#f2f2f2]" />}
        />
        <main className="px-6 pb-16 pt-8 md:px-12 md:pt-10">
          <div className="mx-auto max-w-[1872px] animate-pulse space-y-6">
            <div className="h-14 w-80 rounded bg-[#efefef]" />
            <div className="h-24 rounded-2xl bg-[#f6f6f6]" />
            <div className="h-72 rounded-2xl bg-[#f8f8f8]" />
          </div>
        </main>
      </div>
    );
  }

  if (error || !competition) {
    return (
      <div className="min-h-screen bg-white text-slate-950">
        <SiteHeader
          activeNav="competitions"
          action={
            user ? (
              <UserChip user={user} />
            ) : (
              <Button
                asChild
                className="h-9 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
              >
                <Link href="/login">Login</Link>
              </Button>
            )
          }
        />
        <main className="px-6 pb-16 pt-8 md:px-12 md:pt-10">
          <div className="mx-auto max-w-[960px] rounded-2xl border border-[#f0d4d4] bg-[#fff8f8] px-5 py-4 text-sm text-[#a04141]">
            {error ?? "Competition not found."}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white text-slate-950">
      <SiteHeader
        activeNav="competitions"
        action={
          user ? (
            <UserChip user={user} />
          ) : (
            <Button
              asChild
              className="h-9 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
            >
              <Link href={`/login?next=/competitions/${competition.slug}`}>Login</Link>
            </Button>
          )
        }
      />
      <main className="px-6 pb-16 pt-8 md:px-12 md:pt-10">
        <div className="mx-auto max-w-[1872px]">
          <section className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-5xl">
              <div className="mb-4 flex flex-wrap items-center gap-2">
                <Badge
                  variant="secondary"
                  className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                >
                  {competition.status}
                </Badge>
                <Badge
                  variant="outline"
                  className="border-[#e7e7e7] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                >
                  {competition.scoring_metric}
                </Badge>
              </div>
              <h1 className="text-[2rem] font-semibold tracking-[-0.04em] text-black md:text-[3.5rem] md:leading-[1.05]">
                {competition.title}
              </h1>
              <p className="mt-1 text-xl font-semibold tracking-[-0.03em] text-black md:text-[2rem]">
                {competition.description}
              </p>
            </div>
            <Button
              className="h-12 rounded-full bg-[#1f1f1f] px-8 text-sm font-semibold hover:bg-[#111111]"
              onClick={() => {
                if (!user) {
                  router.push(`/login?next=/competitions/${competition.slug}`);
                  return;
                }

                setActiveTab("submissions");
              }}
            >
              Submit Prediction
            </Button>
          </section>

          {resourceMessage ? (
            <div className="mt-6 rounded-2xl border border-[#ececec] bg-[#fafafa] px-4 py-3 text-sm text-[#555555]">
              {resourceMessage}
            </div>
          ) : null}

          <section className="mt-8 flex justify-start lg:mt-6 lg:justify-center">
            <div className="flex flex-wrap items-center gap-1 rounded-[10px] bg-[#f2f2f2] p-1">
              {competitionTabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={cn(
                    "rounded-[8px] px-3 py-1.5 text-xs font-medium text-[#2b2b2b] transition-colors",
                    activeTab === tab.id
                      ? "bg-white shadow-[0_1px_1px_rgba(0,0,0,0.06)]"
                      : "hover:bg-white/60",
                  )}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </section>

          <section className="mt-8">
            {activeTab === "overview" ? (
              <OverviewTab
                competition={competition}
                leaderboardCount={publicLeaderboard.length}
                selectedPhase={selectedPhase}
                submissionCount={submissions.length}
                user={user}
              />
            ) : null}

            {activeTab === "data" ? (
              <DataTab
                competitionSlug={competition.slug}
                datasets={datasets}
                user={user}
              />
            ) : null}

            {activeTab === "leaderboard" ? (
              <LeaderboardTab
                competition={competition}
                entries={visibleLeaderboard}
                leaderboardVisibility={leaderboardVisibility}
                onVisibilityChange={setLeaderboardVisibility}
              />
            ) : null}

            {activeTab === "rules" ? (
              <RulesTab competition={competition} selectedPhase={selectedPhase} />
            ) : null}

            {activeTab === "submissions" ? (
              <SubmissionsTab
                activeJob={activeJob}
                busy={busy}
                competition={competition}
                fileInputKey={fileInputKey}
                slug={competition.slug}
                submissionFile={submissionFile}
                submissionType={submissionType}
                submissions={submissions}
                user={user}
                onFileChange={setSubmissionFile}
                onSubmit={handleSubmission}
                onTypeChange={setSubmissionType}
              />
            ) : null}
          </section>
        </div>
      </main>
    </div>
  );
}

function OverviewTab({
  competition,
  leaderboardCount,
  selectedPhase,
  submissionCount,
  user,
}: {
  competition: Competition;
  leaderboardCount: number;
  selectedPhase: Competition["phases"][number] | null;
  submissionCount: number;
  user: User | null;
}) {
  return (
    <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
      <Panel>
        <PanelHeader
          description="The competition brief, evaluation setup, and important dates stay visible in one place."
          title="Competition Overview"
        />
        <div className="space-y-8 px-6 pb-6 pt-1">
          <ContentBlock
            body={competition.description}
            title="Description"
          />
          <ContentBlock
            body={`This Phase 1 competition accepts ${allowedSubmissionText(competition)}. Scores are computed with the ${competition.scoring_metric} metric, and ${competition.scoring_direction === "max" ? "higher" : "lower"} scores rank first.`}
            title="Evaluation"
          />
          <ContentBlock
            body={
              selectedPhase
                ? `${formatDate(selectedPhase.starts_at)} to ${formatDate(selectedPhase.ends_at)}. Rules version ${selectedPhase.rules_version} and scoring version ${selectedPhase.scoring_version} are currently active.`
                : "No active phase has been scheduled yet."
            }
            title="Timeline"
          />
        </div>
      </Panel>

      <div className="space-y-6">
        <Panel>
          <PanelHeader
            description="Quick competition metadata, closer to a Kaggle sidebar but kept in the lighter current visual language."
            title="Workspace Summary"
          />
          <div className="grid gap-3 px-6 pb-6 pt-1">
            <InfoRow label="Host" value="Pelatnas Competition" />
            <InfoRow label="Visibility" value={competition.visibility} />
            <InfoRow label="Participants on leaderboard" value={String(leaderboardCount)} />
            <InfoRow label="Your submissions" value={user ? String(submissionCount) : "Sign in to see"} />
            <InfoRow
              label="Accepted formats"
              value={allowedSubmissionText(competition)}
            />
          </div>
        </Panel>

        <Panel>
          <PanelHeader
            description="Current competition limits come directly from the backend competition model."
            title="Limits"
          />
          <div className="grid gap-3 px-6 pb-6 pt-1">
            <InfoRow
              label="Daily submissions"
              value={`${competition.max_submissions_per_day} per day`}
            />
            <InfoRow label="Runtime" value={`${competition.max_runtime_minutes} minutes`} />
            <InfoRow label="Memory" value={`${competition.max_memory_mb} MB`} />
            <InfoRow label="CPU" value={`${competition.max_cpu} CPU`} />
          </div>
        </Panel>
      </div>
    </div>
  );
}

function DataTab({
  competitionSlug,
  datasets,
  user,
}: {
  competitionSlug: string;
  datasets: Dataset[];
  user: User | null;
}) {
  if (!user) {
    return (
      <LockedPanel
        body="The backend requires an authenticated session for dataset history and downloads. Sign in to inspect versions and retrieve files."
        ctaHref={`/login?next=/competitions/${competitionSlug}`}
        ctaLabel="Login to access data"
        title="Data access requires sign-in"
      />
    );
  }

  const activeDataset = datasets.find((dataset) => dataset.is_active) ?? null;

  return (
    <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <Panel>
        <PanelHeader
          description="Dataset history remains visible in Phase 1, with the latest version marked active."
          title="Dataset Versions"
        />
        <div className="px-6 pb-6 pt-1">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Version</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>File</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Download</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datasets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-sm text-[#757575]">
                    No dataset versions have been uploaded yet.
                  </TableCell>
                </TableRow>
              ) : (
                datasets.map((dataset) => (
                  <TableRow key={dataset.id}>
                    <TableCell className="font-medium text-[#111111]">
                      v{dataset.version}
                    </TableCell>
                    <TableCell>{dataset.name}</TableCell>
                    <TableCell>
                      <div className="font-medium text-[#111111]">
                        {dataset.original_filename}
                      </div>
                      <div className="mt-1 text-xs text-[#7a7a7a]">
                        {dataset.content_type} · {formatBytes(dataset.size_bytes)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={dataset.is_active ? "secondary" : "outline"}
                        className={
                          dataset.is_active
                            ? "border-0 bg-[#f2f2f2] text-[#222222]"
                            : "border-[#e7e7e7] text-[#666666]"
                        }
                      >
                        {dataset.is_active ? "Active" : "Archived"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <a
                        className="text-sm font-medium text-[#111111] underline-offset-4 hover:underline"
                        href={`${apiOrigin}/api/v1/datasets/${dataset.id}/download`}
                      >
                        Download
                      </a>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Panel>

      <div className="space-y-6">
        <Panel>
          <PanelHeader
            description="A compact sidebar block, similar to Kaggle's right rail, for the current active data release."
            title="Current Release"
          />
          <div className="grid gap-3 px-6 pb-6 pt-1">
            <InfoRow
              label="Active version"
              value={activeDataset ? `v${activeDataset.version}` : "No active version"}
            />
            <InfoRow
              label="Primary file"
              value={activeDataset?.original_filename ?? "No file available"}
            />
            <InfoRow
              label="Checksum"
              value={activeDataset ? truncateChecksum(activeDataset.checksum) : "-"}
            />
            <InfoRow
              label="Uploaded"
              value={activeDataset ? formatDateTime(activeDataset.created_at) : "-"}
            />
          </div>
        </Panel>

        <Panel>
          <PanelHeader
            description="Backend and guidelines both treat old dataset versions as visible history."
            title="Access Notes"
          />
          <div className="space-y-3 px-6 pb-6 pt-1 text-sm leading-6 text-[#5d5d5d]">
            <p>Datasets are permanent in Phase 1.</p>
            <p>Each new upload becomes the active version and archives the previous one.</p>
            <p>Downloads use the authenticated dataset endpoint from the backend API.</p>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function LeaderboardTab({
  competition,
  entries,
  leaderboardVisibility,
  onVisibilityChange,
}: {
  competition: Competition;
  entries: LeaderboardEntry[];
  leaderboardVisibility: LeaderboardVisibility;
  onVisibilityChange: (visibility: LeaderboardVisibility) => void;
}) {
  return (
    <div className="space-y-6">
      <Panel>
        <div className="flex flex-col gap-4 border-b border-[#efefef] px-6 py-5 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-black">Leaderboard</h2>
            <p className="mt-1 text-sm leading-6 text-[#6b6b6b]">
              Rankings come from persisted leaderboard projections. The current backend exposes both public and private views.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-[#f3f3f3] p-1">
            <button
              type="button"
              className={toggleClass(leaderboardVisibility === "public")}
              onClick={() => onVisibilityChange("public")}
            >
              Public
            </button>
            <button
              type="button"
              className={toggleClass(leaderboardVisibility === "private")}
              onClick={() => onVisibilityChange("private")}
            >
              Private
            </button>
          </div>
        </div>
        <div className="grid gap-4 border-b border-[#efefef] px-6 py-5 md:grid-cols-3">
          <MetricCard label="Projection" value={leaderboardVisibility} />
          <MetricCard label="Ranking rule" value={competition.best_submission_rule} />
          <MetricCard label="Metric direction" value={competition.scoring_direction} />
        </div>
        <div className="px-6 pb-6 pt-3">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rank</TableHead>
                <TableHead>Participant</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Best Submission</TableHead>
                <TableHead>Submitted</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-sm text-[#757575]">
                    No ranked submissions are available in this projection yet.
                  </TableCell>
                </TableRow>
              ) : (
                entries.map((entry) => (
                  <TableRow key={`${leaderboardVisibility}-${entry.best_submission_id}`}>
                    <TableCell className="font-semibold text-[#111111]">
                      {entry.rank ?? "-"}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium text-[#111111]">
                        {entry.submitter_name}
                      </div>
                      <div className="mt-1 text-xs text-[#7a7a7a]">
                        {entry.submitter_email}
                      </div>
                    </TableCell>
                    <TableCell>{formatScore(entry.score_value)}</TableCell>
                    <TableCell className="font-mono text-xs text-[#555555]">
                      {entry.best_submission_id.slice(0, 8)}
                    </TableCell>
                    <TableCell>{formatDateTime(entry.submission_created_at)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Panel>
    </div>
  );
}

function RulesTab({
  competition,
  selectedPhase,
}: {
  competition: Competition;
  selectedPhase: Competition["phases"][number] | null;
}) {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <Panel>
        <PanelHeader
          description="Rules and limits reflect the current competition schema and Phase 1 platform constraints."
          title="Submission Policy"
        />
        <div className="grid gap-3 px-6 pb-6 pt-1">
          <InfoRow
            label="Formats"
            value={allowedSubmissionText(competition)}
          />
          <InfoRow
            label="Daily limit"
            value={`${competition.max_submissions_per_day} submissions per day`}
          />
          <InfoRow
            label="Phase limit"
            value={
              selectedPhase
                ? `${selectedPhase.submission_limit_per_day} submissions per day in ${selectedPhase.name}`
                : "No active phase configured"
            }
          />
          <InfoRow label="Best submission rule" value={competition.best_submission_rule} />
          <InfoRow label="Visibility" value={competition.visibility} />
        </div>
      </Panel>

      <Panel>
        <PanelHeader
          description="Execution constraints are intentionally simple in the MVP and mirror the product guidelines."
          title="Execution Environment"
        />
        <div className="grid gap-3 px-6 pb-6 pt-1">
          <InfoRow label="Runtime" value={`${competition.max_runtime_minutes} minutes`} />
          <InfoRow label="Memory" value={`${competition.max_memory_mb} MB`} />
          <InfoRow label="CPU" value={`${competition.max_cpu} CPU`} />
          <InfoRow label="Internet access" value="Disabled" />
          <InfoRow label="Dockerfiles" value="Custom Dockerfiles are not allowed" />
        </div>
      </Panel>

      <Panel>
        <PanelHeader
          description="Scoring is competition-specific and rankings are read from persisted score records, not recomputed ad hoc."
          title="Scoring and Ranking"
        />
        <div className="grid gap-3 px-6 pb-6 pt-1">
          <InfoRow label="Metric" value={competition.scoring_metric} />
          <InfoRow label="Direction" value={competition.scoring_direction} />
          <InfoRow
            label="Scoring version"
            value={selectedPhase?.scoring_version ?? "v1"}
          />
          <InfoRow
            label="Tie-break default"
            value="Submission time"
          />
        </div>
      </Panel>

      <Panel>
        <PanelHeader
          description="Retention stays explicit so participants know what persists beyond the run itself."
          title="Retention"
        />
        <div className="grid gap-3 px-6 pb-6 pt-1">
          <InfoRow label="Source archives" value={`${competition.source_retention_days} days`} />
          <InfoRow label="Logs" value={`${competition.log_retention_days} days`} />
          <InfoRow label="Artifacts" value={`${competition.artifact_retention_days} days`} />
          <InfoRow label="Datasets" value="Permanent" />
          <InfoRow label="Best submissions" value="Permanent" />
        </div>
      </Panel>
    </div>
  );
}

function SubmissionsTab({
  activeJob,
  busy,
  competition,
  fileInputKey,
  slug,
  submissionFile,
  submissionType,
  submissions,
  user,
  onFileChange,
  onSubmit,
  onTypeChange,
}: {
  activeJob: Job | null;
  busy: boolean;
  competition: Competition;
  fileInputKey: number;
  slug: string;
  submissionFile: File | null;
  submissionType: string;
  submissions: Submission[];
  user: User | null;
  onFileChange: (file: File | null) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onTypeChange: (value: string) => void;
}) {
  if (!user) {
    return (
      <LockedPanel
        body="Submission history and upload actions are tied to the authenticated user. Sign in to submit a CSV or notebook file and monitor its job lifecycle."
        ctaHref={`/login?next=/competitions/${slug}`}
        ctaLabel="Login to submit"
        title="Submissions require sign-in"
      />
    );
  }

  const allowedTypes = [
    competition.allow_csv_submissions ? "csv" : null,
    competition.allow_notebook_submissions ? "notebook" : null,
  ].filter(Boolean) as string[];

  return (
    <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
      <Panel>
        <PanelHeader
          description="A direct Phase 1 submission flow: choose a type, upload a file, and watch the job move through queueing and scoring."
          title="New Submission"
        />
        <div className="space-y-6 px-6 pb-6 pt-1">
          <form className="space-y-5" onSubmit={onSubmit}>
            <Field label="Submission type">
              <select
                className="h-10 w-full rounded-xl border border-[#e7e7e7] bg-white px-3 text-sm text-[#111111] outline-none transition focus:border-[#111111]"
                onChange={(event) => onTypeChange(event.target.value)}
                value={submissionType}
              >
                {allowedTypes.map((type) => (
                  <option key={type} value={type}>
                    {type === "csv" ? "CSV file" : "Jupyter notebook"}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Source file">
              <Input
                key={fileInputKey}
                accept={submissionType === "csv" ? ".csv" : ".ipynb"}
                className="h-10 rounded-xl border-[#e7e7e7] bg-white px-3 text-sm shadow-none file:mr-3 file:rounded-full file:border-0 file:bg-[#f3f3f3] file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-[#111111]"
                onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
                type="file"
              />
              {submissionFile ? (
                <p className="mt-2 text-xs text-[#6d6d6d]">
                  {submissionFile.name} selected
                </p>
              ) : null}
            </Field>

            <Button
              className="h-10 rounded-full bg-[#1f1f1f] px-5 text-xs font-semibold hover:bg-[#111111]"
              disabled={busy}
              type="submit"
            >
              {busy ? "Submitting..." : "Confirm Submission"}
            </Button>
          </form>

          <div className="rounded-2xl border border-[#ececec] bg-[#fafafa] px-4 py-4">
            <h3 className="text-sm font-semibold text-[#111111]">Job Status</h3>
            <JobRail activeJob={activeJob} />
            <div className="mt-4 grid gap-3">
              <InfoRow
                label="Current state"
                value={activeJob ? activeJob.status : "No active job"}
              />
              <InfoRow
                label="Worker"
                value={activeJob?.worker_id ?? "Pending assignment"}
              />
              <InfoRow
                label="Failure"
                value={activeJob?.failure_reason ?? "No failure recorded"}
              />
            </div>
          </div>
        </div>
      </Panel>

      <Panel>
        <PanelHeader
          description="Your submission history comes from the authenticated submissions endpoint and reflects the latest score and job state."
          title="My Submissions"
        />
        <div className="px-6 pb-6 pt-1">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Submitted</TableHead>
                <TableHead>Logs</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {submissions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-sm text-[#757575]">
                    No submissions recorded yet.
                  </TableCell>
                </TableRow>
              ) : (
                submissions.map((submission) => (
                  <TableRow key={submission.id}>
                    <TableCell>
                      <div className="font-medium text-[#111111]">
                        {submission.source_original_filename}
                      </div>
                      <div className="mt-1 text-xs text-[#7a7a7a]">
                        {submission.submission_type.toUpperCase()} · {submission.id.slice(0, 8)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={submission.status} />
                    </TableCell>
                    <TableCell>
                      {submission.latest_score
                        ? formatScore(submission.latest_score.score_value)
                        : "Pending"}
                    </TableCell>
                    <TableCell>{formatDateTime(submission.created_at)}</TableCell>
                    <TableCell>
                      <a
                        className="text-sm font-medium text-[#111111] underline-offset-4 hover:underline"
                        href={`${apiOrigin}/api/v1/submissions/${submission.id}/logs`}
                        rel="noreferrer"
                        target="_blank"
                      >
                        View logs
                      </a>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Panel>
    </div>
  );
}

function Panel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-2xl border border-[#ececec] bg-white", className)}>
      {children}
    </div>
  );
}

function PanelHeader({
  description,
  title,
}: {
  description: string;
  title: string;
}) {
  return (
    <div className="border-b border-[#efefef] px-6 py-5">
      <h2 className="text-lg font-semibold text-black">{title}</h2>
      <p className="mt-1 text-sm leading-6 text-[#6b6b6b]">{description}</p>
    </div>
  );
}

function ContentBlock({
  body,
  title,
}: {
  body: string;
  title: string;
}) {
  return (
    <article>
      <h3 className="text-base font-semibold text-black">{title}</h3>
      <p className="mt-2 text-sm leading-7 text-[#111111]">{body}</p>
    </article>
  );
}

function InfoRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-xl bg-[#fafafa] px-4 py-3">
      <span className="text-xs font-medium uppercase tracking-[0.14em] text-[#8a8a8a]">
        {label}
      </span>
      <span className="text-right text-sm font-medium text-[#171717]">{value}</span>
    </div>
  );
}

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-[#ececec] bg-[#fafafa] px-4 py-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#808080]">
        {label}
      </div>
      <div className="mt-2 text-sm font-semibold capitalize text-[#111111]">
        {value.replaceAll("_", " ")}
      </div>
    </div>
  );
}

function Field({
  children,
  label,
}: {
  children: ReactNode;
  label: string;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.14em] text-[#808080]">
        {label}
      </span>
      {children}
    </label>
  );
}

function LockedPanel({
  body,
  ctaHref,
  ctaLabel,
  title,
}: {
  body: string;
  ctaHref: string;
  ctaLabel: string;
  title: string;
}) {
  return (
    <div className="rounded-2xl border border-[#ececec] bg-white px-6 py-6">
      <h2 className="text-lg font-semibold text-black">{title}</h2>
      <p className="mt-2 max-w-2xl text-sm leading-7 text-[#656565]">{body}</p>
      <Button
        asChild
        className="mt-5 h-10 rounded-full bg-[#1f1f1f] px-5 text-xs font-semibold hover:bg-[#111111]"
      >
        <Link href={ctaHref}>{ctaLabel}</Link>
      </Button>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const palette =
    status === "completed"
      ? "border-0 bg-[#ecf8ef] text-[#22693d]"
      : status === "failed" || status === "timed_out" || status === "cancelled"
        ? "border-0 bg-[#fff2f2] text-[#ab4c4c]"
        : "border-0 bg-[#f2f2f2] text-[#555555]";

  return (
    <Badge variant="secondary" className={cn("px-2.5 py-1 capitalize", palette)}>
      {status.replaceAll("_", " ")}
    </Badge>
  );
}

function JobRail({ activeJob }: { activeJob: Job | null }) {
  const steps = ["queued", "running", "scoring", "completed"] as const;
  const currentIndex = !activeJob
    ? -1
    : activeJob.status === "pending"
      ? 0
      : activeJob.status === "collecting"
        ? 2
        : steps.indexOf(
            activeJob.status as (typeof steps)[number],
          );

  return (
    <div className="mt-4 grid gap-3 md:grid-cols-4">
      {steps.map((step, index) => {
        const isActive = currentIndex >= index;
        return (
          <div
            key={step}
            className={cn(
              "rounded-xl border px-3 py-3 text-center text-xs font-semibold uppercase tracking-[0.14em]",
              isActive
                ? "border-[#111111] bg-[#111111] text-white"
                : "border-[#e7e7e7] bg-white text-[#8a8a8a]",
            )}
          >
            {step}
          </div>
        );
      })}
    </div>
  );
}

function allowedSubmissionText(competition: Competition) {
  if (competition.allow_csv_submissions && competition.allow_notebook_submissions) {
    return "CSV files and Jupyter notebooks";
  }

  if (competition.allow_csv_submissions) {
    return "CSV files";
  }

  if (competition.allow_notebook_submissions) {
    return "Jupyter notebooks";
  }

  return "No submission formats";
}

function truncateChecksum(value: string) {
  return value.length <= 12 ? value : `${value.slice(0, 12)}...`;
}

function formatBytes(value: number) {
  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatScore(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(4);
}

function toggleClass(active: boolean) {
  return cn(
    "rounded-full px-3 py-1.5 text-xs font-semibold transition-colors",
    active ? "bg-white text-[#111111] shadow-[0_1px_1px_rgba(0,0,0,0.06)]" : "text-[#666666]",
  );
}
