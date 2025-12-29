import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
// 引入新安装的插件
import tailwind from 'eslint-plugin-tailwindcss'
import simpleImportSort from 'eslint-plugin-simple-import-sort'
import jsxA11y from 'eslint-plugin-jsx-a11y'
import prettier from 'eslint-config-prettier'

export default tseslint.config(
  { ignores: ['dist'] },
  {
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommended,
      // 1. 引入 Tailwind 推荐配置 (扁平化配置需要放在 extends 或手动加载)
      ...tailwind.configs["flat/recommended"],
      // 2. 引入 Prettier 关闭冲突规则 (必须放在最后)
      prettier
    ],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      // 3. 注册插件
      'simple-import-sort': simpleImportSort,
      'jsx-a11y': jsxA11y,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],

      // --- Tailwind CSS 规则 ---
      // 允许在自定义组件中使用 class (shadcn cn 函数常用)
      'tailwindcss/no-custom-classname': 'off', 
      // 强制类名排序 (如果你没有装 prettier-plugin-tailwindcss，这个很有用)
      'tailwindcss/classnames-order': 'warn',

      // --- Import 排序规则 ---
      'simple-import-sort/imports': 'error',
      'simple-import-sort/exports': 'error',

      // --- 可访问性规则 (示例) ---
      ...jsxA11y.configs.recommended.rules,
    },
  },
)