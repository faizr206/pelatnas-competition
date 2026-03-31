"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AdminAccessState, AdminPageShell } from "@/components/admin-page-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getCompetitions, getOptionalSession } from "@/lib/api";
import type { Competition, User } from "@/lib/competition-types";

export function AdminPanelPage() {
  const [user, setUser] = useState<User | null>(null);
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadAdminData() {
      setLoading(true);
      setError(null);

      try {
        const [currentUser, competitionList] = await Promise.all([
          getOptionalSession(),
          getCompetitions(),
        ]);

        if (!active) {
          return;
        }

        setUser(currentUser);
        setCompetitions(competitionList);
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
        <div className="mt-8 space-y-8">
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
        </div>
      )}
    </AdminPageShell>
  );
}
