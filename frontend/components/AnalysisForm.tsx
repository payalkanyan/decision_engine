interface AnalysisFormProps {
  onSubmit: (company: string, capability: string) => void;
  isLoading?: boolean;
  error?: string | null;
}

export default function AnalysisForm({
  onSubmit,
  isLoading = false,
  error = null,
}: AnalysisFormProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const company = (form.elements.namedItem("company") as HTMLInputElement)
      .value.trim();
    const capability = (
      form.elements.namedItem("capability") as HTMLInputElement
    ).value.trim();

    if (!company || !capability) {
      error;
      return;
    }
    onSubmit(company, capability);
  };

  const presetCompanies = ["Google", "Stripe", "Meta", "OpenAI"];
  const presetCapabilities = [
    "AI voice",
    "Real-time analytics",
    "Blockchain",
    "Computer vision",
  ];

  const fillForm = (company: string, capability: string) => {
    const form = document.querySelector("form") as HTMLFormElement;
    (form.elements.namedItem("company") as HTMLInputElement).value = company;
    (form.elements.namedItem("capability") as HTMLInputElement).value =
      capability;
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-2xl mx-auto space-y-6"
      data-testid="analysis-form"
    >
      <div className="space-y-2">
        <label
          htmlFor="company"
          className="block text-sm font-medium text-crustdata-light"
        >
          Your Company Name
        </label>
        <input
          type="text"
          name="company"
          id="company"
          placeholder="e.g. Google"
          defaultValue=""
          disabled={isLoading}
          className="w-full px-4 py-3 rounded-lg bg-crustdata-dark/50 border border-gray-700/50 text-crustdata-light placeholder-crustdata-light/40 focus:outline-none focus:ring-2 focus:ring-crustdata-blue focus:border-transparent transition-colors disabled:opacity-50"
        />
      </div>

      <div className="space-y-2">
        <label
          htmlFor="capability"
          className="block text-sm font-medium text-crustdata-light"
        >
          Capability You Want to Add
        </label>
        <input
          type="text"
          name="capability"
          id="capability"
          placeholder="e.g. AI voice"
          defaultValue=""
          disabled={isLoading}
          className="w-full px-4 py-3 rounded-lg bg-crustdata-dark/50 border border-gray-700/50 text-crustdata-light placeholder-crustdata-light/40 focus:outline-none focus:ring-2 focus:ring-crustdata-blue focus:border-transparent transition-colors disabled:opacity-50"
        />
      </div>

      {error && (
        <p className="text-red-400 text-sm" data-testid="form-error">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-3 px-6 bg-crustdata-blue hover:bg-crustdata-blue/90 disabled:bg-crustdata-blue/50 text-white font-semibold rounded-lg transition-all duration-200 hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-crustdata-blue focus:ring-offset-2 focus:ring-offset-crustdata-dark disabled:hover:scale-100"
        data-testid="analyze-button"
      >
        {isLoading ? "Analyzing..." : "Analyze Strategy"}
      </button>

      <div className="space-y-3">
        <p className="text-xs text-crustdata-light/60 uppercase tracking-wider">
          Example companies
        </p>
        <div className="flex flex-wrap gap-2">
          {presetCompanies.map((company) => (
            <button
              key={company}
              type="button"
              onClick={() => fillForm(company, "AI voice")}
              disabled={isLoading}
              className="px-3 py-1.5 text-sm text-crustdata-light/80 hover:text-crustdata-blue hover:bg-crustdata-dark/30 border border-crustdata-blue/20 rounded-full transition-colors disabled:opacity-50"
            >
              {company}
            </button>
          ))}
        </div>

        <p className="text-xs text-crustdata-light/60 uppercase tracking-wider">
          Example capabilities
        </p>
        <div className="flex flex-wrap gap-2">
          {presetCapabilities.map((cap) => (
            <button
              key={cap}
              type="button"
              onClick={() => fillForm("Your Company", cap)}
              disabled={isLoading}
              className="px-3 py-1.5 text-sm text-crustdata-light/80 hover:text-crustdata-blue hover:bg-crustdata-dark/30 border border-crustdata-blue/20 rounded-full transition-colors disabled:opacity-50"
            >
              {cap}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}
