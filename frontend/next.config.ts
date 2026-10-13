import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * Emit a self-contained server bundle with only the dependencies the app
   * actually reaches. @designcodeio/threeui unpacks to ~55MB, almost all of it
   * demo assets and a second copy of three.js that this app never imports, so
   * shipping the whole node_modules tree into the runtime image made it far
   * larger than it needed to be and slowed Cloud Run cold starts.
   */
  output: "standalone",
};

export default nextConfig;
