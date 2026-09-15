interface ScoreProgressProps {
  score: number;
  maxScore?: number;
  label?: string;
  size?: "sm" | "md" | "lg";
}

export default function ScoreProgress({
  score,
  maxScore = 10,
  label,
  size = "md",
}: ScoreProgressProps) {
  const percentage = Math.min(100, (score / maxScore) * 100);
  const heightClass = size === "sm" ? "h-2" : size === "lg" ? "h-4" : "h-3";

  const getColorClass = (pct: number) => {
    if (pct >= 70) return "bg-crustdata-blue";
    if (pct >= 40) return "bg-amber-400";
    return "bg-red-400";
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        {label && (
          <span className="text-sm font-medium text-crustdata-light">
            {label}
          </span>
        )}
        <span className="text-sm font-bold text-crustdata-blue">
          {score.toFixed(1)}/{maxScore}
        </span>
      </div>
      <div
        className={`w-full bg-gray-700/50 rounded-full overflow-hidden ${heightClass} transition-all duration-500`}
      >
        <div
          className={`${heightClass} ${getColorClass(percentage)} transition-all duration-700 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
