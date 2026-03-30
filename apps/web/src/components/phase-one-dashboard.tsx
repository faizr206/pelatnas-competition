"use client";

import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowLeft,
  Database,
  FileSpreadsheet,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Package2,
  PlayCircle,
  ShieldCheck,
  TerminalSquare,
  Trophy,
  Upload,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type PageMode = "home" | "competition" | "admin";
type WorkspaceTab =
  | "overview"
  | "data"
  | "code"
  | "models"
  | "discussion"
  | "leaderboard"
  | "rules"
  | "submissions";
type LeaderboardVisibility = "public" | "private";

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
  scoring_metric: string;
  scoring_direction: string;
  best_submission_rule: string;
  max_submissions_per_day: number;
  max_runtime_minutes: number;
  max_memory_mb: number;
  max_cpu: number;
  allow_csv_submissions: boolean;
  allow_notebook_submissions: boolean;
  source_retention_days: number;
  log_retention_days: number;
  artifact_retention_days: number;
  phases: CompetitionPhase[];
};

type Dataset = {
  id: string;
  name: string;
  version: number;
  checksum: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  is_active: boolean;
  created_at: string;
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

type Submission = {
  id: string;
  submission_type: string;
  status: string;
  source_original_filename: string;
  source_size_bytes: number;
  source_checksum: string;
  created_at: string;
  latest_score: {
    metric_name: string;
    metric_value: number;
    score_value: number;
    scoring_version: string;
  } | null;
  latest_job: Job | null;
};

type LeaderboardEntry = {
  rank: number | null;
  score_value: number;
  user_id: string;
  best_submission_id: string;
  submission_created_at: string;
  submitter_email: string;
  submitter_name: string;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const apiOrigin = apiBaseUrl.replace(/\/api\/v1$/, "");

const scoringMetricOptions = [
  "row_count",
  "numeric_sum",
  "mean_value",
  "file_size_kb",
  "notebook_code_cells",
  "checksum_mod_1000",
];

const adminSections = [
  "Dashboard",
  "Competitions",
  "Datasets",
  "Submissions",
  "Workers",
  "Users",
  "Logs",
];

export function PhaseOneDashboard() {
  const [pageMode, setPageMode] = useState<PageMode>("home");
  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>("overview");
  const [leaderboardVisibility, setLeaderboardVisibility] =
    useState<LeaderboardVisibility>("public");
  const [user, setUser] = useState<User | null>(null);
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [selectedCompetitionSlug, setSelectedCompetitionSlug] = useState("");
  const [activeJob, setActiveJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin1234");
  const [datasetName, setDatasetName] = useState("starter-dataset");
  const [datasetFile, setDatasetFile] = useState<File | null>(null);
  const [submissionType, setSubmissionType] = useState("csv");
  const [submissionFile, setSubmissionFile] = useState<File | null>(null);
  const [competitionForm, setCompetitionForm] = useState(() => ({
    slug: "phase1-demo",
    title: "Phase 1 Demo Competition",
    description:
      "Single-phase MVP competition for CSV and notebook submissions.",
    scoring_metric: "row_count",
    scoring_direction: "max",
    starts_at: formatForDatetimeLocal(new Date()),
    ends_at: formatForDatetimeLocal(
      new Date(Date.now() + 1000 * 60 * 60 * 24 * 30),
    ),
  }));

  const selectedCompetition =
    competitions.find((competition) => competition.slug === selectedCompetitionSlug) ??
    null;
  const selectedPhase = selectedCompetition?.phases[0] ?? null;
  const canSeeLeaderboard = Boolean(user?.is_admin || submissions.length > 0);

  const activeCompetitions = useMemo(
    () => competitions.filter((competition) => competition.status === "active"),
    [competitions],
  );

  const loadCompetitions = useCallback(async () => {
    const response = await fetch(`${apiBaseUrl}/competitions`, {
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error("Failed to load competitions.");
    }

    const data = (await response.json()) as Competition[];
    setCompetitions(data);
    setSelectedCompetitionSlug((current) => {
      if (current && data.some((competition) => competition.slug === current)) {
        return current;
      }
      return data[0]?.slug ?? "";
    });
  }, []);

  const loadSession = useCallback(async () => {
    const response = await fetch(`${apiBaseUrl}/auth/me`, {
      credentials: "include",
    });

    if (!response.ok) {
      setUser(null);
      return;
    }

    const currentUser = (await response.json()) as User;
    setUser(currentUser);
  }, []);

  const loadCompetitionResources = useCallback(
    async (slug: string, visibility: LeaderboardVisibility) => {
      if (!user) {
        setDatasets([]);
        setSubmissions([]);
        setLeaderboard([]);
        return;
      }

      const leaderboardPath =
        visibility === "private"
          ? `${apiBaseUrl}/competitions/${slug}/leaderboard/private`
          : `${apiBaseUrl}/competitions/${slug}/leaderboard/public`;

      const [datasetsResponse, submissionsResponse, leaderboardResponse] =
        await Promise.all([
          fetch(`${apiBaseUrl}/competitions/${slug}/datasets`, {
            credentials: "include",
          }),
          fetch(`${apiBaseUrl}/competitions/${slug}/submissions`, {
            credentials: "include",
          }),
          fetch(leaderboardPath, {
            credentials: "include",
          }),
        ]);

      if (!datasetsResponse.ok || !submissionsResponse.ok || !leaderboardResponse.ok) {
        throw new Error("Failed to load competition workspace.");
      }

      setDatasets((await datasetsResponse.json()) as Dataset[]);
      setSubmissions((await submissionsResponse.json()) as Submission[]);
      setLeaderboard((await leaderboardResponse.json()) as LeaderboardEntry[]);
    },
    [user],
  );

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        await Promise.all([loadCompetitions(), loadSession()]);
      } catch (requestError) {
        setError(getErrorMessage(requestError));
      } finally {
        setLoading(false);
      }
    })();
  }, [loadCompetitions, loadSession]);

  useEffect(() => {
    if (!selectedCompetitionSlug || !user) {
      return;
    }

    void (async () => {
      try {
        await loadCompetitionResources(selectedCompetitionSlug, leaderboardVisibility);
      } catch (requestError) {
        setError(getErrorMessage(requestError));
      }
    })();
  }, [leaderboardVisibility, loadCompetitionResources, selectedCompetitionSlug, user]);

  const refreshJob = useCallback(
    async (jobId: string) => {
      try {
        const job = await apiJson<Job>(`${apiBaseUrl}/jobs/${jobId}`, {
          credentials: "include",
        });
        setActiveJob(job);

        if (
          selectedCompetitionSlug &&
          ["completed", "failed", "cancelled", "timed_out"].includes(job.status)
        ) {
          await loadCompetitionResources(selectedCompetitionSlug, leaderboardVisibility);
        }

        if (job.status === "completed") {
          setMessage(`Job ${job.id} completed successfully.`);
        }
        if (job.status === "failed") {
          setError(job.failure_reason ?? "Job failed.");
        }
      } catch (requestError) {
        setError(getErrorMessage(requestError));
      }
    },
    [leaderboardVisibility, loadCompetitionResources, selectedCompetitionSlug],
  );

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
  }, [activeJob, refreshJob]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    setError(null);

    try {
      await apiJson<User>(`${apiBaseUrl}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      await Promise.all([loadSession(), loadCompetitions()]);
      setMessage("Session established.");
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function handleLogout() {
    setBusy(true);
    setMessage(null);
    setError(null);

    try {
      await fetch(`${apiBaseUrl}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      setUser(null);
      setDatasets([]);
      setSubmissions([]);
      setLeaderboard([]);
      setActiveJob(null);
      setPageMode("home");
      setWorkspaceTab("overview");
      setMessage("Session cleared.");
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateCompetition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    setError(null);

    try {
      const competition = await apiJson<Competition>(`${apiBaseUrl}/competitions`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slug: competitionForm.slug,
          title: competitionForm.title,
          description: competitionForm.description,
          visibility: "public",
          status: "active",
          scoring_metric: competitionForm.scoring_metric,
          scoring_direction: competitionForm.scoring_direction,
          phase: {
            name: "main",
            starts_at: new Date(competitionForm.starts_at).toISOString(),
            ends_at: new Date(competitionForm.ends_at).toISOString(),
            submission_limit_per_day: 5,
            scoring_version: "v1",
            rules_version: "v1",
          },
        }),
      });
      await loadCompetitions();
      setSelectedCompetitionSlug(competition.slug);
      setMessage(`Competition ${competition.title} created.`);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function handleUploadDataset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCompetitionSlug || !datasetFile) {
      setError("Choose a competition and dataset file first.");
      return;
    }

    setBusy(true);
    setMessage(null);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("name", datasetName);
      formData.append("dataset_file", datasetFile);
      await apiJson<Dataset>(`${apiBaseUrl}/competitions/${selectedCompetitionSlug}/datasets`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      await loadCompetitionResources(selectedCompetitionSlug, leaderboardVisibility);
      setDatasetFile(null);
      setMessage("Dataset uploaded and marked active.");
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmitFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCompetitionSlug || !submissionFile) {
      setError("Choose a competition and submission file first.");
      return;
    }

    setBusy(true);
    setMessage(null);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("submission_type", submissionType);
      formData.append("source_file", submissionFile);
      const job = await apiJson<Job>(
        `${apiBaseUrl}/competitions/${selectedCompetitionSlug}/submissions`,
        {
          method: "POST",
          credentials: "include",
          body: formData,
        },
      );
      setActiveJob(job);
      setSubmissionFile(null);
      setMessage(`Submission accepted. Job ${job.id} is ${job.status}.`);
      await loadCompetitionResources(selectedCompetitionSlug, leaderboardVisibility);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  function openCompetition(slug: string, tab: WorkspaceTab = "overview") {
    if (!user) {
      setError("Sign in first to open the competition workspace.");
      return;
    }
    setSelectedCompetitionSlug(slug);
    setWorkspaceTab(tab);
    setPageMode("competition");
  }

  function handleTopNavigation(target: "home" | "datasets" | "submissions" | "admin") {
    if (target === "home") {
      setPageMode("home");
      return;
    }

    if (target === "admin") {
      if (user?.is_admin) {
        setPageMode("admin");
      }
      return;
    }

    if (!selectedCompetitionSlug && competitions[0]) {
      setSelectedCompetitionSlug(competitions[0].slug);
    }

    if (!selectedCompetitionSlug && !competitions[0]) {
      setError("No competition is available yet.");
      return;
    }

    setPageMode("competition");
    setWorkspaceTab(target === "datasets" ? "data" : "submissions");
  }

  return (
    <main className="dashboard-shell">
      <TopNavigation
        loading={loading}
        pageMode={pageMode}
        user={user}
        onNavigate={handleTopNavigation}
        onLogout={handleLogout}
      />

      <Notice className="mt-6" error={error} message={message} />

      {pageMode === "home" ? (
        <HomeView
          activeCompetitions={activeCompetitions}
          busy={busy}
          competitions={competitions}
          email={email}
          loading={loading}
          password={password}
          user={user}
          onEmailChange={setEmail}
          onLogin={handleLogin}
          onOpenCompetition={openCompetition}
          onPasswordChange={setPassword}
        />
      ) : null}

      {pageMode === "competition" && selectedCompetition ? (
        <CompetitionWorkspace
          activeJob={activeJob}
          busy={busy}
          canSeeLeaderboard={canSeeLeaderboard}
          datasets={datasets}
          leaderboard={leaderboard}
          leaderboardVisibility={leaderboardVisibility}
          selectedCompetition={selectedCompetition}
          selectedPhase={selectedPhase}
          submissionFile={submissionFile}
          submissionType={submissionType}
          submissions={submissions}
          tab={workspaceTab}
          user={user}
          onBack={() => setPageMode("home")}
          onLeaderboardVisibilityChange={setLeaderboardVisibility}
          onOpenSubmit={() => setWorkspaceTab("submissions")}
          onRefreshJob={refreshJob}
          onSubmissionFileChange={setSubmissionFile}
          onSubmissionSubmit={handleSubmitFile}
          onSubmissionTypeChange={setSubmissionType}
          onTabChange={(value) => setWorkspaceTab(value as WorkspaceTab)}
        />
      ) : null}

      {pageMode === "admin" && user?.is_admin ? (
        <AdminPanel
          activeJob={activeJob}
          busy={busy}
          competitionForm={competitionForm}
          competitions={competitions}
          datasetFile={datasetFile}
          datasetName={datasetName}
          selectedCompetition={selectedCompetition}
          submissions={submissions}
          user={user}
          onCompetitionFormChange={setCompetitionForm}
          onCreateCompetition={handleCreateCompetition}
          onDatasetFileChange={setDatasetFile}
          onDatasetNameChange={setDatasetName}
          onOpenCompetition={openCompetition}
          onUploadDataset={handleUploadDataset}
        />
      ) : null}
    </main>
  );
}

