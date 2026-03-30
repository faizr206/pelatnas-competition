"use client";

import type { User } from "@/lib/competition-types";

type UserChipProps = {
  user: User;
};

export function UserChip({ user }: UserChipProps) {
  const initials = user.display_name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("") || user.email.slice(0, 2).toUpperCase();

  return (
    <div
      className="flex h-9 min-w-9 items-center justify-center rounded-[10px] border border-[#e7e7e7] bg-white px-2 text-[11px] font-semibold text-[#303030] shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
      title={user.display_name}
    >
      {initials}
    </div>
  );
}
