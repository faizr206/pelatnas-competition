"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState, useTransition } from "react";

import { SessionActions } from "@/components/session-actions";
import { SiteHeader } from "@/components/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { changePassword, getOptionalSession } from "@/lib/api";
import type { User } from "@/lib/competition-types";

export function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let active = true;

    async function loadProfile() {
      setLoading(true);
      setError(null);

      try {
        const currentUser = await getOptionalSession();
        if (!active) {
          return;
        }

        setUser(currentUser);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setError(
          loadError instanceof Error
            ? loadError.message
            : "Failed to load your profile.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      active = false;
    };
  }, []);

  function handlePasswordChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError(null);
    setPasswordMessage(null);

    startTransition(() => {
      void (async () => {
        try {
          const updatedUser = await changePassword(currentPassword, newPassword);
          setUser(updatedUser);
          setCurrentPassword("");
          setNewPassword("");
          setPasswordMessage("Password updated successfully.");
        } catch (changePasswordError) {
          setPasswordError(
            changePasswordError instanceof Error
              ? changePasswordError.message
              : "Failed to update the password.",
          );
        }
      })();
    });
  }

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
              <Link href="/login?next=/profile">Login</Link>
            </Button>
          )
        }
      />
      <main className="px-6 pb-16 pt-8 md:px-12 md:pt-10">
        <section className="mx-auto max-w-[960px]">
          <div className="max-w-2xl">
            <h1 className="text-[1.9rem] font-semibold tracking-[-0.03em] text-black">
              Profile
            </h1>
            <p className="mt-2 text-sm leading-6 text-[#6f6f6f]">
              Session identity, access level, and the quickest route back into
              competitions.
            </p>
          </div>

          {loading ? (
            <div className="mt-8 animate-pulse rounded-2xl border border-[#ececec] bg-white px-6 py-6">
              <div className="h-5 w-40 rounded bg-[#efefef]" />
              <div className="mt-4 h-4 w-56 rounded bg-[#f4f4f4]" />
              <div className="mt-3 h-4 w-72 rounded bg-[#f4f4f4]" />
            </div>
          ) : error ? (
            <div className="mt-8 rounded-2xl border border-[#f0d4d4] bg-[#fff8f8] px-5 py-4 text-sm text-[#a04141]">
              {error}
            </div>
          ) : !user ? (
            <div className="mt-8 rounded-2xl border border-[#ececec] bg-[#fafafa] px-5 py-5">
              <p className="text-sm text-[#555555]">
                Sign in to view your profile and account access.
              </p>
              <Button
                asChild
                className="mt-4 h-9 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
              >
                <Link href="/login?next=/profile">Login</Link>
              </Button>
            </div>
          ) : (
            <div className="mt-8 rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-xl font-semibold tracking-[-0.03em] text-black">
                  {user.display_name}
                </h2>
                <Badge
                  variant="secondary"
                  className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                >
                  {user.is_admin ? "Admin" : "Participant"}
                </Badge>
                <Badge
                  variant="outline"
                  className="border-[#e7e7e7] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                >
                  {user.status}
                </Badge>
                {user.must_change_password ? (
                  <Badge className="border-0 bg-[#fff4d6] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#8c5a00]">
                    Password change required
                  </Badge>
                ) : null}
              </div>

              {user.must_change_password ? (
                <div className="mt-6 rounded-2xl border border-[#f2dfaf] bg-[#fff9ea] px-5 py-4 text-sm text-[#7a5b10]">
                  This account is still using a temporary password. Change it before continuing.
                </div>
              ) : null}

              <dl className="mt-8 grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl border border-[#efefef] bg-[#fafafa] px-4 py-4">
                  <dt className="text-[11px] uppercase tracking-[0.14em] text-[#7a7a7a]">
                    Email
                  </dt>
                  <dd className="mt-2 text-sm font-medium text-[#202020]">
                    {user.email}
                  </dd>
                </div>
                <div className="rounded-2xl border border-[#efefef] bg-[#fafafa] px-4 py-4">
                  <dt className="text-[11px] uppercase tracking-[0.14em] text-[#7a7a7a]">
                    User ID
                  </dt>
                  <dd className="mt-2 break-all text-sm font-medium text-[#202020]">
                    {user.id}
                  </dd>
                </div>
              </dl>

              <section className="mt-8 rounded-2xl border border-[#efefef] bg-[#fafafa] p-5">
                <div className="max-w-xl">
                  <h3 className="text-base font-semibold text-black">Change Password</h3>
                  <p className="mt-2 text-sm text-[#6f6f6f]">
                    Use your current password once, then set a new private password for this account.
                  </p>
                </div>

                <form className="mt-5 grid gap-4 md:grid-cols-2" onSubmit={handlePasswordChange}>
                  <div className="space-y-2">
                    <Label htmlFor="current-password">Current password</Label>
                    <Input
                      id="current-password"
                      type="password"
                      value={currentPassword}
                      onChange={(event) => setCurrentPassword(event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="new-password">New password</Label>
                    <Input
                      id="new-password"
                      type="password"
                      value={newPassword}
                      onChange={(event) => setNewPassword(event.target.value)}
                    />
                  </div>
                  <div className="md:col-span-2 flex flex-wrap items-center gap-3">
                    <Button className="h-10 rounded-full bg-[#1f1f1f] px-5 text-xs font-semibold hover:bg-[#111111]">
                      {isPending ? "Updating..." : "Update password"}
                    </Button>
                    {passwordMessage ? (
                      <p className="text-sm text-[#2d6a4f]">{passwordMessage}</p>
                    ) : null}
                    {passwordError ? (
                      <p className="text-sm text-[#b14d4d]">{passwordError}</p>
                    ) : null}
                  </div>
                </form>
              </section>

              <div className="mt-8 flex flex-wrap gap-3">
                <Button
                  asChild
                  variant="outline"
                  className="h-9 rounded-full border-[#e4e4e4] bg-white px-4 text-xs font-semibold text-[#1f1f1f] hover:bg-[#f6f6f6]"
                >
                  <Link href="/competitions">Browse competitions</Link>
                </Button>
                {user.is_admin ? (
                  <Button
                    asChild
                    className="h-9 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
                  >
                    <Link href="/admin">Open admin panel</Link>
                  </Button>
                ) : null}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
