"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AdminAccessState, AdminPageShell } from "@/components/admin-page-shell";
import { AdminUserManagement } from "@/components/admin-user-management";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  getAdminTasks,
  getAdminWorkers,
  getCompetitions,
  getOptionalSession,
  updateAdminWorker,
} from "@/lib/api";
import type { AdminTask, AdminWorker, Competition, User } from "@/lib/competition-types";

type AdminTab = "competitions" | "workers" | "tasks" | "users";

export function AdminPanelPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>("competitions");
  const [user, setUser] = useState<User | null>(null);
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [workers, setWorkers] = useState<AdminWorker[]>([]);
  const [tasks, setTasks] = useState<AdminTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingWorkerIds, setSavingWorkerIds] = useState<string[]>([]);

  useEffect(() => {
    let active = true;

    async function loadAdminData() {
      setLoading(true);
      setError(null);

      try {
        const [currentUser, competitionList, workerList, taskList] = await Promise.all([
          getOptionalSession(),
          getCompetitions(),
          getAdminWorkers(),
          getAdminTasks(),
        ]);

        if (!active) {
          return;
        }

        setUser(currentUser);
        setCompetitions(competitionList);
        setWorkers(workerList);
        setTasks(taskList);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setError(
          loadError instanceof Error ? loadError.message : "Failed to load the admin panel.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadAdminData();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!user?.is_admin) {
      return;
    }

    let active = true;
    const interval = window.setInterval(async () => {
      try {
        const workerList = await getAdminWorkers();
        if (active) {
          setWorkers(workerList);
        }
      } catch {
        // Keep current data if background refresh fails.
      }
    }, 5000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [user?.is_admin]);

  async function handleWorkerToggle(workerId: string, nextEnabled: boolean) {
    setSavingWorkerIds((current) => [...current, workerId]);
    setError(null);

    try {
      const updated = await updateAdminWorker(workerId, { is_enabled: nextEnabled });
      setWorkers((current) =>
        current.map((worker) => (worker.worker_id === workerId ? updated : worker)),
      );
    } catch (toggleError) {
      setError(
        toggleError instanceof Error ? toggleError.message : "Failed to update the worker.",
      );
    } finally {
      setSavingWorkerIds((current) => current.filter((id) => id !== workerId));
    }
  }

  return (
    <AdminPageShell
      user={user}
      title="Admin Panel"
      description="Manage competitions from a single hub. Create a new competition, or open an existing one to edit its metadata, limits, and phase configuration."
    >
      {loading ? (
        <AdminAccessState kind="loading" />
      ) : error ? (
        <div className="mt-8 rounded-2xl border border-[#f0d4d4] bg-[#fff8f8] px-5 py-4 text-sm text-[#a04141]">
          {error}
        </div>
      ) : !user ? (
        <AdminAccessState kind="logged_out" />
      ) : !user.is_admin ? (
        <AdminAccessState kind="forbidden" />
      ) : (
        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value as AdminTab)}
          className="mt-8"
        >
          <TabsList className="h-auto flex-wrap justify-start gap-2 rounded-[24px] bg-[#f3f3f3] p-2">
            <TabsTrigger
              value="competitions"
              className="px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.14em] data-[state=active]:bg-white"
            >
              Competitions
            </TabsTrigger>
            <TabsTrigger
              value="workers"
              className="px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.14em] data-[state=active]:bg-white"
            >
              Workers
            </TabsTrigger>
            <TabsTrigger
              value="tasks"
              className="px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.14em] data-[state=active]:bg-white"
            >
              Tasks
            </TabsTrigger>
            <TabsTrigger
              value="users"
              className="px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.14em] data-[state=active]:bg-white"
            >
              Users
            </TabsTrigger>
          </TabsList>

          <TabsContent value="competitions" className="space-y-8">
            <section className="rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-lg font-semibold tracking-[-0.03em] text-black">
                    Create A New Competition
                  </h2>
                  <p className="mt-2 text-sm text-[#6f6f6f]">
                    Start a new competition with its own slug, dates, submission rules,
                    and execution limits.
                  </p>
                </div>
                <Button
                  asChild
                  className="h-10 rounded-full bg-[#1f1f1f] px-5 text-xs font-semibold hover:bg-[#111111]"
                >
                  <Link href="/admin/new">Create competition</Link>
                </Button>
              </div>
            </section>

            <section className="space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold tracking-[-0.03em] text-black">
                  Active Competitions
                </h2>
                <Badge
                  variant="secondary"
                  className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                >
                  {competitions.length} competitions
                </Badge>
              </div>

              {competitions.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-[#e4e4e4] px-5 py-5 text-sm text-[#6b6b6b]">
                  No competitions are available yet.
                </div>
              ) : (
                competitions.map((competition) => (
                  <article
                    key={competition.id}
                    className="rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
                  >
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-lg font-semibold tracking-[-0.03em] text-black">
                            {competition.title}
                          </h3>
                          <Badge
                            variant="secondary"
                            className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                          >
                            {competition.status}
                          </Badge>
                        </div>
                        <p className="mt-2 text-sm text-[#6f6f6f]">
                          {competition.description}
                        </p>
                        <p className="mt-2 text-xs text-[#8a8a8a]">
                          Slug: {competition.slug}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-3">
                        <Button
                          asChild
                          variant="outline"
                          className="h-9 rounded-full border-[#e4e4e4] bg-white px-4 text-xs font-semibold text-[#1f1f1f] hover:bg-[#f6f6f6]"
                        >
                          <Link href={`/competitions/${competition.slug}`}>Open competition</Link>
                        </Button>
                        <Button
                          asChild
                          className="h-9 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
                        >
                          <Link href={`/admin/competitions/${competition.slug}`}>Edit competition</Link>
                        </Button>
                      </div>
                    </div>
                  </article>
                ))
              )}
            </section>
          </TabsContent>

          <TabsContent value="workers" className="space-y-6">
            <section className="grid gap-4 md:grid-cols-3">
              <MonitoringStatCard label="Known workers" value={String(workers.length)} />
              <MonitoringStatCard
                label="Online now"
                value={String(workers.filter((worker) => worker.is_online).length)}
              />
              <MonitoringStatCard
                label="Enabled"
                value={String(workers.filter((worker) => worker.is_enabled).length)}
              />
            </section>

            <section className="rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold tracking-[-0.03em] text-black">
                    Worker Fleet
                  </h2>
                  <p className="mt-2 text-sm text-[#6f6f6f]">
                    Workers report live heartbeats. Use the checkbox to disable a worker from
                    taking new jobs.
                  </p>
                </div>
                <Badge
                  variant="secondary"
                  className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                >
                  {workers.length} workers
                </Badge>
              </div>

              {workers.length === 0 ? (
                <div className="mt-6 rounded-2xl border border-dashed border-[#e4e4e4] px-5 py-5 text-sm text-[#6b6b6b]">
                  No workers have claimed jobs yet.
                </div>
              ) : (
                <div className="mt-6 grid gap-4 xl:grid-cols-2">
                  {workers.map((worker) => (
                    <article
                      key={worker.worker_id}
                      className="rounded-3xl border border-[#ececec] bg-[#fafafa] p-5"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h3 className="text-base font-semibold tracking-[-0.03em] text-black">
                            {worker.worker_id}
                          </h3>
                          <p className="mt-1 text-sm text-[#6f6f6f]">
                            Last heartbeat {formatDateTime(worker.last_heartbeat_at)}
                          </p>
                        </div>
                        <div className="flex items-start gap-3">
                          <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-[#666666]">
                            <input
                              type="checkbox"
                              checked={worker.is_enabled}
                              disabled={savingWorkerIds.includes(worker.worker_id)}
                              onChange={(event) =>
                                void handleWorkerToggle(worker.worker_id, event.target.checked)
                              }
                              className="h-4 w-4 rounded border border-[#cfcfcf]"
                            />
                            Enabled
                          </label>
                          <StatusBadge status={worker.availability_status} />
                        </div>
                      </div>
                      <div className="mt-5 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
                        <WorkerMetric label="Active" value={String(worker.active_jobs)} />
                        <WorkerMetric label="Done" value={String(worker.completed_jobs)} />
                        <WorkerMetric label="Failed" value={String(worker.failed_jobs)} />
                        <WorkerMetric label="Total" value={String(worker.total_jobs)} />
                      </div>
                      <p className="mt-4 text-xs uppercase tracking-[0.14em] text-[#8a8a8a]">
                        Latest job status: {worker.latest_job_status ?? "unknown"}
                      </p>
                      <p className="mt-2 text-xs uppercase tracking-[0.14em] text-[#8a8a8a]">
                        Online: {worker.is_online ? "yes" : "no"}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </TabsContent>

          <TabsContent value="tasks" className="space-y-6">
            <section className="grid gap-4 md:grid-cols-4">
              <MonitoringStatCard label="All submissions" value={String(tasks.length)} />
              <MonitoringStatCard
                label="Succeeded"
                value={String(tasks.filter((task) => task.latest_job?.status === "completed").length)}
              />
              <MonitoringStatCard
                label="Failed"
                value={String(tasks.filter((task) => task.latest_job?.status === "failed").length)}
              />
              <MonitoringStatCard
                label="In progress"
                value={String(
                  tasks.filter((task) =>
                    ["pending", "queued", "running", "collecting", "scoring"].includes(
                      task.latest_job?.status ?? task.submission_status,
                    ),
                  ).length,
                )}
              />
            </section>

            <section className="rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold tracking-[-0.03em] text-black">
                    Submission Tasks
                  </h2>
                  <p className="mt-2 text-sm text-[#6f6f6f]">
                    Global submission queue visibility across competitions, including owner,
                    current job status, worker assignment, and failure details.
                  </p>
                </div>
                <Badge
                  variant="secondary"
                  className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                >
                  {tasks.length} tasks
                </Badge>
              </div>

              {tasks.length === 0 ? (
                <div className="mt-6 rounded-2xl border border-dashed border-[#e4e4e4] px-5 py-5 text-sm text-[#6b6b6b]">
                  No submissions have been created yet.
                </div>
              ) : (
                <div className="mt-6">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Competition</TableHead>
                        <TableHead>Participant</TableHead>
                        <TableHead>File</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Worker</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Created</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tasks.map((task) => (
                        <TableRow key={task.submission_id}>
                          <TableCell className="min-w-[220px]">
                            <div className="font-medium text-black">{task.competition_title}</div>
                            <div className="mt-1 text-xs text-[#777777]">
                              <Link
                                href={`/competitions/${task.competition_slug}`}
                                className="underline decoration-[#cccccc] underline-offset-4"
                              >
                                {task.competition_slug}
                              </Link>
                            </div>
                          </TableCell>
                          <TableCell className="min-w-[220px]">
                            <div className="font-medium text-black">{task.participant_name}</div>
                            <div className="mt-1 text-xs text-[#777777]">
                              {task.participant_email}
                            </div>
                          </TableCell>
                          <TableCell className="min-w-[220px]">
                            <div className="font-medium text-black">
                              {task.source_original_filename}
                            </div>
                            <div className="mt-1 text-xs uppercase tracking-[0.14em] text-[#8a8a8a]">
                              {task.submission_type}
                            </div>
                          </TableCell>
                          <TableCell className="min-w-[180px]">
                            <StatusBadge status={task.latest_job?.status ?? task.submission_status} />
                            {task.latest_job?.failure_reason ? (
                              <p className="mt-2 max-w-[280px] text-xs leading-5 text-[#9b4a4a]">
                                {task.latest_job.failure_reason}
                              </p>
                            ) : null}
                          </TableCell>
                          <TableCell>{task.latest_job?.worker_id ?? "pending"}</TableCell>
                          <TableCell>
                            {task.latest_score ? task.latest_score.score_value.toFixed(4) : "-"}
                          </TableCell>
                          <TableCell>{formatDateTime(task.created_at)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </section>
          </TabsContent>

          <TabsContent value="users">
            <AdminUserManagement currentUser={user} />
          </TabsContent>
        </Tabs>
      )}
    </AdminPageShell>
  );
}

function MonitoringStatCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-[24px] border border-[#ececec] bg-white px-5 py-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#8a8a8a]">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-black">{value}</p>
    </article>
  );
}

function WorkerMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#e8e8e8] bg-white px-4 py-3">
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#8a8a8a]">
        {label}
      </div>
      <div className="mt-2 text-xl font-semibold tracking-[-0.04em] text-black">{value}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const className =
    normalized === "completed" || normalized === "idle"
      ? "bg-[#eef8ef] text-[#25623a]"
      : normalized === "failed"
        ? "bg-[#fff1f1] text-[#a04141]"
        : normalized === "busy" || normalized === "running" || normalized === "scoring"
          ? "bg-[#eef4ff] text-[#315ba8]"
          : normalized === "disabled"
            ? "bg-[#f7f0e8] text-[#94602a]"
          : "bg-[#f2f2f2] text-[#5f5f5f]";

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] ${className}`}
    >
      {normalized}
    </span>
  );
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleString();
}
