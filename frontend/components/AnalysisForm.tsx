"use client";

import { useId, useState, type FormEvent } from "react";
import { ArrowRight, CircleNotch } from "@phosphor-icons/react";
import { EXAMPLE_CAPABILITIES, EXAMPLE_COMPANIES } from "@/lib/constants";
import MagneticButton from "@/components/MagneticButton";

interface AnalysisFormProps {
  onSubmit: (company: string, capability: string) => void;
  isLoading?: boolean;
}

interface FieldErrors {
  company?: string;
  capability?: string;
}

const inputClass =
  "w-full border border-line bg-surface px-4 py-3.5 text-text placeholder:text-faint transition-[border-color,box-shadow] duration-200 hover:border-chrome focus:border-accent focus:outline-none disabled:opacity-60 aria-[invalid=true]:border-accent";

export default function AnalysisForm({
  onSubmit,
  isLoading = false,
}: AnalysisFormProps) {
  const companyId = useId();
  const capabilityId = useId();
  const [company, setCompany] = useState("");
  const [capability, setCapability] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedCompany = company.trim();
    const trimmedCapability = capability.trim();
    const nextErrors: FieldErrors = {};

    if (!trimmedCompany) {
      nextErrors.company = "Enter the company making the decision.";
    }
    if (!trimmedCapability) {
      nextErrors.capability = "Enter the capability you want to add.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    onSubmit(trimmedCompany, trimmedCapability);
  };

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="w-full space-y-7"
      data-testid="analysis-form"
    >
      <div className="space-y-2">
        <label
          htmlFor={companyId}
          className="block text-sm font-medium text-text"
        >
          Your company
        </label>
        <input
          id={companyId}
          name="company"
          type="text"
          autoComplete="organization"
          placeholder="Stripe"
          value={company}
          disabled={isLoading}
          aria-invalid={Boolean(errors.company)}
          aria-describedby={errors.company ? `${companyId}-error` : undefined}
          onChange={(event) => {
            setCompany(event.target.value);
            if (errors.company) setErrors((e) => ({ ...e, company: undefined }));
          }}
          className={inputClass}
        />
        {errors.company && (
          <p
            id={`${companyId}-error`}
            role="alert"
            className="text-sm text-accent"
            data-testid="company-error"
          >
            {errors.company}
          </p>
        )}
        <ExampleChips
          values={EXAMPLE_COMPANIES}
          disabled={isLoading}
          onPick={(value) => {
            setCompany(value);
            setErrors((e) => ({ ...e, company: undefined }));
          }}
        />
      </div>

      <div className="space-y-2">
        <label
          htmlFor={capabilityId}
          className="block text-sm font-medium text-text"
        >
          Capability to add
        </label>
        <input
          id={capabilityId}
          name="capability"
          type="text"
          placeholder="AI voice"
          value={capability}
          disabled={isLoading}
          aria-invalid={Boolean(errors.capability)}
          aria-describedby={
            errors.capability ? `${capabilityId}-error` : undefined
          }
          onChange={(event) => {
            setCapability(event.target.value);
            if (errors.capability)
              setErrors((e) => ({ ...e, capability: undefined }));
          }}
          className={inputClass}
        />
        {errors.capability && (
          <p
            id={`${capabilityId}-error`}
            role="alert"
            className="text-sm text-accent"
            data-testid="capability-error"
          >
            {errors.capability}
          </p>
        )}
        <ExampleChips
          values={EXAMPLE_CAPABILITIES}
          disabled={isLoading}
          onPick={(value) => {
            setCapability(value);
            setErrors((e) => ({ ...e, capability: undefined }));
          }}
        />
      </div>

      <MagneticButton>
        <button
          type="submit"
          disabled={isLoading}
          className="group inline-flex items-center justify-center gap-2.5 bg-accent-deep px-7 py-4 font-medium whitespace-nowrap text-on-accent transition-[background-color,transform] duration-200 hover:bg-accent active:translate-y-px disabled:opacity-60"
          data-testid="analyze-button"
        >
          {isLoading ? (
            <>
              <CircleNotch size={18} weight="bold" className="animate-spin" />
              Scoring
            </>
          ) : (
            <>
              Analyze strategy
              <ArrowRight
                size={18}
                weight="bold"
                className="transition-transform duration-300 ease-out group-hover:translate-x-1"
              />
            </>
          )}
        </button>
      </MagneticButton>
    </form>
  );
}

function ExampleChips({
  values,
  disabled,
  onPick,
}: {
  values: readonly string[];
  disabled: boolean;
  onPick: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2 pt-1">
      {values.map((value) => (
        <button
          key={value}
          type="button"
          disabled={disabled}
          onClick={() => onPick(value)}
          className="border border-line px-3 py-1 text-sm text-muted transition-[color,border-color,transform] duration-200 hover:-translate-y-px hover:border-chrome hover:text-text active:translate-y-0 disabled:opacity-60"
        >
          {value}
        </button>
      ))}
    </div>
  );
}
