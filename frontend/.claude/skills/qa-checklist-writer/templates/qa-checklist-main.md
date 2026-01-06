# {{projectName}} 问题清单

## 如何使用本文档

本文档收录了 {{projectName}} 的常见问题及其解决方案。当你遇到问题时，可以：

1. **按分类查找**：根据问题类型（报错类、渲染异常类、性能问题类、配置问题类）查找对应的 QA 条目
2. **按关键词搜索**：使用浏览器的搜索功能（Ctrl+F / Cmd+F）搜索关键词
3. **查阅解决方案**：每个 QA 条目都包含详细的问题描述、根本原因和解决方案
4. **提交新问题**：如果问题未解决，请按照文档末尾的"提交 Issue 指南"准备信息并提交

---

## QA 问题清单

{{#each categories}}
### {{categoryNumber}}. {{categoryName}}

{{categoryDescription}}

{{#each items}}
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

---
{{/each}}
{{/each}}

---

## 提交 Issue 指南

如果通过查阅本文档仍无法解决问题，请按以下格式提交 Issue：

{{issueTemplateContent}}

---

## 贡献指南

我们欢迎你在解决问题后为本文档做出贡献！

### 如何补充新的问题案例

如果你遇到并解决了文档中未收录的问题，可以通过以下方式贡献：

1. **提交 Pull Request**：
   - Fork 本项目
   - 在对应的问题分类下添加新条目（参考 QA 条目模板）
   - 提交 PR，标题格式：`docs: 添加 QA 条目 - [简短问题描述]`

2. **提交 Issue**：
   - 如果不熟悉 PR 流程，可以创建 Issue
   - 使用标签 `documentation` 和 `qa-contribution`
   - 按照 QA 条目模板提供信息

### QA 条目模板

#### Q[分类编号].[序号] [简短问题标题]

**问题描述**：
[详细描述问题的表现形式、触发条件、影响范围]

**根本原因**：
[解释为什么会出现这个问题，涉及的技术原理]

**解决方案**：
[提供具体的修复步骤或配置调整方法]
- 步骤1：...
- 步骤2：...

**相关信息**（可选）：
- 影响版本：v1.x.x - v1.y.y
- 相关 Issue：#123
- 参考文档：[链接]---

## 元数据

- **文档版本**: {{version}}
- **最后更新**: {{lastUpdate}}
- **适用产品**: {{productName}} {{productVersion}}+
- **维护者**: {{maintainer}}
- **问题反馈**: [GitHub Issues]({{issuesUrl}})