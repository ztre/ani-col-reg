import js from '@eslint/js'
import tsPlugin from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser'
import eslintConfigPrettier from 'eslint-config-prettier'
import vuePlugin from 'eslint-plugin-vue'
import globals from 'globals'
import vueParser from 'vue-eslint-parser'

const sharedGlobals = {
  ...globals.browser,
  ...globals.es2021,
  ...globals.node,
}

const typescriptRules = {
  ...tsPlugin.configs.recommended.rules,
  'no-undef': 'off',
  '@typescript-eslint/no-unused-vars': 'off',
}

export default [
  {
    ignores: ['dist/**', 'node_modules/**', 'coverage/**', 'tsconfig.tsbuildinfo'],
  },
  js.configs.recommended,
  ...vuePlugin.configs['flat/recommended'],
  {
    files: ['src/**/*.ts', 'vite.config.ts'],
    languageOptions: {
      parser: tsParser,
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: sharedGlobals,
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: typescriptRules,
  },
  {
    files: ['src/**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
        ecmaVersion: 'latest',
        sourceType: 'module',
        extraFileExtensions: ['.vue'],
      },
      globals: sharedGlobals,
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      ...typescriptRules,
      'vue/multi-word-component-names': 'off',
    },
  },
  eslintConfigPrettier,
]