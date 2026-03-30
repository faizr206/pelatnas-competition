import Link from "next/link";
import { ReactNode } from "react";

import { SiteBrand } from "@/components/site-brand";
import { cn } from "@/lib/utils";

type NavigationKey = "home" | "competitions" | "more";

type SiteHeaderProps = {
  activeNav: NavigationKey;
  action: ReactNode;
};

const navItems: Array<{
  key: NavigationKey;
  href: string;
  label: string;
}> = [
  { key: "home", href: "/", label: "Home" },
  { key: "competitions", href: "/competitions", label: "Competitions" },
  { key: "more", href: "/#", label: "More" },
];

export function SiteHeader({ activeNav, action }: SiteHeaderProps) {
  return (
    <header className="border-b border-[#ebebeb] bg-[#ededed]">
      <div className="mx-auto flex max-w-[1904px] flex-col gap-4 px-6 py-4 md:grid md:min-h-[75px] md:grid-cols-[1fr_auto_1fr] md:items-center md:gap-6 md:px-8 md:py-0">
        <SiteBrand className="justify-self-start" />
        <nav className="flex items-center justify-start gap-4 md:justify-center">
          {navItems.map((item) => (
            <Link
              key={item.key}
              href={item.href}
              className={cn(
                "inline-flex h-9 items-center rounded-[8px] px-4 text-xs font-medium text-[#202020] transition-colors",
                activeNav === item.key ? "bg-[#e1e1e1]" : "hover:bg-[#e6e6e6]",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex min-h-9 items-center justify-start md:justify-end">
          {action}
        </div>
      </div>
    </header>
  );
}
