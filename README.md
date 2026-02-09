# 智能论文阅读助手 (Intelligent Paper Reading Assistant) 📚

> 基于 AI 的智能阅读助手，支持 PDF、网页、视频等多种内容，自动提取摘要、回答问题并整理知识到 Obsidian。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 核心特性

- 📄 **多格式支持** - 支持 PDF 文档、 **YouTube 视频**、**网页链接**、图片等多种内容源
- 🤖 **多 AI 服务支持** - 支持 OpenAI、Claude、百度千帆、Ollama 等多种模型
- 💬 **交互式问答** - 针对内容进行深度提问，支持连续追问
- 🌲 **对话树视图** - 独创的树形对话管理，清晰展示思维脉络
- 🎨 **精美终端界面** - 基于 Rich 库的现代化 CLI 界面，支持 Markdown 渲染
- 🧠 **智能知识归类** - AI 自动分析内容，将其归档到 Obsidian 库中最合适的位置
- 🔧 **零配置启动** - 自动检测 Chrome 和 Obsidian 路径，开箱即用

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-repo/read.git
cd read

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 (可选)

程序首次运行会自动通过 `setup_helper.py` 引导配置，或者你可以手动创建 `config.yaml`。

```bash
# 运行配置向导
python setup_helper.py
```

### 3. 启动程序

```bash
python main.py
```

**macOS 用户注意：**
首次运行时，程序会请求 **辅助功能 (Accessibility)** 权限。这是为了支持交互式对话树的键盘导航（方向键控制）。
- 如果看到权限提示，请前往 `系统设置 -> 隐私与安全性 -> 辅助功能`，启用你的终端（如 Terminal, iTerm2）或 Python。
- 如果不授予权限，程序仍可运行，但对话树交互体验会受限。


## 📖 使用指南

### 1. 加载内容

程序启动后，你可以输入本地文件路径或网络链接：

```bash
📎 请输入内容来源
   支持: 📄 PDF/文档 │ 🖼️  图片 │ 🎬 视频 │ 🔗 YouTube/网页链接
❯ 路径或URL: https://www.youtube.com/watch?v=example
```

- **PDF/文档**: 自动上传并分析
- **YouTube/网页**: 自动抓取内容并作为上下文

### 2. 交互式问答

内容加载后，你可以：

- **提问**: 输入 `q: 你的问题` 添加到队列
- **执行**: 输入 `run` 开始批量获取回答
- **追问**: 在回答后选择 `[f]ollow` 进行深入追问

### 3. 对话树视图 (Tree View)

输入 `tree` 进入全屏交互模式，浏览历史对话：

```bash
🌳 对话树
├── 📝 视频摘要
│   ├── 💬 核心观点
│   └── 💬 举例说明
└── 📝 观众评论分析
```

- **↑/↓**: 移动选择
- **←/→**: 折叠/展开
- **Enter**: 查看详情（按 Enter 返回）
- **F**: 在当前节点追问

### 4. 保存到 Obsidian

系统会根据你的 Obsidian 库结构，智能建议保存位置：

```bash
🧠 正在使用 DeepSeek 分析归类位置...
📍 建议路径: 02_Input/视频笔记/AI技术发展.md
📝 归类理由: 内容涉及AI最新进展，适合由于"视频笔记"分类
```

## 🛠️ 配置说明

### AI 服务配置

在 `config.yaml` 中配置你喜欢的 AI 服务：

#### 百度千帆 (DeepSeek)
```yaml
ai_service:
  provider: "baidu"
  baidu:
    api_key: "your-key"
    model: "deepseek-v3.2"
```

#### OpenAI / Claude / Ollama
支持标准 OpenAI 格式接口，可对接任何兼容服务（如本地 Ollama）：

```yaml
ai_service:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3"
```

## ❓ 常见问题

- **Q: Chrome 启动失败？**
  - A: 请确保 Chrome 已安装。如果端口 9222 被占用，尝试关闭正在运行的 Chrome 调试实例。程序会自动尝试连接现有实例或创建新实例。

- **Q: 为什么 YouTube 链接没有摘要？**
  - A: 请确保网络可以访问 YouTube。程序会将 URL 作为 Prompt 的一部分发送给 AI Studio，由 AI 进行解析。

- **Q: 权限提示一直出现？**
  - A: 尝试在系统设置中移除终端的权限，然后重新添加。

## 📄 许可证

MIT License
