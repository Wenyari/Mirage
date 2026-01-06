# {{moduleName}} 配置

## 模块概述

{{moduleDescription}}

## 配置项列表

本模块包含以下配置项：

{{#each configItems}}
### {{path}}

**类型**: `{{type}}` | **默认值**: `{{defaultValue}}` | **必需**: {{required}}

{{description}}

{{#if hasExample}}
**示例**：
\`\`\`{{../codeLanguage}}
{{example}}
\`\`\`
{{/if}}

[查看详细说明 →]({{detailLink}})

---
{{/each}}

## 完整示例

\`\`\`{{codeLanguage}}
{{moduleFullExample}}
\`\`\`

## 相关模块

{{#each relatedModules}}
- [{{name}}]({{link}}) - {{description}}
{{/each}}

---

**变量说明**：
- `moduleName`: 模块名称
- `moduleDescription`: 模块描述
- `configItems`: 该模块的配置项列表
- `moduleFullExample`: 模块完整配置示例
- `relatedModules`: 相关模块列表