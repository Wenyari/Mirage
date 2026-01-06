/**
 * Claude Code 配置文件
 *
 * 此文件定义了 Claude Code 的 skills、agents 和 commands 配置
 * Claude Code 也会自动识别 .claude 目录下的文件结构
 */

export default {
  // Skills 配置
  skills: [
    {
      name: "write_doc",
      path: "./.claude/skills/write_doc",
      description: "生成项目的技术文档（项目概述、API参考、架构设计等）"
    },
    {
      name: "decision-tree-writer",
      path: "./.claude/skills/decision-tree-writer",
      description: "生成决策树形式的配置手册和QA清单"
    }
  ],

  // Agents 配置
  agents: [
    {
      name: "technical-doc-writer",
      path: "./.claude/agents/technical-doc-writer.md",
      description: "Technical documentation writer agent - 用于编写完整的技术文档"
    },
    {
      name: "decision-tree-writer",
      path: "./.claude/agents/decision-tree-writer.md",
      description: "Decision tree documentation agent - 用于创建决策树形式的文档"
    }
  ],

  // Commands 配置
  commands: [
    {
      name: "prompt-optimizer",
      path: "./.claude/commands/prompt-optimizer.md",
      description: "提示词优化器 - 帮助优化和澄清用户提示词"
    },
    {
      name: "decision-tree",
      path: "./.claude/commands/decision-tree.md",
      description: "决策树文档生成器 - 创建配置手册、QA清单、故障排查指南"
    }
  ]
}
