"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { SessionActions } from "@/components/session-actions";
import { SiteHeader } from "@/components/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getCompetitions, getOptionalSession } from "@/lib/api";
import type { Competition, User } from "@/lib/competition-types";

type CompetitionsDirectoryProps = {
  activeNav: "home" | "competitions";
};

export function CompetitionsDirectory({
  activeNav,
}: CompetitionsDirectoryProps) {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadDirectory() {
      setLoading(true);
      setError(null);

      try {
        const [competitionList, currentUser] = await Promise.all([
          getCompetitions(),
          getOptionalSession(),
        ]);

        if (!active) {
          return;
        }

        setCompetitions(competitionList);
        setUser(currentUser);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setError(
          loadError instanceof Error
            ? loadError.message
            : "Failed to load competitions.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadDirectory();

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-white text-slate-950">
      <SiteHeader
        activeNav={activeNav}
        action={
          user ? (
            <SessionActions user={user} />
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
        <section className="mx-auto max-w-[1824px]">
          <div className="max-w-3xl">
            <h1 className="text-[1.9rem] font-semibold tracking-[-0.03em] text-black">
              Active Competitions
            </h1>
            <p className="mt-2 text-sm leading-6 text-[#6f6f6f]">
              Start simple on the index, then move into the fuller Kaggle-style
              workspace once you open a competition.
            </p>
          </div>

          {error ? (
            <div className="mt-7 rounded-2xl border border-[#f0d4d4] bg-[#fff8f8] px-4 py-3 text-sm text-[#a04141]">
              {error}
            </div>
          ) : null}

          <div className="mt-7 space-y-3">
            {loading ? (
              Array.from({ length: 3 }).map((_, index) => (
                <div
                  key={index}
                  className="animate-pulse rounded-xl border border-[#ececec] bg-white px-4 py-4"
                >
                  <div className="h-4 w-44 rounded bg-[#efefef]" />
                  <div className="mt-3 h-3 w-72 max-w-full rounded bg-[#f4f4f4]" />
                </div>
              ))
            ) : competitions.length === 0 ? (
              <div className="rounded-xl border border-dashed border-[#e4e4e4] px-4 py-5 text-sm text-[#6b6b6b]">
                No competitions are available yet.
              </div>
            ) : (
              competitions.map((competition) => {
                const activePhase = competition.phases[0] ?? null;

                return (
                  <article
                    key={competition.id}
                    className="rounded-xl border border-[#ececec] bg-white px-4 py-4 transition-colors hover:bg-[#fafafa]"
                  >
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="text-sm font-semibold text-[#111111] md:text-[15px]">
                            {competition.title}
                          </h2>
                          <Badge
                            variant="secondary"
                            className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#6a6a6a]"
                          >
                            {competition.status}
                          </Badge>
                        </div>
                        <p className="mt-1 text-sm text-[#6f6f6f]">
                          {competition.description}
                        </p>
                        <div className="mt-3 flex flex-wrap gap-4 text-xs text-[#8a8a8a]">
                          <span>Metric: {competition.scoring_metric}</span>
                          <span>
                            Limit: {competition.max_submissions_per_day} submissions/day
                          </span>
                          <span>
                            Phase:{" "}
                            {activePhase
                              ? `${formatDate(activePhase.starts_at)} - ${formatDate(activePhase.ends_at)}`
                              : "Not scheduled"}
                          </span>
                        </div>
                      </div>

                      <Button
                        asChild
                        variant="outline"
                        className="h-9 rounded-full border-[#e4e4e4] bg-white px-4 text-xs font-semibold text-[#1f1f1f] hover:bg-[#f6f6f6]"
                      >
                        <Link href={`/competitions/${competition.slug}`}>
                          View Competition
                        </Link>
                      </Button>
                    </div>
                  </article>
                );
              })
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}
