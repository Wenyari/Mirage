---
name: qa-checklist-writer
description: 生成 QA 问题清单文档
---

## 核心功能
生成结构化的 QA 问题清单，包括：
- 分类的 QA 条目列表
- 每个条目的详细解决方案
- Issue 提交指南
- 贡献指南

## 工作流程
1. 输入分析（问题列表、分类信息）
2. 选择合适的模板
3. 生成文档
4. 格式验证

## 模板列表

### 1. 主文档模板 (qa-checklist-main.md)
- 用途：生成完整的 QA 问题清单文档
- 适用场景：所有 QA 清单
- 相对路径：`.claude/skills/qa-checklist-writer/templates/qa-checklist-main.md`

### 2. QA 条目模板 (qa-item.md)
- 用途：生成单个 QA 条目的详细说明
- 适用场景：QA 条目生成
- 相对路径：`.claude/skills/qa-checklist-writer/templates/qa-item.md`

## 规范要求

### 1. QA 条目格式
- 编号格式：`Q[分类编号].[序号]`
- 必须包含：问题描述、根本原因、解决方案
- 可选包含：相关信息、影响版本、相关 Issue、代码示例

### 2. 问题分类
- 报错类问题（Q1.x）
- 渲染异常类问题（Q2.x）
- 性能问题类（Q3.x）
- 配置问题类（Q4.x）

### 3. 文档结构
- 文档说明（如何使用）
- 按分类组织的 QA 条目列表
- Issue 提交指南
- 贡献指南
- 元数据

## 权限
需要以下工具权限：
- `Read` - 读取项目文件
- `Write` - 生成文档
- `Glob` / `Grep` - 搜索问题信息
- `AskUserQuestion` - 与用户交互收集问题