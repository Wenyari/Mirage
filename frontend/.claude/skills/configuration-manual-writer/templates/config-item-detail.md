# {{configPath}}

## 基本信息

- **类型**: `{{type}}`
- **默认值**: `{{defaultValue}}`
- **是否必需**: {{required}}
- **适用版本**: {{sinceVersion}}+

## 描述

{{description}}

{{#if typeDefinition}}
## 类型说明

\`\`\`typescript
{{typeDefinition}}
\`\`\`
{{/if}}

{{#if enumValues}}
## 可选值

| 值 | 说明 |
|---|---|
{{#each enumValues}}
| `{{value}}` | {{description}} |
{{/each}}
{{/if}}

## 示例

### 基础示例

\`\`\`{{codeLanguage}}
{{basicExample}}
\`\`\`

{{#if advancedExample}}
### 高级示例

\`\`\`{{codeLanguage}}
{{advancedExample}}
\`\`\`
{{/if}}

{{#if notes}}
## 注意事项

{{#each notes}}
- {{this}}
{{/each}}
{{/if}}

{{#if relatedConfigs}}
## 相关配置

{{#each relatedConfigs}}
- [{{path}}]({{link}}) - {{description}}
{{/each}}
{{/if}}

{{#if references}}
## 参考资源

{{#each references}}
- [{{title}}]({{url}})
{{/each}}
{{/if}}

---

**变量说明**：
- `configPath`: 配置项完整路径
- `type`: 类型字符串
- `defaultValue`: 默认值
- `required`: 是否必需（是/否）
- `sinceVersion`: 引入版本
- `description`: 详细描述
- `typeDefinition`: TypeScript 类型定义
- `enumValues`: 枚举值列表
- `basicExample`: 基础示例代码
- `advancedExample`: 高级示例代码
- `notes`: 注意事项列表
- `relatedConfigs`: 相关配置项
- `references`: 参考资源链接