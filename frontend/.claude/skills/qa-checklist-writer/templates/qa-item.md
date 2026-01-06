#### {{itemNumber}} {{title}}

**问题描述**：
{{description}}

**根本原因**：
{{rootCause}}

**解决方案**：
{{solution}}

{{#if codeExample}}
**代码示例**：
\`\`\`{{codeLanguage}}
{{codeExample}}
\`\`\`
{{/if}}

{{#if relatedInfo}}
**相关信息**：
{{#each relatedInfo}}
- {{this}}
{{/each}}
{{/if}}

{{#if affectedVersions}}
**影响版本**：{{affectedVersions}}
{{/if}}

{{#if relatedIssues}}
**相关 Issue**：
{{#each relatedIssues}}
- #{{this}}
{{/each}}
{{/if}}

{{#if references}}
**参考文档**：
{{#each references}}
- [{{title}}]({{url}})
{{/each}}
{{/if}}