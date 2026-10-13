"use client";

import { ArrowClockwise, WarningCircle } from "@phosphor-icons/react";
import MagneticButton from "@/components/MagneticButton";

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="max-w-[62ch] py-12" data-testid="error-state" role="alert">
      <WarningCircle size={32} weight="light" className="text-accent" />

      <h2 className="mt-7 text-4xl font-semibold tracking-[-0.035em] md:text-5xl">
        The analysis did not complete
      </h2>
      <p className="mt-5 text-lg leading-relaxed text-muted">{message}</p>

      <MagneticButton className="mt-10">
        <button
          type="button"
          onClick={onRetry}
          className="group inline-flex items-center gap-2.5 bg-accent-deep px-6 py-3 font-medium whitespace-nowrap text-on-accent transition-[background-color,transform] duration-200 hover:bg-accent active:translate-y-px"
          data-testid="retry-button"
        >
          <ArrowClockwise
            size={17}
            weight="bold"
            className="transition-transform duration-500 ease-out group-hover:rotate-180"
          />
          Try again
        </button>
      </MagneticButton>
    </div>
  );
}
