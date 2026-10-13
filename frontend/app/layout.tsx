import type { Metadata } from "next";
import { Geist, Fragment_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

/**
 * The face the ThreeUI dock is set in (SIL OFL 1.1). Loaded through next/font
 * rather than the base64 copy embedded in the package stylesheet, so it is
 * subset and self-hosted like the rest of the type.
 */
const fragmentMono = Fragment_Mono({
  variable: "--font-fragment-mono",
  weight: "400",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Decision Engine: Build, Partner or Acquire",
  description:
    "Score the build, partner and acquire paths to a new capability against live hiring, funding and technographic signals.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${fragmentMono.variable} h-full`}
    >
      <body className="min-h-full flex flex-col bg-canvas text-muted">
        {children}
      </body>
    </html>
  );
}
