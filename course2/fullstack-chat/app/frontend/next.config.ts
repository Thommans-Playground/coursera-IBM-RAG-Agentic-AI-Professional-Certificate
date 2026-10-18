import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // a small server bundle, used by the Docker image
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
