// ============================================================
// page.tsx — the homepage at "/".
// It simply stacks the section components in order. Keeping the
// page thin (just composition) and the sections separate makes
// each piece easy to edit and reuse.
// ============================================================

import Hero from "@/components/home/Hero";
import HowItWorks from "@/components/home/HowItWorks";
import Features from "@/components/home/Features";
import About from "@/components/home/About";

export default function HomePage() {
  return (
    <>
      <Hero />
      <HowItWorks />
      <Features />
      <About />
    </>
  );
}
