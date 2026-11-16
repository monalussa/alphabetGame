// Single source of truth for security headers: vite.config.ts injects the CSP <meta>
// into the built index.html and emits public `_headers` (Netlify / Cloudflare Pages).
// A <meta> CSP cannot carry frame-ancestors, so that directive is header-only.

const META_CSP_DIRECTIVES: Readonly<Record<string, string>> = {
  'default-src': "'self'",
  'script-src': "'self'",
  'style-src': "'self'",
  'img-src': "'self'",
  'media-src': "'self'",
  'font-src': "'self'",
  'connect-src': "'self'",
  'manifest-src': "'self'",
  'worker-src': "'self'",
  'object-src': "'none'",
  'base-uri': "'none'",
  'form-action': "'none'",
};

const HEADER_ONLY_CSP_DIRECTIVES: Readonly<Record<string, string>> = {
  'frame-ancestors': "'none'",
};

function serializeDirectives(directives: Readonly<Record<string, string>>): string {
  return Object.entries(directives)
    .map(([name, value]) => `${name} ${value}`)
    .join('; ');
}

export const META_CONTENT_SECURITY_POLICY = serializeDirectives(META_CSP_DIRECTIVES);

export const CONTENT_SECURITY_POLICY = serializeDirectives({
  ...META_CSP_DIRECTIVES,
  ...HEADER_ONLY_CSP_DIRECTIVES,
});

export const SECURITY_HEADERS: Readonly<Record<string, string>> = {
  'Content-Security-Policy': CONTENT_SECURITY_POLICY,
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'no-referrer',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Resource-Policy': 'same-origin',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Permissions-Policy':
    'camera=(), microphone=(), geolocation=(), payment=(), usb=(), serial=(), bluetooth=(), ' +
    'midi=(), display-capture=(), browsing-topics=(), fullscreen=(self), autoplay=(self)',
};

export function buildHeadersFile(
  headers: Readonly<Record<string, string>> = SECURITY_HEADERS,
): string {
  const lines = Object.entries(headers).map(([name, value]) => `  ${name}: ${value}`);
  return ['/*', ...lines, ''].join('\n');
}