function TopNavigation({
  loading,
  pageMode,
  user,
  onLogout,
  onNavigate,
}: {
  loading: boolean;
  pageMode: PageMode;
  user: User | null;
  onLogout: () => void;
  onNavigate: (target: "home" | "datasets" | "submissions" | "admin") => void;
}) {
  return (
    <header className="sticky top-4 z-20 rounded-[1.7rem] border border-border/70 bg-card/85 shadow-panel backdrop-blur">
      <div className="flex flex-col gap-4 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground">
            PC
          </div>
          <div>
            <div className="text-sm font-semibold tracking-[0.18em] text-primary">
              Pelatnas Competition
            </div>
            <div className="text-xs text-muted-foreground">
              TLX-style entry, Kaggle-style workspace
            </div>
          </div>
        </div>

        <nav className="flex flex-wrap items-center gap-2">
          <TopNavButton active={pageMode === "home"} onClick={() => onNavigate("home")}>
            Home
          </TopNavButton>
          <TopNavButton active={pageMode === "home"} onClick={() => onNavigate("home")}>
            Competitions
          </TopNavButton>
          <TopNavButton
            active={pageMode === "competition"}
            onClick={() => onNavigate("datasets")}
          >
            Datasets
          </TopNavButton>
          <TopNavButton
            active={pageMode === "competition"}
            onClick={() => onNavigate("submissions")}
          >
            Submissions
          </TopNavButton>
          {user?.is_admin ? (
            <TopNavButton active={pageMode === "admin"} onClick={() => onNavigate("admin")}>
              Admin
            </TopNavButton>
          ) : null}
        </nav>

        <div className="flex items-center gap-3">
          <div className="rounded-full border border-border bg-secondary/60 px-3 py-2 text-sm">
            {loading ? "Loading..." : user ? user.display_name : "Guest"}
          </div>
          {user ? (
            <Button onClick={onLogout} size="sm" variant="outline">
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          ) : null}
        </div>
      </div>
    </header>
  );
}

