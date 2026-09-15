export default function LoadingState({
  capability,
}: {
  capability?: string;
}) {
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-8 p-6"
      data-testid="loading-state"
    >
      <div className="relative">
        <div className="w-16 h-16 border-4 border-crustdata-blue/30 border-t-crustdata-blue rounded-full animate-spin" />
        <div className="absolute inset-0 w-16 h-16 border-4 border-crustdata-accent/20 border-b-crustdata-accent rounded-full animate-ping" />
      </div>

      <div className="text-center space-y-3">
        <h2 className="text-2xl font-semibold text-crustdata-light">
          Analyzing your strategy
        </h2>
        <p className="text-crustdata-light/60 max-w-md">
          {capability
            ? `Scoring Build, Partner, and Acquire paths for "${capability}"...`
            : "Scoring Build, Partner, and Acquire paths..."}
        </p>
      </div>

      <div className="flex gap-3">
        {["Build", "Partner", "Acquire"].map((path) => (
          <div
            key={path}
            className="px-4 py-2 bg-crustdata-dark/50 border border-crustdata-blue/20 rounded-lg"
          >
            <span className="text-sm font-medium text-crustdata-light">
              {path}
            </span>
          </div>
        ))}
      </div>

      <div className="w-full max-w-2xl space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-3 bg-gray-700/30 rounded-full animate-pulse"
            style={{ width: `${80 - i * 10}%` }}
          />
        ))}
      </div>
    </div>
  );
}
