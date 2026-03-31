"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { SessionActions } from "@/components/session-actions";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import type { User } from "@/lib/competition-types";

type AdminPageShellProps = {
  user: User | null;
  title: string;
  description: string;
  children: ReactNode;
  loginHref?: string;
};

export function AdminPageShell({
  user,
  title,
  description,
  children,
  loginHref = "/login?next=/admin",
}: AdminPageShellProps) {
  return (
    <div className="min-h-screen bg-white text-slate-950">
      <SiteHeader
        activeNav="competitions"
        action={
          user ? (
            <SessionActions user={user} />
          ) : (
            <Button
              asChild
              className="h-9 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
            >
              <Link href={loginHref}>Login</Link>
            </Button>
          )
        }
      />
      <main className="px-6 pb-16 pt-8 md:px-12 md:pt-10">
        <section className="mx-auto max-w-[1400px]">
          <div className="max-w-3xl">
            <h1 className="text-[1.9rem] font-semibold tracking-[-0.03em] text-black">
              {title}
            </h1>
            <p className="mt-2 text-sm leading-6 text-[#6f6f6f]">{description}</p>
          </div>
          {children}
        </section>
      </main>
    </div>
  );
}

export function AdminAccessState({
  kind,
}: {
  kind: "loading" | "error" | "logged_out" | "forbidden";
}) {
  if (kind === "loading") {
    return (
      <div className="mt-8 animate-pulse rounded-2xl border border-[#ececec] bg-white px-6 py-6">
        <div className="h-5 w-52 rounded bg-[#efefef]" />
        <div className="mt-4 h-4 w-full rounded bg-[#f4f4f4]" />
        <div className="mt-3 h-4 w-3/4 rounded bg-[#f4f4f4]" />
      </div>
    );
  }

  if (kind === "logged_out") {
    return (
      <div className="mt-8 rounded-2xl border border-[#ececec] bg-[#fafafa] px-5 py-5">
        <p className="text-sm text-[#555555]">
          Sign in with an admin account to manage competitions.
        </p>
        <Button
          asChild
          className="mt-4 h-9 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
        >
          <Link href="/login?next=/admin">Login</Link>
        </Button>
      </div>
    );
  }

  if (kind === "forbidden") {
    return (
      <div className="mt-8 rounded-2xl border border-[#ececec] bg-[#fafafa] px-5 py-5">
        <p className="text-sm text-[#555555]">
          Your account is signed in but does not have admin access.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-8 rounded-2xl border border-[#f0d4d4] bg-[#fff8f8] px-5 py-4 text-sm text-[#a04141]">
      Failed to load the admin panel.
    </div>
  );
}