function HomeView({
  activeCompetitions,
  busy,
  competitions,
  email,
  loading,
  password,
  user,
  onEmailChange,
  onLogin,
  onOpenCompetition,
  onPasswordChange,
}: {
  activeCompetitions: Competition[];
  busy: boolean;
  competitions: Competition[];
  email: string;
  loading: boolean;
  password: string;
  user: User | null;
  onEmailChange: (value: string) => void;
  onLogin: (event: FormEvent<HTMLFormElement>) => void;
  onOpenCompetition: (slug: string) => void;
  onPasswordChange: (value: string) => void;
}) {
  return (
    <div className="mt-8 grid gap-8 lg:grid-cols-[1.15fr_0.85fr]">
      <section className="space-y-6">
        <div className="hero-panel p-8 md:p-10">
          <div className="space-y-4">
            <Badge className="w-fit">Home</Badge>
            <p className="text-sm uppercase tracking-[0.26em] text-primary/80">
              Lightweight first view
            </p>
            <h1 className="max-w-4xl text-4xl font-semibold tracking-tight md:text-6xl">
              Browse active competitions without getting hit by rankings first.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
              The entry page stays simple on purpose: discover competitions, read short task
              descriptions, and only move into the full workspace after choosing one.
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Active competitions</CardTitle>
            <CardDescription>
              TLX-style listing: title, short description, status, and one clear action.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(activeCompetitions.length > 0 ? activeCompetitions : competitions).map(
              (competition) => (
                <div
                  className="flex flex-col gap-4 rounded-3xl border border-border/70 bg-card/70 p-5 md:flex-row md:items-center md:justify-between"
                  key={competition.id}
                >
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-lg font-semibold">{competition.title}</h3>
                      <Badge variant="outline">{competition.status}</Badge>
                      <Badge variant="secondary">{daysLeftLabel(competition)}</Badge>
                    </div>
                    <p className="max-w-2xl text-sm text-muted-foreground">
                      {competition.description}
                    </p>
                  </div>
                  <Button onClick={() => onOpenCompetition(competition.slug)}>
                    View Competition
                  </Button>
                </div>
              ),
            )}
          </CardContent>
        </Card>
      </section>

      <section className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>{user ? "Profile" : "Sign in"}</CardTitle>
            <CardDescription>
              {user
                ? "Competition workspace opens after you choose a competition."
                : "Log in to open the competition workspace and submit files."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {user ? (
              <div className="space-y-4">
                <InfoRow label="User" value={user.display_name} />
                <InfoRow label="Email" value={user.email} />
                <InfoRow label="Role" value={user.is_admin ? "Admin" : "Participant"} />
              </div>
            ) : (
              <form className="space-y-5" onSubmit={onLogin}>
                <Field label="Email">
                  <Input
                    type="email"
                    value={email}
                    onChange={(event) => onEmailChange(event.target.value)}
                  />
                </Field>
                <Field label="Password">
                  <Input
                    type="password"
                    value={password}
                    onChange={(event) => onPasswordChange(event.target.value)}
                  />
                </Field>
                <Button className="w-full" disabled={busy || loading} type="submit">
                  {busy ? "Signing in..." : "Login"}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Why the home page is simple</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>No leaderboard here. No rankings. No heavy analytics.</p>
            <p>
              The goal is exploration first, then a richer Kaggle-style workspace after the user
              commits to a competition.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function CompetitionWorkspace({
  activeJob,
  busy,
  canSeeLeaderboard,
  datasets,
  leaderboard,
  leaderboardVisibility,
  selectedCompetition,
  selectedPhase,
  submissionFile,
  submissionType,
  submissions,
  tab,
  user,
  onBack,
  onLeaderboardVisibilityChange,
  onOpenSubmit,
  onRefreshJob,
  onSubmissionFileChange,
  onSubmissionSubmit,
  onSubmissionTypeChange,
  onTabChange,
}: {
  activeJob: Job | null;
  busy: boolean;
  canSeeLeaderboard: boolean;
  datasets: Dataset[];
  leaderboard: LeaderboardEntry[];
  leaderboardVisibility: LeaderboardVisibility;
  selectedCompetition: Competition;
  selectedPhase: CompetitionPhase | null;
  submissionFile: File | null;
  submissionType: string;
  submissions: Submission[];
  tab: WorkspaceTab;
  user: User | null;
  onBack: () => void;
  onLeaderboardVisibilityChange: (value: LeaderboardVisibility) => void;
  onOpenSubmit: () => void;
  onRefreshJob: (jobId: string) => Promise<void>;
  onSubmissionFileChange: (file: File | null) => void;
  onSubmissionSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onSubmissionTypeChange: (value: string) => void;
  onTabChange: (value: string) => void;
}) {
  return (
    <div className="mt-8 space-y-6">
      <section className="hero-panel p-8 md:p-10">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
          <div className="space-y-4">
            <Button onClick={onBack} size="sm" variant="ghost">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{selectedCompetition.status}</Badge>
                <Badge variant="outline">{selectedCompetition.scoring_metric}</Badge>
              </div>
              <h1 className="max-w-4xl text-4xl font-semibold tracking-tight md:text-5xl">
                {selectedCompetition.title}
              </h1>
              <p className="max-w-3xl text-base leading-7 text-muted-foreground">
                {selectedCompetition.description}
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-3 md:flex-row">
            <Button onClick={onOpenSubmit}>
              <Upload className="mr-2 h-4 w-4" />
              Submit
            </Button>
          </div>
        </div>
      </section>

      <Tabs onValueChange={onTabChange} value={tab}>
        <TabsList className="h-auto flex-wrap rounded-3xl p-2">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
          <TabsTrigger value="code">Code</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="discussion">Discussion</TabsTrigger>
          <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
          <TabsTrigger value="rules">Rules</TabsTrigger>
          <TabsTrigger value="submissions">Submissions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <Card>
              <CardHeader>
                <CardTitle>Overview</CardTitle>
                <CardDescription>
                  Kaggle-style competition context after the user commits to a workspace.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <ContentSection
                  body={selectedCompetition.description}
                  title="Competition description"
                />
                <ContentSection
                  body={`Participants submit ${allowedSubmissionText(selectedCompetition)} and are scored by ${selectedCompetition.scoring_metric}.`}
                  title="Task explanation"
                />
                <ContentSection
                  body={`Evaluation uses ${selectedCompetition.scoring_metric} with ${selectedCompetition.scoring_direction === "max" ? "higher scores ranked first" : "lower scores ranked first"}.`}
                  title="Evaluation metric"
                />
                <ContentSection
                  body={
                    selectedPhase
                      ? `${formatDate(selectedPhase.starts_at)} to ${formatDate(selectedPhase.ends_at)}`
                      : "Timeline not configured."
                  }
                  title="Timeline"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Competition sidebar</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <InfoRow label="Host" value="Pelatnas Admin" />
                <InfoRow label="Participants" value={user?.is_admin ? "Admin view" : "Participant"} />
                <InfoRow label="Submission count" value={String(submissions.length)} />
                <InfoRow
                  label="Tags"
                  value={allowedSubmissionText(selectedCompetition).replace(" and ", ", ")}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="data">
          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <Card>
              <CardHeader>
                <CardTitle>Data</CardTitle>
                <CardDescription>
                  Dataset history stays visible while the latest version is active.
                </CardDescription>
              </CardHeader>
              <CardContent>
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
                        <TableCell colSpan={5} className="text-muted-foreground">
                          No dataset versions uploaded yet.
                        </TableCell>
                      </TableRow>
                    ) : (
                      datasets.map((dataset) => (
                        <TableRow key={dataset.id}>
                          <TableCell>v{dataset.version}</TableCell>
                          <TableCell>{dataset.name}</TableCell>
                          <TableCell>{dataset.original_filename}</TableCell>
                          <TableCell>
                            <Badge variant={dataset.is_active ? "default" : "outline"}>
                              {dataset.is_active ? "Active" : "Archived"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <a
                              className="text-primary underline-offset-4 hover:underline"
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
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>File structure preview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {datasets.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Upload a dataset version to preview the current file set.
                  </p>
                ) : (
                  datasets.map((dataset) => (
                    <div
                      className="rounded-2xl border border-border/70 bg-secondary/30 p-4 text-sm"
                      key={dataset.id}
                    >
                      <div className="font-medium">{dataset.original_filename}</div>
                      <div className="mt-1 text-muted-foreground">
                        {dataset.content_type} · {formatBytes(dataset.size_bytes)}
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="code">
          <OptionalPanel
            description="Starter notebooks and example scripts can live here when the repo adds curated starter assets."
            icon={TerminalSquare}
            title="Code tab is optional in v1"
          />
        </TabsContent>

        <TabsContent value="models">
          <OptionalPanel
            description="Model registries and pretrained checkpoints are intentionally deferred beyond the MVP."
            icon={Package2}
            title="Models tab is optional in v1"
          />
        </TabsContent>

        <TabsContent value="discussion">
          <OptionalPanel
            description="Forum threads can be added later without changing the home-to-workspace information architecture."
            icon={MessageSquare}
            title="Discussion is deferred"
          />
        </TabsContent>

        <TabsContent value="leaderboard">
          <Card>
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle>Leaderboard</CardTitle>
                <CardDescription>
                  Best score per user, with public/private projection toggle.
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => onLeaderboardVisibilityChange("public")}
                  size="sm"
                  variant={leaderboardVisibility === "public" ? "default" : "outline"}
                >
                  Public
                </Button>
                <Button
                  onClick={() => onLeaderboardVisibilityChange("private")}
                  size="sm"
                  variant={leaderboardVisibility === "private" ? "default" : "outline"}
                >
                  Private
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {!canSeeLeaderboard ? (
                <div className="rounded-3xl border border-border/70 bg-secondary/30 p-6 text-sm text-muted-foreground">
                  Leaderboard is intentionally hidden until the participant joins the competition.
                  Submit a file first to unlock it.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rank</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>Score</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leaderboard.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} className="text-muted-foreground">
                          No ranked submissions yet.
                        </TableCell>
                      </TableRow>
                    ) : (
                      leaderboard.map((entry) => (
                        <TableRow key={entry.best_submission_id}>
                          <TableCell>{entry.rank ?? "-"}</TableCell>
                          <TableCell>
                            <div className="font-medium">{entry.submitter_name}</div>
                            <div className="text-xs text-muted-foreground">
                              {entry.submitter_email}
                            </div>
                          </TableCell>
                          <TableCell>{entry.score_value}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rules">
          <Card>
            <CardHeader>
              <CardTitle>Rules</CardTitle>
              <CardDescription>
                Keep submission rules explicit, structured, and easy to scan.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <Detail
                label="Submission limits"
                value={`${selectedCompetition.max_submissions_per_day} per day`}
              />
              <Detail
                label="Allowed methods"
                value={allowedSubmissionText(selectedCompetition)}
              />
              <Detail label="Evaluation method" value={selectedCompetition.scoring_metric} />
              <Detail label="Runtime" value={`${selectedCompetition.max_runtime_minutes} minutes`} />
              <Detail label="CPU" value={`${selectedCompetition.max_cpu} CPU`} />
              <Detail label="RAM" value={`${selectedCompetition.max_memory_mb} MB`} />
              <Detail label="Internet" value="Disabled" />
              <Detail label="Dockerfiles" value="Custom Dockerfiles not allowed" />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="submissions">
          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <Card>
              <CardHeader>
                <CardTitle>Submission flow</CardTitle>
                <CardDescription>
                  Upload file or code, confirm the submission, then follow the job state.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <form className="space-y-5" onSubmit={onSubmissionSubmit}>
                  <Field label="1. Upload type">
                    <select
                      className="h-11 w-full rounded-2xl border border-input bg-background/80 px-4 text-sm"
                      onChange={(event) => onSubmissionTypeChange(event.target.value)}
                      value={submissionType}
                    >
                      <option value="csv">CSV</option>
                      <option value="notebook">Jupyter notebook</option>
                    </select>
                  </Field>
                  <Field label="2. File">
                    <Input
                      accept={submissionType === "csv" ? ".csv" : ".ipynb"}
                      onChange={(event) => onSubmissionFileChange(event.target.files?.[0] ?? null)}
                      type="file"
                    />
                  </Field>
                  <Button disabled={busy} type="submit">
                    {busy ? "Submitting..." : "3. Confirm submission"}
                  </Button>
                </form>

                <Card className="border-dashed shadow-none">
                  <CardHeader>
                    <CardTitle className="text-base">Job status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <JobStateRail activeJob={activeJob} />
                    {activeJob ? (
                      <div className="mt-4 space-y-3 text-sm">
                        <InfoRow label="Worker" value={activeJob.worker_id ?? "pending"} />
                        <InfoRow
                          label="Failure"
                          value={activeJob.failure_reason ?? "none"}
                        />
                        <Button
                          onClick={() => void onRefreshJob(activeJob.id)}
                          size="sm"
                          variant="outline"
                        >
                          Refresh job
                        </Button>
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>My submissions</CardTitle>
                <CardDescription>
                  User-specific history with score, status, timestamp, and log access.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Submission ID</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Score</TableHead>
                      <TableHead>Time</TableHead>
                      <TableHead>Logs</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {submissions.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-muted-foreground">
                          No submissions recorded yet.
                        </TableCell>
                      </TableRow>
                    ) : (
                      submissions.map((submission) => (
                        <TableRow key={submission.id}>
                          <TableCell>
                            <div className="font-medium">{submission.id.slice(0, 8)}</div>
                            <div className="text-xs text-muted-foreground">
                              {submission.source_original_filename}
                            </div>
                          </TableCell>
                          <TableCell>
                            <StatusBadge status={submission.status} />
                          </TableCell>
                          <TableCell>
                            {submission.latest_score?.score_value?.toString() ?? "Pending"}
                          </TableCell>
                          <TableCell>{formatDateTime(submission.created_at)}</TableCell>
                          <TableCell>
                            <a
                              className="text-primary underline-offset-4 hover:underline"
                              href={`${apiOrigin}/api/v1/submissions/${submission.id}/logs`}
                              target="_blank"
                              rel="noreferrer"
                            >
                              View logs
                            </a>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function AdminPanel({
  activeJob,
  busy,
  competitionForm,
  competitions,
  datasetFile,
  datasetName,
  selectedCompetition,
  submissions,
  user,
  onCompetitionFormChange,
  onCreateCompetition,
  onDatasetFileChange,
  onDatasetNameChange,
  onOpenCompetition,
  onUploadDataset,
}: {
  activeJob: Job | null;
  busy: boolean;
  competitionForm: {
    slug: string;
    title: string;
    description: string;
    scoring_metric: string;
    scoring_direction: string;
    starts_at: string;
    ends_at: string;
  };
  competitions: Competition[];
  datasetFile: File | null;
  datasetName: string;
  selectedCompetition: Competition | null;
  submissions: Submission[];
  user: User;
  onCompetitionFormChange: (
    value:
      | {
          slug: string;
          title: string;
          description: string;
          scoring_metric: string;
          scoring_direction: string;
          starts_at: string;
          ends_at: string;
        }
      | ((
          current: {
            slug: string;
            title: string;
            description: string;
            scoring_metric: string;
            scoring_direction: string;
            starts_at: string;
            ends_at: string;
          },
        ) => {
          slug: string;
          title: string;
          description: string;
          scoring_metric: string;
          scoring_direction: string;
          starts_at: string;
          ends_at: string;
        }),
  ) => void;
  onCreateCompetition: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onDatasetFileChange: (file: File | null) => void;
  onDatasetNameChange: (value: string) => void;
  onOpenCompetition: (slug: string) => void;
  onUploadDataset: (event: FormEvent<HTMLFormElement>) => Promise<void>;
}) {
  const activeJobs = submissions.filter((submission) =>
    submission.latest_job
      ? !["completed", "failed", "cancelled", "timed_out"].includes(
          submission.latest_job.status,
        )
      : false,
  ).length;
  const failedJobs = submissions.filter(
    (submission) => submission.latest_job?.status === "failed",
  ).length;

  return (
    <div className="mt-8 grid gap-6 xl:grid-cols-[220px_1fr]">
      <Card className="h-fit">
        <CardHeader>
          <CardTitle>Admin</CardTitle>
          <CardDescription>Control-oriented workflow for internal operations.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {adminSections.map((section) => (
            <div
              className="rounded-2xl border border-border/60 bg-secondary/35 px-4 py-3 text-sm"
              key={section}
            >
              {section}
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="space-y-6">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard icon={LayoutDashboard} label="Total competitions" value={String(competitions.length)} />
          <StatCard icon={Activity} label="Active jobs" value={String(activeJobs)} />
          <StatCard icon={TerminalSquare} label="Failed jobs" value={String(failedJobs)} />
          <StatCard
            icon={ShieldCheck}
            label="Worker status"
            value={activeJob?.worker_id ? `online: ${activeJob.worker_id}` : "local / pending"}
          />
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Competition management</CardTitle>
              <CardDescription>
                Create or tune the MVP competition contract: title, description, rules, and limits.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-5" onSubmit={onCreateCompetition}>
                <div className="grid gap-5 md:grid-cols-2">
                  <Field label="Title">
                    <Input
                      value={competitionForm.title}
                      onChange={(event) =>
                        onCompetitionFormChange((current) => ({
                          ...current,
                          title: event.target.value,
                        }))
                      }
                    />
                  </Field>
                  <Field label="Slug">
                    <Input
                      value={competitionForm.slug}
                      onChange={(event) =>
                        onCompetitionFormChange((current) => ({
                          ...current,
                          slug: event.target.value,
                        }))
                      }
                    />
                  </Field>
                </div>
                <Field label="Description">
                  <Textarea
                    value={competitionForm.description}
                    onChange={(event) =>
                      onCompetitionFormChange((current) => ({
                        ...current,
                        description: event.target.value,
                      }))
                    }
                  />
                </Field>
                <div className="grid gap-5 md:grid-cols-2">
                  <Field label="Metric">
                    <select
                      className="h-11 w-full rounded-2xl border border-input bg-background/80 px-4 text-sm"
                      onChange={(event) =>
                        onCompetitionFormChange((current) => ({
                          ...current,
                          scoring_metric: event.target.value,
                        }))
                      }
                      value={competitionForm.scoring_metric}
                    >
                      {scoringMetricOptions.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Direction">
                    <select
                      className="h-11 w-full rounded-2xl border border-input bg-background/80 px-4 text-sm"
                      onChange={(event) =>
                        onCompetitionFormChange((current) => ({
                          ...current,
                          scoring_direction: event.target.value,
                        }))
                      }
                      value={competitionForm.scoring_direction}
                    >
                      <option value="max">Higher is better</option>
                      <option value="min">Lower is better</option>
                    </select>
                  </Field>
                </div>
                <Button disabled={busy} type="submit">
                  {busy ? "Saving..." : "Create competition"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Dataset management</CardTitle>
              <CardDescription>
                Upload dataset versions and keep old versions visible.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-5" onSubmit={onUploadDataset}>
                <Field label="Dataset name">
                  <Input
                    value={datasetName}
                    onChange={(event) => onDatasetNameChange(event.target.value)}
                  />
                </Field>
                <Field label="Dataset file">
                  <Input
                    onChange={(event) => onDatasetFileChange(event.target.files?.[0] ?? null)}
                    type="file"
                  />
                </Field>
                <Button disabled={busy || !selectedCompetition || !datasetFile} type="submit">
                  {busy ? "Uploading..." : "Upload dataset"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <Card>
            <CardHeader>
              <CardTitle>Submission monitoring</CardTitle>
              <CardDescription>
                Focus on visibility first. Retry and cancel controls can be added on top later.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Submission</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Worker</TableHead>
                    <TableHead>Runtime</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {submissions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-muted-foreground">
                        No submission activity yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    submissions.map((submission) => (
                      <TableRow key={submission.id}>
                        <TableCell>{submission.id.slice(0, 8)}</TableCell>
                        <TableCell>{user.display_name}</TableCell>
                        <TableCell>
                          <StatusBadge status={submission.status} />
                        </TableCell>
                        <TableCell>{submission.latest_job?.worker_id ?? "pending"}</TableCell>
                        <TableCell>
                          {runtimeLabel(
                            submission.latest_job?.started_at,
                            submission.latest_job?.finished_at,
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Worker management</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <InfoRow label="Worker name" value={activeJob?.worker_id ?? "worker-local"} />
                <InfoRow label="Status" value={activeJob?.worker_id ? "online" : "pending"} />
                <InfoRow label="CPU usage" value="Tracked later" />
                <InfoRow label="Job count" value={String(activeJobs)} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Users and logs</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <InfoRow label="Admin" value={user.email} />
                <InfoRow label="Participants" value="Derived from submissions later" />
                <InfoRow label="Logs" value="Use job log links from submission monitoring" />
                {selectedCompetition ? (
                  <Button
                    className="w-full"
                    onClick={() => onOpenCompetition(selectedCompetition.slug)}
                    variant="outline"
                  >
                    Open selected competition
                  </Button>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </div>
  );
}

function OptionalPanel({
  description,
  icon: Icon,
  title,
}: {
  description: string;
  icon: typeof TerminalSquare;
  title: string;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-4 p-8">
        <div className="rounded-2xl bg-primary/12 p-3 text-primary">
          <Icon className="h-5 w-5" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-semibold">{title}</h3>
          <p className="max-w-2xl text-sm leading-7 text-muted-foreground">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function JobStateRail({ activeJob }: { activeJob: Job | null }) {
  const states = ["queued", "running", "scoring", "completed"];
  const currentIndex = activeJob ? Math.max(states.indexOf(activeJob.status), 0) : -1;

  return (
    <div className="grid gap-3 md:grid-cols-4">
      {states.map((state, index) => (
        <div
          className={cn(
            "rounded-2xl border px-4 py-3 text-center text-sm",
            index <= currentIndex
              ? "border-primary/40 bg-primary/10 text-primary"
              : "border-border/70 bg-background/70 text-muted-foreground",
          )}
          key={state}
        >
          {state}
        </div>
      ))}
    </div>
  );
}

function TopNavButton({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      className={cn(
        "rounded-full px-4 py-2 text-sm transition-colors",
        active ? "bg-primary text-primary-foreground" : "bg-secondary/60 text-foreground",
      )}
      onClick={onClick}
      type="button"
    >
      {children}
    </button>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2.5">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-border/70 bg-secondary/30 px-4 py-3">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-right">{value}</span>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/70 bg-background/65 p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-2 text-sm font-medium">{value}</div>
    </div>
  );
}

function ContentSection({ body, title }: { body: string; title: string }) {
  return (
    <div className="space-y-2">
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="text-sm leading-7 text-muted-foreground">{body}</p>
    </div>
  );
}

function Notice({
  className,
  error,
  message,
}: {
  className?: string;
  error: string | null;
  message: string | null;
}) {
  if (!message && !error) {
    return null;
  }

  return (
    <div className={cn("space-y-3", className)}>
      {message ? (
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700">
          {message}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Activity;
  label: string;
  value: string;
}) {
  return (
    <Card className="border-none bg-card/80">
      <CardContent className="flex items-start gap-4 p-5">
        <div className="rounded-2xl bg-primary/12 p-3 text-primary">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
            {label}
          </div>
          <div className="mt-2 text-sm font-semibold leading-6">{value}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === "completed"
      ? "default"
      : status === "failed" || status === "timed_out"
        ? "destructive"
        : "outline";

  return <Badge variant={variant}>{status}</Badge>;
}

async function apiJson<T>(input: string, init: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    const body = (await safeJson(response)) as { detail?: string; error?: { message?: string } };
    throw new Error(body.detail ?? body.error?.message ?? "Request failed.");
  }
  return (await response.json()) as T;
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function allowedSubmissionText(competition: Competition): string {
  if (competition.allow_csv_submissions && competition.allow_notebook_submissions) {
    return "CSV and Jupyter notebook";
  }
  if (competition.allow_csv_submissions) {
    return "CSV only";
  }
  if (competition.allow_notebook_submissions) {
    return "Jupyter notebook only";
  }
  return "No submission types enabled";
}

function daysLeftLabel(competition: Competition): string {
  const endsAt = competition.phases[0]?.ends_at;
  if (!endsAt) {
    return "Timeline pending";
  }
  const diff = Math.ceil(
    (new Date(endsAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24),
  );
  if (diff < 0) {
    return "Finished";
  }
  if (diff === 0) {
    return "Ends today";
  }
  return `${diff} days left`;
}

function runtimeLabel(startedAt: string | null | undefined, finishedAt: string | null | undefined) {
  if (!startedAt) {
    return "pending";
  }
  if (!finishedAt) {
    return "running";
  }
  const ms = new Date(finishedAt).getTime() - new Date(startedAt).getTime();
  return `${Math.max(Math.round(ms / 1000), 0)}s`;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected request failure.";
}

function formatBytes(sizeBytes: number): string {
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }
  if (sizeBytes < 1024 * 1024) {
    return `${(sizeBytes / 1024).toFixed(1)} KB`;
  }
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString();
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}

function formatForDatetimeLocal(date: Date): string {
  const adjusted = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return adjusted.toISOString().slice(0, 16);
}
