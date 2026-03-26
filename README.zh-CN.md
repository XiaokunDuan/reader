# Reader

面向长内容阅读的 AI 辅助工作台。

Reader 把论文、PDF、网页、视频、图片这些内容源，变成一个可持续追问、可保留思路分支、可沉淀到 Obsidian 的阅读流程。

## 为什么做这个项目

很多阅读工具只能做高亮、摘要或者一次性问答。Reader 想解决的是另一类问题：

- 读完以后如何继续追问
- 追问路径怎么保留下来
- 结论怎么进入知识库，而不是散落在聊天记录里

它更适合论文阅读、研究资料消化、长网页精读、视频学习等场景。

## 核心能力

- 支持 PDF、本地文档、图片、网页链接、YouTube 链接等多种输入
- 基于 AI 做摘要、问答和连续追问
- 用对话树保存问题分支，而不是只有线性聊天记录
- 支持 Obsidian 集成，并用 AI 辅助判断笔记归档位置
- 基于 Rich 的终端界面，更适合长文本阅读
- 提供配置向导，自动处理 Chrome、Obsidian 和模型配置

## 快速开始

### 环境要求

- Python 3.10+
- 当前交互流程更适合 macOS
- Google Chrome
- Obsidian

### 安装

```bash
git clone https://github.com/XiaokunDuan/reader.git
cd reader
pip install -r requirements.txt
```

### 配置

推荐先运行配置向导：

```bash
python setup_helper.py
```

也可以手动复制配置文件：

```bash
cp config.example.yaml config.yaml
```

### 启动

```bash
python main.py
```

## 使用流程

1. 启动程序，输入本地文件路径或 URL。
2. 先生成初始摘要。
3. 继续提问，或进入树状视图做分支追问。
4. 最终将结果保存到 Obsidian。

## 支持的模型后端

通过配置层支持多种模型服务：

- 百度千帆 / DeepSeek
- OpenAI 兼容接口
- Anthropic Claude
- Ollama

## 项目结构

```text
reader/
├── main.py
├── setup_helper.py
├── config.example.yaml
├── modules/
│   ├── ai_adapter.py
│   ├── browser.py
│   ├── cli.py
│   ├── knowledge.py
│   ├── obsidian.py
│   ├── qa_tree.py
│   ├── qa_tree_view.py
│   ├── statistics.py
│   └── templates.py
├── templates/
└── data/
```

## 说明

- macOS 下的树状交互可能会请求辅助功能权限，用于键盘导航。
- 当前流程依赖 Chrome 远程调试，配置向导会帮你自动检测相关设置。
- 这个项目更偏个人本地阅读工作流，不是多用户 SaaS。

## 文档

- English README: [README.md](./README.md)

## License

MIT
