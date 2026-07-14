export function NeuralNode() {
  return (
    <div className="relative w-6 h-6">
      <div className="absolute inset-0 bg-[var(--accent)]/20 blur-[6px] rounded-full animate-pulse" />
      <div className="relative w-full h-full rounded-full border border-[var(--accent)]/40 flex items-center justify-center">
        <div className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" />
      </div>
    </div>
  );
}
