import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import AnalysisForm from "@/components/AnalysisForm";

describe("AnalysisForm", () => {
  it("blocks an empty submit and says what is missing", async () => {
    const onSubmit = vi.fn();
    render(<AnalysisForm onSubmit={onSubmit} />);

    await userEvent.click(screen.getByTestId("analyze-button"));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByTestId("company-error")).toBeInTheDocument();
    expect(screen.getByTestId("capability-error")).toBeInTheDocument();
  });

  it("rejects whitespace-only input", async () => {
    const onSubmit = vi.fn();
    render(<AnalysisForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText("Your company"), "   ");
    await userEvent.type(screen.getByLabelText("Capability to add"), "   ");
    await userEvent.click(screen.getByTestId("analyze-button"));

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits trimmed values", async () => {
    const onSubmit = vi.fn();
    render(<AnalysisForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText("Your company"), "  Ramp  ");
    await userEvent.type(
      screen.getByLabelText("Capability to add"),
      "  Fraud detection  ",
    );
    await userEvent.click(screen.getByTestId("analyze-button"));

    expect(onSubmit).toHaveBeenCalledWith("Ramp", "Fraud detection");
  });

  it("fills only its own field when an example chip is picked", async () => {
    render(<AnalysisForm onSubmit={vi.fn()} />);

    const company = screen.getByLabelText("Your company") as HTMLInputElement;
    const capability = screen.getByLabelText(
      "Capability to add",
    ) as HTMLInputElement;

    await userEvent.type(capability, "Speech synthesis");
    await userEvent.click(screen.getByRole("button", { name: "Stripe" }));

    expect(company.value).toBe("Stripe");
    expect(capability.value).toBe("Speech synthesis");
  });

  it("clears a field error once the reader starts fixing it", async () => {
    render(<AnalysisForm onSubmit={vi.fn()} />);

    await userEvent.click(screen.getByTestId("analyze-button"));
    expect(screen.getByTestId("company-error")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Your company"), "V");
    expect(screen.queryByTestId("company-error")).not.toBeInTheDocument();
  });
});
