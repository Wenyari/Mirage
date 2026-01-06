---
allowed-tools: AskUserQuestion, Read, Glob, Write, Task, TODOWriter
---

# 配置项手册生成

快速启动配置项手册生成任务，帮助你创建类似 ECharts 风格的配置项文档。

## 使用方式
输入 `/configuration-manual` 启动此命令

## 工作流程
1. 确认配置目标（项目/组件名称）
2. 确认配置范围（全部/特定模块）
3. 调用 configuration-manual-writer Agent
4. 生成配置项手册

## 示例
用户: /configuration-manual
系统: 需要为哪个项目生成配置项手册？
用户: paradigm-chart
系统: 启动 configuration-manual-writer Agent...