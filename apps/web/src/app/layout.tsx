import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pelatnas Competition Platform",
  description: "Phase 0 foundation for the competition platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

