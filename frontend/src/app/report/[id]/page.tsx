// Placeholder for the "/report/[id]" route.
// The real report view (graphs + metrics) is built in Stage 6.
// The [id] in the folder name becomes params.id here.
export default function ReportPage({ params }: { params: { id: string } }) {
  return (
    <section className="mx-auto max-w-3xl px-6 py-28 text-center">
      <span className="font-mono text-xs uppercase tracking-widest text-track">
        Stage 6
      </span>
      <h1 className="mt-3 font-display text-3xl font-bold text-ink">
        Report view coming soon
      </h1>
      <p className="mt-4 text-muted">
        This page will show the full report for analysis{" "}
        <span className="font-mono text-ink">{params.id}</span>.
      </p>
    </section>
  );
}
