import js from '@eslint/js';
import boundaries from 'eslint-plugin-boundaries';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import ts from 'typescript-eslint';
import svelteConfig from './svelte.config.js';

const UNSAFE_DOM_SINKS = [
  {
    selector: 'AssignmentExpression[left.property.name=/^(innerHTML|outerHTML)$/]',
    message: 'Do not write HTML strings into the DOM. Render text with Svelte instead.',
  },
  {
    selector: 'CallExpression[callee.property.name=/^(insertAdjacentHTML|write|writeln)$/]',
    message: 'Do not write HTML strings into the DOM. Render text with Svelte instead.',
  },
  {
    selector: 'Literal[value=/^(https?:)?\\/\\//]',
    message: 'No external URLs at runtime: every asset must be self-hosted.',
  },
];

export default ts.config(
  { ignores: ['dist/', 'coverage/', 'playwright-report/', 'test-results/', 'node_modules/'] },
  js.configs.recommended,
  ...ts.configs.strict,
  ...svelte.configs.recommended,
  {
    languageOptions: { globals: { ...globals.browser } },
    rules: {
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      'no-script-url': 'error',
      'no-restricted-syntax': ['error', ...UNSAFE_DOM_SINKS],
      'svelte/no-at-html-tags': 'error',
      'svelte/no-target-blank': 'error',
    },
  },
  {
    files: ['**/*.svelte', '**/*.svelte.ts'],
    languageOptions: {
      parserOptions: { parser: ts.parser, extraFileExtensions: ['.svelte'], svelteConfig },
    },
  },
  {
    files: ['src/**/*.{ts,svelte}'],
    plugins: { boundaries },
    settings: {
      'import/resolver': { node: { extensions: ['.ts', '.js', '.svelte'] } },
      'boundaries/elements': [
        { type: 'app', pattern: 'src/app/**', partialMatch: false },
        { type: 'games', pattern: 'src/games/*', capture: ['game'] },
        { type: 'ui', pattern: 'src/ui/**', partialMatch: false },
        { type: 'core', pattern: 'src/core/**', partialMatch: false },
      ],
    },
    rules: {
      'boundaries/no-unknown-files': 'error',
      'boundaries/dependencies': [
        'error',
        {
          default: 'disallow',
          policies: [
            {
              from: { element: { type: 'app' } },
              allow: { to: { element: { types: ['app', 'games', 'ui', 'core'] } } },
            },
            {
              from: { element: { type: 'games' } },
              allow: { to: { element: { types: ['ui', 'core'] } } },
            },
            {
              from: { element: { type: 'ui' } },
              allow: { to: { element: { types: ['ui', 'core'] } } },
            },
            { from: { element: { type: 'core' } }, allow: { to: { element: { type: 'core' } } } },
          ],
        },
      ],
    },
  },
  {
    files: ['tests/**/*.ts', 'config/**/*.ts', '*.config.{js,ts}'],
    languageOptions: { globals: { ...globals.node } },
    rules: { 'no-restricted-syntax': 'off' },
  },
);
