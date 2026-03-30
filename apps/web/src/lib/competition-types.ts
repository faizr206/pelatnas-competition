export type User = {
  id: string;
  email: string;
  display_name: string;
  status: string;
  is_admin: boolean;
};

export type CompetitionPhase = {
  id: string;
  name: string;
  starts_at: string;
  ends_at: string;
  submission_limit_per_day: number;
  scoring_version: string;
  rules_version: string;
};

export type Competition = {
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

export type Dataset = {
  id: string;
  competition_id: string;
  name: string;
  version: number;
  storage_path: string;
  checksum: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  is_active: boolean;
  created_at: string;
};

export type Job = {
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

export type Submission = {
  id: string;
  competition_id: string;
  phase_id: string;
  user_id: string;
  submission_type: string;
  status: string;
  source_archive_path: string;
  source_original_filename: string;
  source_content_type: string;
  source_checksum: string;
  source_size_bytes: number;
  created_at: string;
  latest_score: {
    metric_name: string;
    metric_value: number;
    score_value: number;
    scoring_version: string;
  } | null;
  latest_job: Job | null;
};

export type LeaderboardEntry = {
  rank: number | null;
  score_value: number;
  user_id: string;
  best_submission_id: string;
  submission_created_at: string;
  submitter_email: string;
  submitter_name: string;
};

export type CompetitionTab =
  | "overview"
  | "data"
  | "leaderboard"
  | "rules"
  | "submissions";

export type LeaderboardVisibility = "public" | "private";

export const competitionTabs: Array<{
  id: CompetitionTab;
  label: string;
}> = [
  { id: "overview", label: "Overview" },
  { id: "data", label: "Data" },
  { id: "leaderboard", label: "Leaderboard" },
  { id: "rules", label: "Rules" },
  { id: "submissions", label: "Submissions" },
];

export const activeJobStatuses = new Set([
  "pending",
  "queued",
  "running",
  "collecting",
  "scoring",
]);
