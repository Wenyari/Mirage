--- 
name: write_doc
description: 生成项目的技术文档
---

### 必须遵守
1.使用中文写作

### 项目元信息

**在生成任何技术文档前，必须先读取项目元信息配置文件获取准确信息。**

**配置文件位置：** `.claude/docs_meta/project.yaml`

**禁止臆造以下内容：**
- 开发环境版本要求（Node.js、包管理器等）
- 项目依赖及其版本号
- 开发命令、构建命令、测试命令
- 构建产物路径和文件名
- 部署地址、CDN 链接、NPM 包名
- Git 分支策略、Commit 规范等团队约定
- 目录结构和架构设计

**如何使用：**
1. 生成文档前，先用 Read 工具读取 `.claude/docs_meta/project.yaml`
2. 从配置文件中获取相关信息填充到模板中
3. 如果配置文件中缺少某些信息，使用占位符（如 `[待补充：具体信息]`）而非猜测
4. 引用版本号时，使用配置文件中的精确版本

**配置文件包含的信息类别：**
- `project` - 项目基本信息（名称、版本、仓库地址等）
- `environment` - 开发环境要求（Node.js、IDE、浏览器等）
- `dependencies` - 核心依赖及版本
- `development` - 开发命令和工具
- `build` - 构建命令和产物
- `deployment` - 部署信息（NPM、CDN 等）
- `team_conventions` - 团队约定（代码规范、Git 流程等）
- `architecture` - 架构信息
- `troubleshooting` - 常见问题解决方案

### 指导
1.根据当前的写作内容，判断使用哪种类型模版
2.然后在对应的模版中，获取模板内容
3.根据模板结构生成对应的文档

### 模板列表
1.base_project_information_template
- 类型：生成项目概览与基础信息的文档模板
- 相对路径: .claude/skills/write_doc/templates/base_project_information_template.md

2. common_template的相对路径
- 类型：通用模版，用于生成其他类型的文档
- 相对路径: .claude/skills/write_doc/templates/common_template.md

3.explanation_of_core_concepts_template
- 类型：通用模版，用于生成
- 相对路径: .claude/skills/write_doc/templates/explanation_of_core_concepts_template.md

4.quick_start_temlate
- 类型：生成快速开始与操作指引的文档
- 相对路径：.claude/skills/write_doc/templates/quick_start_temlate.md


5.technical_architecture_and_system_design_template
- 类型：用于生成技术架构与系统设计的文档
- 相对路径:.claude/skills/write_doc/templates/technical_architecture_and_system_design_template.md

### 权限
允许调用所有的工具

### 写作规范注意
- 代码块：必须指定语言（如 ```typescript），关键逻辑请添加注释。

- 排版：
  - 重点词汇使用 加粗。
  - 文件路径、参数名、简单的命令使用 行内代码块。
  - 层级不要超过 4 层（避免使用 #####）。

- 文档拆分：
    - **拆分时机**：当文档超过 5个一级章节时，应考虑拆分成文档系列。
    - **命名规范**：使用序号前缀（如`01-项目概览.md`、`02-快速开始.md`），保持命名简洁清晰。
    - **索引文档**：必须创建 `README.md` 或 `INDEX.md`作为导航入口，包含文档列表、阅读顺序和简要说明。
    - **主题完整性**：优先保证每个子文档的主题完整，避免在逻辑中间切
  断内容。
    - **避免过度拆分**：章节内容少于 500 字时，考虑与相关内容合并。

- 语气：保持客观、专业、鼓励性。避免使用“很简单”、“显然”等词汇。
- 图表：涉及复杂逻辑时，尽量提供 Mermaid 图或截图。
- 链接：章节间引用请使用相对路径，方便 Git 仓库浏览。
