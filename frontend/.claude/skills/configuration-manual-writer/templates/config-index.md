# 配置项索引

本页面列出了所有可用的配置项，点击配置项名称可跳转到详细说明。

## 配置项层级结构

### {{rootConfigName}}
{{#each configTree}}
- [{{path}}]({{link}}) - {{description}}
  {{#if children}}
  {{#each children}}
  - [{{path}}]({{link}}) - {{description}}
  {{/each}}
  {{/if}}
{{/each}}

## 按功能分类

### {{categoryName}}
{{#each categoryItems}}
- [{{path}}]({{link}}) - {{description}}
{{/each}}

---

**变量说明**：
- `rootConfigName`: 根配置对象名称（如 `chart`）
- `configTree`: 配置项树形结构
- `path`: 配置项路径（如 `chart.title.text`）
- `link`: 跳转链接
- `description`: 配置项简短描述
- `categoryName`: 分类名称
- `categoryItems`: 该分类下的配置项列表