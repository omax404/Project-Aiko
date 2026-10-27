import type { NextConfig } from "next";

// Baseline security headers for every route.
//
// Notes (no build was run when this was added -- website/node_modules is absent):
// - Next's App Router emits inline bootstrap/streaming scripts, so `script-src` needs
//   'unsafe-inline' unless a nonce-based middleware is introduced. There is deliberately
//   no 'unsafe-eval'. Tightening to a nonce is the documented follow-up.
// - `style-src` needs 'unsafe-inline' because the site uses inline style attributes
//   (emotion colours are data-driven from content.ts).
// - next/font self-hosts the woff2 files, so `font-src 'self'` is sufficient.
// - No analytics/embeds/forms exist today, so `connect-src`/`form-action` stay 'self'.
const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self' data:",
      "connect-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "object-src 'none'",
    ].join("; "),
  },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains",
  },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=()",
  },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["three"],
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
