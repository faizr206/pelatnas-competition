import Link from "next/link";

import { cn } from "@/lib/utils";

type SiteBrandProps = {
  className?: string;
  href?: string;
};

export function SiteBrand({ className, href = "/" }: SiteBrandProps) {
  return (
    <Link
      href={href}
      className={cn("inline-flex items-center gap-2 text-sm font-semibold text-black", className)}
    >
      <span className="inline-flex h-6 w-6 items-center justify-center text-black">
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="h-4.5 w-4.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.9"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="7" cy="7" r="2.25" />
          <circle cx="17" cy="7" r="2.25" />
          <circle cx="7" cy="17" r="2.25" />
          <circle cx="17" cy="17" r="2.25" />
          <path d="M9.2 7h5.6" />
          <path d="M7 9.2v5.6" />
          <path d="M17 9.2v5.6" />
          <path d="M9.2 17h5.6" />
        </svg>
      </span>
      <span>Pelatnas Competition</span>
    </Link>
  );
}
