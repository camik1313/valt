// ============================================================
// layout.tsx — the shell wrapped around EVERY page in the app.
// Whatever a page renders appears where {children} is below.
// This is where we load fonts, set the browser tab title, and
// place the site-wide Navbar and Footer.
// ============================================================

import type { Metadata } from "next";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";

// next/font loads Google Fonts at build time (fast, private, no layout shift).
// Each font is assigned to a CSS variable that Tailwind reads (see tailwind.config).
const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});
const body = Inter({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

// Metadata shows up in the browser tab and in link previews / search results.
export const metadata: Metadata = {
  title: "VALT: Movement analysis for jump landings",
  description:
    "Measure biomechanical patterns associated with ACL injury risk from a smartphone video. Not a diagnostic tool.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <body className="min-h-screen flex flex-col">
        <Navbar />
        {/* Each page's content renders here */}
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
