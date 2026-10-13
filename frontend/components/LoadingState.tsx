/**
 * Skeleton shaped like the results page, not a spinner. The reader sees where
 * the verdict, the three path rows and the candidate grid will land, so the
 * layout does not jump when the response arrives.
 */
export default function LoadingState({ capability }: { capability?: string }) {
  return (
    <div
      className="animate-pulse motion-reduce:animate-none"
      data-testid="loading-state"
      role="status"
      aria-live="polite"
    >
      <span className="sr-only">
        {capability
          ? `Scoring the build, partner and acquire paths for ${capability}`
          : "Scoring the build, partner and acquire paths"}
      </span>

      <Bar className="h-6 w-72" />

      <div className="mt-16 grid gap-12 border-b border-line pb-20 lg:grid-cols-12 lg:gap-16">
        <div className="space-y-6 lg:col-span-7">
          <Bar className="h-24 w-80" />
          <Bar className="h-4 w-full max-w-xl" />
          <Bar className="h-4 w-4/5 max-w-lg" />
        </div>
        <div className="space-y-5 lg:col-span-5 lg:pt-4">
          <Bar className="h-20 w-56" />
          <Bar className="h-1 w-full" />
          <Bar className="h-4 w-full" />
          <Bar className="h-4 w-2/3" />
        </div>
      </div>

      <div className="mt-20 border-t border-line">
        {[0, 1, 2].map((row) => (
          <div
            key={row}
            className="grid gap-6 border-b border-line py-10 lg:grid-cols-12 lg:gap-10"
          >
            <Bar className="h-9 w-32 lg:col-span-3" />
            <Bar className="h-9 w-28 lg:col-span-3" />
            <div className="space-y-3 lg:col-span-6">
              <Bar className="h-4 w-full max-w-xl" />
              <Bar className="h-4 w-3/5 max-w-md" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Bar({ className }: { className: string }) {
  return <div className={`bg-raised ${className}`} />;
}
