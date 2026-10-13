import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ScoreMeter from "@/components/ScoreMeter";

describe("ScoreMeter", () => {
  // The visible digits are driven by a count-up that only starts once the
  // meter scrolls into view, so they are asserted through the value the
  // component reports rather than through whatever frame the tween is on.
  it("reports the score to one decimal against the maximum", () => {
    render(<ScoreMeter score={8.65} scored />);

    expect(screen.getByRole("meter")).toHaveAttribute(
      "aria-valuetext",
      "8.7 of 10",
    );
    expect(screen.getByText("/10")).toBeInTheDocument();
  });

  it("has the true value in the DOM before anything animates", () => {
    // Nothing has scrolled into view, so the server-rendered figure stands.
    render(<ScoreMeter score={7.1} scored />);

    expect(screen.getByText("7.1")).toBeInTheDocument();
  });

  it("says 'Not scored' rather than printing a zero", () => {
    render(<ScoreMeter score={0} scored={false} />);

    expect(screen.getByTestId("score-no-data")).toHaveTextContent("Not scored");
    expect(screen.queryByText("0.0")).not.toBeInTheDocument();
  });

  it("exposes the reading to assistive tech only when there is one", () => {
    const { rerender } = render(<ScoreMeter score={7.1} scored />);
    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow", "7.1");

    rerender(<ScoreMeter score={0} scored={false} />);
    expect(screen.getByRole("meter")).not.toHaveAttribute("aria-valuenow");
  });
});
