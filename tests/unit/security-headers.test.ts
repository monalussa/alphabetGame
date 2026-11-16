import { describe, expect, it } from 'vitest';
import {
  CONTENT_SECURITY_POLICY,
  META_CONTENT_SECURITY_POLICY,
  SECURITY_HEADERS,
  buildHeadersFile,
} from '../../config/security-headers';

describe('security headers', () => {
  it.each([CONTENT_SECURITY_POLICY, META_CONTENT_SECURITY_POLICY])(
    'CSP never allows unsafe sources: %s',
    (policy) => {
      expect(policy).not.toMatch(/unsafe-|data:|blob:|\*|https?:/);
    },
  );

  it('header CSP forbids framing, which a meta CSP cannot express', () => {
    expect(CONTENT_SECURITY_POLICY).toContain("frame-ancestors 'none'");
    expect(META_CONTENT_SECURITY_POLICY).not.toContain('frame-ancestors');
  });

  it('headers file applies every header to all paths', () => {
    const file = buildHeadersFile();

    expect(file.startsWith('/*\n')).toBe(true);
    for (const name of Object.keys(SECURITY_HEADERS)) {
      expect(file).toContain(`  ${name}: `);
    }
  });
});
