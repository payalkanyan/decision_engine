interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-8 p-6 text-center"
      data-testid="error-state"
    >
      <div className="w-20 h-20 bg-red-500/10 border border-red-500/30 rounded-full flex items-center justify-center">
        <svg
          className="w-10 h-10 text-red-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>

      <div className="space-y-3 max-w-md">
        <h2 className="text-2xl font-semibold text-crustdata-light">
          Something went wrong
        </h2>
        <p className="text-crustdata-light/60 text-sm leading-relaxed">
          {message}
        </p>
      </div>

      <button
        onClick={onRetry}
        className="px-6 py-3 bg-crustdata-blue hover:bg-crustdata-blue/90 text-white font-medium rounded-lg transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-crustdata-blue focus:ring-offset-2 focus:ring-offset-crustdata-dark"
        data-testid="retry-button"
      >
        Try Again
      </button>
    </div>
  );
}
