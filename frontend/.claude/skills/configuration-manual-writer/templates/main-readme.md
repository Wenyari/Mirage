# {{projectName}} 配置项手册

## 概述

本手册详细说明了 {{projectName}} 的所有配置项，包括参数类型、默认值、使用示例等。

## 快速导航

- [配置项索引](./config-index.md) - 查看所有配置项的层级结构
- [快速开始](#快速开始) - 最简配置示例
- [完整配置示例](#完整配置示例) - 包含所有常用配置的示例

## 配置项分类

{{#each categories}}
### {{icon}} {{name}}
{{#each modules}}
- [{{title}}]({{link}}) - {{description}}
{{/each}}
{{/each}}

## 快速开始

最简配置示例：

\`\`\`{{codeLanguage}}
{{quickStartExample}}
\`\`\`

## 完整配置示例

\`\`\`{{codeLanguage}}
{{fullExample}}
\`\`\`

## 版本信息

- **当前版本**: {{version}}
- **最后更新**: {{lastUpdate}}
- **适用版本**: {{applicableVersion}}

---

**变量说明**：
- `projectName`: 项目名称
- `categories`: 配置项分类列表
- `codeLanguage`: 代码语言（javascript/typescript）
- `quickStartExample`: 快速开始示例代码
- `fullExample`: 完整配置示例代码
- `version`: 文档版本
- `lastUpdate`: 最后更新日期
- `applicableVersion`: 适用的产品版本