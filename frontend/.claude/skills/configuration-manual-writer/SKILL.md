---
name: configuration-manual-writer
description: 生成 ECharts 风格的配置项手册
---

## 核心功能
生成结构化的配置项手册，包括：
- 配置项索引（导航树）
- 主目录文档
- 配置项详细说明
- 模块配置文档

## 工作流程
1. 输入分析（配置项列表、层级结构）
2. 选择合适的模板
3. 生成文档
4. 格式验证

## 模板列表

### 1. 配置项索引模板 (config-index.md)
- 用途：生成配置项导航树
- 适用场景：所有配置项手册
- 相对路径：`.claude/skills/configuration-manual-writer/templates/config-index.md`

### 2. 主目录模板 (main-readme.md)
- 用途：生成配置手册主入口
- 适用场景：所有配置项手册
- 相对路径：`.claude/skills/configuration-manual-writer/templates/main-readme.md`

### 3. 配置项详细说明模板 (config-item-detail.md)
- 用途：生成单个配置项的详细文档
- 适用场景：配置项详细说明
- 相对路径：`.claude/skills/configuration-manual-writer/templates/config-item-detail.md`

### 4. 模块配置文档模板 (module-config.md)
- 用途：生成某个模块的所有配置项文档
- 适用场景：分模块的配置手册
- 相对路径：`.claude/skills/configuration-manual-writer/templates/module-config.md`

## 规范要求

### 1. 配置项路径命名
- 使用点号分隔：`chart.title.text`
- 数组使用 `[]`：`series[].data`

### 2. 类型表示
- 使用 TypeScript 风格
- 支持联合类型、函数类型等

### 3. 文档格式
- Markdown 格式
- 统一的章节结构
- 代码示例必须可运行

### 4. 质量标准
- 配置项完整覆盖
- 类型信息准确
- 示例代码验证

## 权限
需要以下工具权限：
- `Read` - 读取项目文件
- `Write` - 生成文档
- `Glob` / `Grep` - 搜索配置定义