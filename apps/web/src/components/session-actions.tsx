"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState, useTransition } from "react";
import { ChevronDown } from "lucide-react";

import { UserChip } from "@/components/user-chip";
import { Button } from "@/components/ui/button";
import { logout } from "@/lib/api";
import type { User } from "@/lib/competition-types";

type SessionActionsProps = {
  user: User;
};

export function SessionActions({ user }: SessionActionsProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  function handleLogout() {
    setError(null);
    setOpen(false);

    startTransition(() => {
      void (async () => {
        try {
          await logout();
          router.push("/");
          router.refresh();
        } catch (logoutError) {
          setError(
            logoutError instanceof Error
              ? logoutError.message
              : "Logout failed.",
          );
        }
      })();
    });
  }

  return (
    <div
      ref={containerRef}
      className="flex flex-wrap items-center justify-end gap-2"
    >
      {error ? <span className="text-[11px] text-[#a04141]">{error}</span> : null}
      <div className="relative">
        <button
          type="button"
          aria-expanded={open}
          aria-haspopup="menu"
          className="inline-flex h-9 items-center gap-2 rounded-full border border-[#e7e7e7] bg-white px-2 py-1 text-xs font-medium text-[#202020] shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition-colors hover:bg-[#f7f7f7]"
          onClick={() => setOpen((current) => !current)}
        >
          <UserChip user={user} />
          <span className="max-w-[9rem] truncate pr-1">{user.display_name}</span>
          <ChevronDown
            className={`h-3.5 w-3.5 text-[#7a7a7a] transition-transform ${open ? "rotate-180" : ""}`}
          />
        </button>

        {open ? (
          <div
            className="absolute right-0 z-20 mt-2 min-w-[180px] overflow-hidden rounded-2xl border border-[#e7e7e7] bg-white p-1 shadow-[0_12px_30px_rgba(15,23,42,0.12)]"
            role="menu"
          >
            <Link
              href="/profile"
              className="flex items-center rounded-[14px] px-3 py-2 text-sm text-[#202020] transition-colors hover:bg-[#f6f6f6]"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              Profile
            </Link>
            {user.is_admin ? (
              <Link
                href={pathname?.startsWith("/admin") ? "/competitions" : "/admin"}
                className="flex items-center rounded-[14px] px-3 py-2 text-sm text-[#202020] transition-colors hover:bg-[#f6f6f6]"
                role="menuitem"
                onClick={() => setOpen(false)}
              >
                {pathname?.startsWith("/admin") ? "Competitions" : "Admin Panel"}
              </Link>
            ) : null}
            <button
              type="button"
              className="flex w-full items-center rounded-[14px] px-3 py-2 text-left text-sm text-[#202020] transition-colors hover:bg-[#f6f6f6]"
              disabled={isPending}
              role="menuitem"
              onClick={handleLogout}
            >
              {isPending ? "Logging out..." : "Logout"}
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
