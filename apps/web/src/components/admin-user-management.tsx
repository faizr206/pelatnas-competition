"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createAdminUser,
  getAdminUsers,
  importAdminUsers,
  resetAdminUserPassword,
  updateAdminUser,
} from "@/lib/api";
import type { AdminManagedUser, User } from "@/lib/competition-types";

type AdminUserManagementProps = {
  currentUser: User;
};

type UserDraft = {
  display_name: string;
  status: string;
  is_admin: boolean;
  reset_password: string;
};

const defaultCreateForm = {
  email: "",
  display_name: "",
  default_password: "",
  is_admin: false,
  status: "active",
};

export function AdminUserManagement({ currentUser }: AdminUserManagementProps) {
  const [users, setUsers] = useState<AdminManagedUser[]>([]);
  const [drafts, setDrafts] = useState<Record<string, UserDraft>>({});
  const [createForm, setCreateForm] = useState(defaultCreateForm);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState<string | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [resettingUserId, setResettingUserId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadUsers() {
      setLoading(true);
      setError(null);

      try {
        const nextUsers = await getAdminUsers();
        if (!active) {
          return;
        }

        setUsers(nextUsers);
        setDrafts(buildDrafts(nextUsers));
      } catch (loadError) {
        if (!active) {
          return;
        }

        setError(
          loadError instanceof Error ? loadError.message : "Failed to load users.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadUsers();

    return () => {
      active = false;
    };
  }, []);

  function updateDraft(userId: string, patch: Partial<UserDraft>) {
    setDrafts((current) => ({
      ...current,
      [userId]: {
        ...current[userId],
        ...patch,
      },
    }));
  }

  async function handleCreateUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreateError(null);
    setCreateSuccess(null);

    try {
      const createdUser = await createAdminUser(createForm);
      const nextUsers = [createdUser, ...users];
      setUsers(nextUsers);
      setDrafts(buildDrafts(nextUsers));
      setCreateForm(defaultCreateForm);
      setCreateSuccess(
        `${createdUser.display_name} was created with a temporary password and must rotate it on first login.`,
      );
    } catch (createUserError) {
      setCreateError(
        createUserError instanceof Error
          ? createUserError.message
          : "Failed to create the user.",
      );
    }
  }

  async function handleImportUsers(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setImportError(null);
    setImportSuccess(null);

    if (!importFile) {
      setImportError("Choose a CSV file before importing users.");
      return;
    }

    setImporting(true);
    try {
      const result = await importAdminUsers(importFile);
      const nextUsers = [...result.users, ...users];
      setUsers(nextUsers);
      setDrafts(buildDrafts(nextUsers));
      setImportFile(null);
      setImportSuccess(
        `Imported ${result.created_count} users. All imported accounts are active, non-admin, and must change password on first login.`,
      );
    } catch (importUsersError) {
      setImportError(
        importUsersError instanceof Error
          ? importUsersError.message
          : "Failed to import users.",
      );
    } finally {
      setImporting(false);
    }
  }

  async function handleSaveUser(userId: string) {
    const draft = drafts[userId];
    if (!draft) {
      return;
    }

    setSavingUserId(userId);
    setError(null);

    try {
      const updatedUser = await updateAdminUser(userId, {
        display_name: draft.display_name,
        status: draft.status,
        is_admin: draft.is_admin,
      });
      setUsers((current) =>
        current.map((user) => (user.id === userId ? updatedUser : user)),
      );
      setDrafts((current) => ({
        ...current,
        [userId]: {
          ...current[userId],
          display_name: updatedUser.display_name,
          status: updatedUser.status,
          is_admin: updatedUser.is_admin,
        },
      }));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to update the user.");
    } finally {
      setSavingUserId(null);
    }
  }

  async function handleResetPassword(userId: string) {
    const draft = drafts[userId];
    if (!draft?.reset_password) {
      setError("Enter a temporary password before resetting a user password.");
      return;
    }

    setResettingUserId(userId);
    setError(null);

    try {
      const updatedUser = await resetAdminUserPassword(userId, draft.reset_password);
      setUsers((current) =>
        current.map((user) => (user.id === userId ? updatedUser : user)),
      );
      setDrafts((current) => ({
        ...current,
        [userId]: {
          ...current[userId],
          reset_password: "",
        },
      }));
    } catch (resetError) {
      setError(
        resetError instanceof Error ? resetError.message : "Failed to reset the password.",
      );
    } finally {
      setResettingUserId(null);
    }
  }

  return (
    <section className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-[-0.03em] text-black">
            User Management
          </h2>
          <p className="mt-2 text-sm text-[#6f6f6f]">
            Create accounts, control admin access, suspend users, and issue temporary passwords.
          </p>
        </div>
        <Badge
          variant="secondary"
          className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
        >
          {users.length} users
        </Badge>
      </div>

      <section className="rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
        <div className="max-w-3xl">
          <h3 className="text-lg font-semibold tracking-[-0.03em] text-black">Create User</h3>
          <p className="mt-2 text-sm text-[#6f6f6f]">
            New accounts are created with a temporary password and are required to change it after signing in.
          </p>
        </div>

        <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={handleCreateUser}>
          <div className="space-y-2">
            <Label htmlFor="new-user-name">Display name</Label>
            <Input
              id="new-user-name"
              value={createForm.display_name}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, display_name: event.target.value }))
              }
              placeholder="Participant One"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="new-user-email">Email</Label>
            <Input
              id="new-user-email"
              type="email"
              value={createForm.email}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, email: event.target.value }))
              }
              placeholder="participant@example.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="new-user-password">Temporary password</Label>
            <Input
              id="new-user-password"
              type="password"
              value={createForm.default_password}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  default_password: event.target.value,
                }))
              }
              placeholder="At least 8 characters"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="new-user-status">Status</Label>
            <select
              id="new-user-status"
              className="flex h-11 w-full rounded-2xl border border-input bg-background/80 px-4 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={createForm.status}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, status: event.target.value }))
              }
            >
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
            </select>
          </div>
          <label className="flex items-center gap-3 rounded-2xl border border-[#ececec] px-4 py-3 text-sm text-[#303030]">
            <input
              checked={createForm.is_admin}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, is_admin: event.target.checked }))
              }
              type="checkbox"
            />
            Grant admin access
          </label>
          <div className="flex items-end">
            <Button className="h-11 rounded-full bg-[#1f1f1f] px-5 text-xs font-semibold hover:bg-[#111111]">
              Create user
            </Button>
          </div>
        </form>

        {createError ? (
          <p className="mt-4 text-sm text-[#b14d4d]">{createError}</p>
        ) : null}
        {createSuccess ? (
          <p className="mt-4 text-sm text-[#2d6a4f]">{createSuccess}</p>
        ) : null}
      </section>

      <section className="rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
        <div className="max-w-3xl">
          <h3 className="text-lg font-semibold tracking-[-0.03em] text-black">Bulk Import Users</h3>
          <p className="mt-2 text-sm text-[#6f6f6f]">
            Upload a `.csv` with exactly `display_name,email,default_password`. Imported users are created as active non-admin accounts and must change password on first login.
          </p>
        </div>

        <form className="mt-6 flex flex-col gap-4 md:flex-row md:items-end" onSubmit={handleImportUsers}>
          <div className="flex-1 space-y-2">
            <Label htmlFor="bulk-user-import">User CSV</Label>
            <Input
              id="bulk-user-import"
              type="file"
              accept=".csv"
              onChange={(event) => setImportFile(event.target.files?.[0] ?? null)}
            />
          </div>
          <div className="flex items-end">
            <Button
              className="h-11 rounded-full bg-[#1f1f1f] px-5 text-xs font-semibold hover:bg-[#111111]"
              disabled={importing}
            >
              {importing ? "Importing..." : "Import users"}
            </Button>
          </div>
        </form>

        {importError ? (
          <p className="mt-4 text-sm text-[#b14d4d]">{importError}</p>
        ) : null}
        {importSuccess ? (
          <p className="mt-4 text-sm text-[#2d6a4f]">{importSuccess}</p>
        ) : null}
      </section>

      <section className="rounded-[28px] border border-[#ececec] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
        {loading ? (
          <div className="animate-pulse space-y-3">
            <div className="h-5 w-40 rounded bg-[#efefef]" />
            <div className="h-12 rounded bg-[#f6f6f6]" />
            <div className="h-12 rounded bg-[#f6f6f6]" />
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-[#f0d4d4] bg-[#fff8f8] px-5 py-4 text-sm text-[#a04141]">
            {error}
          </div>
        ) : users.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#e4e4e4] px-5 py-5 text-sm text-[#6b6b6b]">
            No users are available yet.
          </div>
        ) : (
          <div className="space-y-4">
            {users.map((user) => {
              const draft = drafts[user.id];
              const isSelf = user.id === currentUser.id;

              return (
                <article
                  key={user.id}
                  className="rounded-2xl border border-[#ececec] bg-[#fcfcfc] p-4"
                >
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-semibold text-black">{user.display_name}</h3>
                        <Badge
                          variant="secondary"
                          className="border-0 bg-[#f2f2f2] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#666666]"
                        >
                          {user.is_admin ? "Admin" : "Participant"}
                        </Badge>
                        <Badge
                          variant={user.status === "active" ? "outline" : "destructive"}
                          className="px-2.5 py-1 text-[10px] uppercase tracking-[0.14em]"
                        >
                          {user.status}
                        </Badge>
                        {user.must_change_password ? (
                          <Badge
                            className="border-0 bg-[#fff4d6] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[#8c5a00]"
                          >
                            Password rotation required
                          </Badge>
                        ) : null}
                      </div>
                      <p className="mt-2 break-all text-sm text-[#6f6f6f]">{user.email}</p>
                    </div>

                    <div className="grid gap-3 md:grid-cols-2 xl:w-[760px]">
                      <Input
                        value={draft?.display_name ?? ""}
                        onChange={(event) =>
                          updateDraft(user.id, { display_name: event.target.value })
                        }
                        placeholder="Display name"
                      />
                      <select
                        className="flex h-11 w-full rounded-2xl border border-input bg-background/80 px-4 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                        value={draft?.status ?? "active"}
                        onChange={(event) =>
                          updateDraft(user.id, { status: event.target.value })
                        }
                      >
                        <option value="active">Active</option>
                        <option value="suspended">Suspended</option>
                      </select>
                      <label className="flex items-center gap-3 rounded-2xl border border-[#ececec] px-4 py-3 text-sm text-[#303030]">
                        <input
                          checked={draft?.is_admin ?? false}
                          disabled={isSelf}
                          onChange={(event) =>
                            updateDraft(user.id, { is_admin: event.target.checked })
                          }
                          type="checkbox"
                        />
                        Admin access {isSelf ? "(locked for your own account)" : ""}
                      </label>
                      <div className="flex gap-2">
                        <Button
                          className="h-11 rounded-full bg-[#1f1f1f] px-4 text-xs font-semibold hover:bg-[#111111]"
                          disabled={savingUserId === user.id}
                          onClick={() => void handleSaveUser(user.id)}
                          type="button"
                        >
                          {savingUserId === user.id ? "Saving..." : "Save changes"}
                        </Button>
                      </div>
                      <Input
                        type="password"
                        value={draft?.reset_password ?? ""}
                        onChange={(event) =>
                          updateDraft(user.id, { reset_password: event.target.value })
                        }
                        placeholder={
                          isSelf
                            ? "Use profile page for your own password"
                            : "New temporary password"
                        }
                        disabled={isSelf}
                      />
                      <Button
                        variant="outline"
                        className="h-11 rounded-full border-[#e4e4e4] bg-white px-4 text-xs font-semibold text-[#1f1f1f] hover:bg-[#f6f6f6]"
                        disabled={isSelf || resettingUserId === user.id}
                        onClick={() => void handleResetPassword(user.id)}
                        type="button"
                      >
                        {resettingUserId === user.id ? "Resetting..." : "Reset password"}
                      </Button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </section>
  );
}

function buildDrafts(users: AdminManagedUser[]) {
  return Object.fromEntries(
    users.map((user) => [
      user.id,
      {
        display_name: user.display_name,
        status: user.status,
        is_admin: user.is_admin,
        reset_password: "",
      },
    ]),
  );
}
