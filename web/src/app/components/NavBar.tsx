"use client";

import Link from "next/link";

const LINKS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/library", label: "Library" },
  { href: "/brand-models", label: "Brand Models" },
  { href: "/profile", label: "Profile" },
];

export default function NavBar() {
  return (
    <nav className="flex items-center gap-6 border-b border-zinc-200 px-6 py-3 dark:border-zinc-800">
      <span className="font-semibold">MomentA</span>
      {LINKS.map((link) => (
        <Link key={link.href} href={link.href} className="text-sm text-zinc-600 hover:text-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50">
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
