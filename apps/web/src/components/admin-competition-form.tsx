"use client";

import type { FormEvent, ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type {
  Competition,
  CompetitionCreatePayload,
  CompetitionUpdatePayload,
} from "@/lib/competition-types";

export type CompetitionFormState = {
  slug: string;
  title: string;
  description: string;
  visibility: string;
  status: string;
  scoring_metric: string;
  scoring_direction: string;
  best_submission_rule: string;
  max_submissions_per_day: string;
  max_runtime_minutes: string;
  max_memory_mb: string;
  max_cpu: string;
  allow_csv_submissions: string;
  allow_notebook_submissions: string;
  source_retention_days: string;
  log_retention_days: string;
  artifact_retention_days: string;
  phase_name: string;
  phase_starts_at: string;
  phase_ends_at: string;
  phase_submission_limit_per_day: string;
  phase_scoring_version: string;
  phase_rules_version: string;
};

const inputClassName =
  "h-10 rounded-xl border-[#e7e7e7] bg-white px-3 text-sm shadow-none placeholder:text-[#b1b1b1] focus-visible:ring-1";
const textareaClassName =
  "min-h-[120px] rounded-2xl border-[#e7e7e7] bg-white px-4 py-3 text-sm shadow-none placeholder:text-[#b1b1b1] focus-visible:ring-1";

type CompetitionFormProps = {
  form: CompetitionFormState;
  mode: "create" | "edit";
  message: string | null;
  submitLabel: string;
  onChange: (field: keyof CompetitionFormState, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function AdminCompetitionForm({
  form,
  mode,
  message,
  submitLabel,
  onChange,
  onSubmit,
}: CompetitionFormProps) {
  return (
    <form className="space-y-8" onSubmit={onSubmit}>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Slug">
          <Input
            className={inputClassName}
            disabled={mode === "edit"}
            value={form.slug}
            onChange={(event) => onChange("slug", event.target.value)}
          />
        </Field>
        <Field label="Title">
          <Input
            className={inputClassName}
            value={form.title}
            onChange={(event) => onChange("title", event.target.value)}
          />
        </Field>
        <Field label="Visibility">
          <select
            className={inputClassName}
            value={form.visibility}
            onChange={(event) => onChange("visibility", event.target.value)}
          >
            <option value="public">public</option>
            <option value="private">private</option>
          </select>
        </Field>
        <Field label="Status">
          <select
            className={inputClassName}
            value={form.status}
            onChange={(event) => onChange("status", event.target.value)}
          >
            <option value="draft">draft</option>
            <option value="active">active</option>
            <option value="archived">archived</option>
          </select>
        </Field>
      </section>

      <Field label="Description">
        <Textarea
          className={textareaClassName}
          value={form.description}
          onChange={(event) => onChange("description", event.target.value)}
        />
      </Field>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Scoring metric">
          <Input
            className={inputClassName}
            value={form.scoring_metric}
            onChange={(event) => onChange("scoring_metric", event.target.value)}
          />
        </Field>
        <Field label="Scoring direction">
          <select
            className={inputClassName}
            value={form.scoring_direction}
            onChange={(event) => onChange("scoring_direction", event.target.value)}
          >
            <option value="max">max</option>
            <option value="min">min</option>
          </select>
        </Field>
        <Field label="Best submission rule">
          <Input
            className={inputClassName}
            value={form.best_submission_rule}
            onChange={(event) => onChange("best_submission_rule", event.target.value)}
          />
        </Field>
        <Field label="Phase name">
          <Input
            className={inputClassName}
            value={form.phase_name}
            onChange={(event) => onChange("phase_name", event.target.value)}
          />
        </Field>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Max submissions / day">
          <Input
            className={inputClassName}
            min="1"
            type="number"
            value={form.max_submissions_per_day}
            onChange={(event) => onChange("max_submissions_per_day", event.target.value)}
          />
        </Field>
        <Field label="Phase submissions / day">
          <Input
            className={inputClassName}
            min="1"
            type="number"
            value={form.phase_submission_limit_per_day}
            onChange={(event) =>
              onChange("phase_submission_limit_per_day", event.target.value)
            }
          />
        </Field>
        <Field label="Max runtime minutes">
          <Input
            className={inputClassName}
            min="1"
            type="number"
            value={form.max_runtime_minutes}
            onChange={(event) => onChange("max_runtime_minutes", event.target.value)}
          />
        </Field>
        <Field label="Max memory MB">
          <Input
            className={inputClassName}
            min="256"
            type="number"
            value={form.max_memory_mb}
            onChange={(event) => onChange("max_memory_mb", event.target.value)}
          />
        </Field>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Max CPU">
          <Input
            className={inputClassName}
            min="1"
            type="number"
            value={form.max_cpu}
            onChange={(event) => onChange("max_cpu", event.target.value)}
          />
        </Field>
        <Field label="Source retention days">
          <Input
            className={inputClassName}
            min="1"
            type="number"
            value={form.source_retention_days}
            onChange={(event) => onChange("source_retention_days", event.target.value)}
          />
        </Field>
        <Field label="Log retention days">
          <Input
            className={inputClassName}
            min="1"
            type="number"
            value={form.log_retention_days}
            onChange={(event) => onChange("log_retention_days", event.target.value)}
          />
        </Field>
        <Field label="Artifact retention days">
          <Input
            className={inputClassName}
            min="1"
            type="number"
            value={form.artifact_retention_days}
            onChange={(event) =>
              onChange("artifact_retention_days", event.target.value)
            }
          />
        </Field>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="CSV submissions">
          <select
            className={inputClassName}
            value={form.allow_csv_submissions}
            onChange={(event) => onChange("allow_csv_submissions", event.target.value)}
          >
            <option value="true">enabled</option>
            <option value="false">disabled</option>
          </select>
        </Field>
        <Field label="Notebook submissions">
          <select
            className={inputClassName}
            value={form.allow_notebook_submissions}
            onChange={(event) =>
              onChange("allow_notebook_submissions", event.target.value)
            }
          >
            <option value="true">enabled</option>
            <option value="false">disabled</option>
          </select>
        </Field>
        <Field label="Phase starts at">
          <Input
            className={inputClassName}
            type="datetime-local"
            value={form.phase_starts_at}
            onChange={(event) => onChange("phase_starts_at", event.target.value)}
          />
        </Field>
        <Field label="Phase ends at">
          <Input
            className={inputClassName}
            type="datetime-local"
            value={form.phase_ends_at}
            onChange={(event) => onChange("phase_ends_at", event.target.value)}
          />
        </Field>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Field label="Scoring version">
          <Input
            className={inputClassName}
            value={form.phase_scoring_version}
            onChange={(event) => onChange("phase_scoring_version", event.target.value)}
          />
        </Field>
        <Field label="Rules version">
          <Input
            className={inputClassName}
            value={form.phase_rules_version}
            onChange={(event) => onChange("phase_rules_version", event.target.value)}
          />
        </Field>
      </section>

      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        {message ? (
          <p className="text-sm text-[#555555]">{message}</p>
        ) : (
          <span className="text-sm text-[#8a8a8a]">
            {mode === "create"
              ? "New competitions become available immediately after creation."
              : "Saving updates the competition metadata and the active phase."}
          </span>
        )}
        <Button className="h-10 rounded-full bg-[#1f1f1f] px-5 text-xs font-semibold hover:bg-[#111111]">
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="space-y-2">
      <Label className="text-[11px] uppercase tracking-[0.14em] text-[#666666]">
        {label}
      </Label>
      {children}
    </label>
  );
}

export function createEmptyCompetitionForm(): CompetitionFormState {
  return {
    slug: "",
    title: "",
    description: "",
    visibility: "public",
    status: "draft",
    scoring_metric: "row_count",
    scoring_direction: "max",
    best_submission_rule: "best_score",
    max_submissions_per_day: "5",
    max_runtime_minutes: "20",
    max_memory_mb: "4096",
    max_cpu: "2",
    allow_csv_submissions: "true",
    allow_notebook_submissions: "true",
    source_retention_days: "30",
    log_retention_days: "14",
    artifact_retention_days: "14",
    phase_name: "main",
    phase_starts_at: formatForDateTimeInput(
      new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    ),
    phase_ends_at: formatForDateTimeInput(
      new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    ),
    phase_submission_limit_per_day: "5",
    phase_scoring_version: "v1",
    phase_rules_version: "v1",
  };
}

export function competitionFormFromCompetition(
  competition: Competition,
): CompetitionFormState {
  const phase = competition.phases[0];

  return {
    slug: competition.slug,
    title: competition.title,
    description: competition.description,
    visibility: competition.visibility,
    status: competition.status,
    scoring_metric: competition.scoring_metric,
    scoring_direction: competition.scoring_direction,
    best_submission_rule: competition.best_submission_rule,
    max_submissions_per_day: String(competition.max_submissions_per_day),
    max_runtime_minutes: String(competition.max_runtime_minutes),
    max_memory_mb: String(competition.max_memory_mb),
    max_cpu: String(competition.max_cpu),
    allow_csv_submissions: String(competition.allow_csv_submissions),
    allow_notebook_submissions: String(competition.allow_notebook_submissions),
    source_retention_days: String(competition.source_retention_days),
    log_retention_days: String(competition.log_retention_days),
    artifact_retention_days: String(competition.artifact_retention_days),
    phase_name: phase?.name ?? "main",
    phase_starts_at: formatForDateTimeInput(phase?.starts_at ?? new Date().toISOString()),
    phase_ends_at: formatForDateTimeInput(
      phase?.ends_at ?? new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    ),
    phase_submission_limit_per_day: String(phase?.submission_limit_per_day ?? 5),
    phase_scoring_version: phase?.scoring_version ?? "v1",
    phase_rules_version: phase?.rules_version ?? "v1",
  };
}

export function toCreateCompetitionPayload(
  form: CompetitionFormState,
): CompetitionCreatePayload {
  return {
    slug: form.slug.trim(),
    ...toSharedCompetitionPayload(form),
  };
}

export function toUpdateCompetitionPayload(
  form: CompetitionFormState,
): CompetitionUpdatePayload {
  return toSharedCompetitionPayload(form);
}

function toSharedCompetitionPayload(
  form: CompetitionFormState,
): CompetitionUpdatePayload {
  return {
    title: form.title.trim(),
    description: form.description.trim(),
    visibility: form.visibility,
    status: form.status,
    scoring_metric: form.scoring_metric.trim(),
    scoring_direction: form.scoring_direction,
    best_submission_rule: form.best_submission_rule.trim(),
    max_submissions_per_day: Number(form.max_submissions_per_day),
    max_runtime_minutes: Number(form.max_runtime_minutes),
    max_memory_mb: Number(form.max_memory_mb),
    max_cpu: Number(form.max_cpu),
    allow_csv_submissions: form.allow_csv_submissions === "true",
    allow_notebook_submissions: form.allow_notebook_submissions === "true",
    source_retention_days: Number(form.source_retention_days),
    log_retention_days: Number(form.log_retention_days),
    artifact_retention_days: Number(form.artifact_retention_days),
    phase: {
      name: form.phase_name.trim(),
      starts_at: toIsoString(form.phase_starts_at),
      ends_at: toIsoString(form.phase_ends_at),
      submission_limit_per_day: Number(form.phase_submission_limit_per_day),
      scoring_version: form.phase_scoring_version.trim(),
      rules_version: form.phase_rules_version.trim(),
    },
  };
}

function formatForDateTimeInput(value: string) {
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const adjusted = new Date(date.getTime() - offset * 60 * 1000);
  return adjusted.toISOString().slice(0, 16);
}

function toIsoString(value: string) {
  return new Date(value).toISOString();
}
