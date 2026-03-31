"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import {
  AdminCompetitionForm,
  createEmptyCompetitionForm,
  toCreateCompetitionPayload,
  type CompetitionFormState,
} from "@/components/admin-competition-form";
import { AdminPageShell } from "@/components/admin-page-shell";
import { Button } from "@/components/ui/button";
import { createCompetition, getOptionalSession } from "@/lib/api";
import type { User } from "@/lib/competition-types";

export function AdminCreateCompetitionPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [form, setForm] = useState<CompetitionFormState>(createEmptyCompetitionForm());
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadUser() {
      try {
        const currentUser = await getOptionalSession();
        if (active) {
          setUser(currentUser);
        }
      } finally {
        if (active) {
          setLoadingUser(false);
        }
      }
    }

    void loadUser();

    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);

    try {
      const createdCompetition = await createCompetition(toCreateCompetitionPayload(form));
      router.push(`/admin/competitions/${createdCompetition.slug}`);
      router.refresh();
    } catch (submitError) {
      setMessage(
        submitError instanceof Error ? submitError.message : "Failed to create competition.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <AdminPageShell
      user={user}
      title="Create Competition"
      description="Define a new competition as a standalone workflow, then continue directly into the dedicated edit screen."
      loginHref="/login?next=/admin/new"
    >
      {loadingUser ? (
        <div className="mt-8 animate-pulse rounded-2xl border border-[#ececec] bg-white px-6 py-6">
          <div className="h-5 w-52 rounded bg-[#efefef]" />
          <div className="mt-4 h-4 w-full rounded bg-[#f4f4f4]" />
          <div className="mt-3 h-4 w-3/4 rounded bg-[#f4f4f4]" />
        </div>
      ) : !user ? (
        <div className="mt-8 rounded-2xl border border-[#ececec] bg-[#fafafa] px-5 py-5">
          <p className="text-sm text-[#555555]">
            Sign in with an admin account to create competitions.
          </p>
          <Button
            asChild
            className="mt-4 h-9 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
          >
            <Link href="/login?next=/admin/new">Login</Link>
          </Button>
        </div>
      ) : !user.is_admin ? (
        <div className="mt-8 rounded-2xl border border-[#ececec] bg-[#fafafa] px-5 py-5">
          <p className="text-sm text-[#555555]">
            Your account is signed in but does not have admin access.
          </p>
        </div>
      ) : (
        <div className="mt-8 rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold tracking-[-0.03em] text-black">
              New Competition
            </h2>
            <p className="mt-2 text-sm text-[#6f6f6f]">
              Set the competition metadata, submission policy, retention windows,
              and the current active phase.
            </p>
          </div>
          <Button
            asChild
            variant="outline"
            className="h-9 rounded-full border-[#e4e4e4] bg-white px-4 text-xs font-semibold text-[#1f1f1f] hover:bg-[#f6f6f6]"
          >
            <Link href="/admin">Back to admin</Link>
          </Button>
        </div>

        <AdminCompetitionForm
          form={form}
          mode="create"
          message={message}
          submitLabel={busy ? "Creating..." : "Create competition"}
          onChange={(field, value) => setForm((current) => ({ ...current, [field]: value }))}
          onSubmit={handleSubmit}
        />
        </div>
      )}
    </AdminPageShell>
  );
}
