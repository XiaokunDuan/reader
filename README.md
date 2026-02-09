# 智能论文阅读助手 📚

> 基于AI的智能论文助手，帮助你高效阅读论文并自动整理知识到Obsidian

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 核心特性

- 📄 **PDF直接上传** - 无需转文本，直接上传到AI Studio
- 🤖 **多AI服务支持** - 支持OpenAI、Claude、百度千帆、Ollama等
- 💬 **智能问答** - 批量提问，支持追问，可自定义初始问题
- 🎨 **美化终端** - Rich库实现的Markdown渲染
- 🧠 **智能归类** - AI自动分析归档位置
- 📁 **自动创建文件夹** - 根据内容创建新分类
- 🖼️ **截图支持** - 手动添加论文截图到笔记
- 🔧 **配置向导** - 自动检测Chrome和Obsidian路径

## 🚀 快速开始

### 方式一：使用配置向导（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/read.git
cd read

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行配置向导（自动检测路径并生成配置）
python setup_helper.py

# 4. 启动程序
python main.py
```

### 方式二：手动配置

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/read.git
cd read

# 2. 安装依赖
pip install -r requirements.txt

# 3. 复制配置模板
cp config.example.yaml config.yaml

# 4. 编辑 config.yaml（参考下方配置指南）
vim config.yaml

# 5. 启动程序
python main.py
```

## 📋 配置指南

### 🔍 自动检测路径

不知道Chrome Profile路径？运行这些命令：

**macOS:**
```bash
# 查看Chrome Profiles
ls ~/Library/Application\ Support/Google/Chrome/

# 查找Obsidian Vaults
find ~ -name ".obsidian" -type d 2>/dev/null
```

**Linux:**
```bash
# 查看Chrome Profiles
ls ~/.config/google-chrome/

# 查找Obsidian Vaults
find ~ -name ".obsidian" -type d 2>/dev/null
```

**Windows (PowerShell):**
```powershell
# 查看Chrome Profiles
dir "$env:LOCALAPPDATA\Google\Chrome\User Data"

# 查找Obsidian Vaults
Get-ChildItem -Path $env:USERPROFILE -Filter ".obsidian" -Recurse -Directory -ErrorAction SilentlyContinue
```

### 🤖 AI服务配置

项目支持多种AI服务，在`config.yaml`中配置：

#### 1️⃣ 百度千帆 (DeepSeek)

```yaml
ai_service:
  provider: "baidu"
  baidu:
    base_url: "https://qianfan.baidubce.com/v2"
    api_key: "your-api-key-here"  # 👈 在千帆平台申请
    model: "deepseek-v3.2"
```

🔗 [申请百度千帆API](https://console.bce.baidu.com/qianfan/overview)

#### 2️⃣ OpenAI (GPT-4)

```yaml
ai_service:
  provider: "openai"
  openai:
    api_key: "sk-..."  # 👈 OpenAI API Key
    model: "gpt-4"
    base_url: "https://api.openai.com/v1"  # 兼容API可修改
```

🔗 [申请OpenAI API Key](https://platform.openai.com/api-keys)

#### 3️⃣ Anthropic Claude

```yaml
ai_service:
  provider: "claude"
  claude:
    api_key: "sk-ant-..."  # 👈 Claude API Key
    model: "claude-3-5-sonnet-20241022"
```

🔗 [申请Claude API Key](https://console.anthropic.com/)

#### 4️⃣ Ollama (本地LLM)

```bash
# 先安装并启动Ollama
brew install ollama  # macOS
ollama serve

# 拉取模型
ollama pull llama3
```

```yaml
ai_service:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3"
```

🔗 [Ollama官网](https://ollama.com/)

### 📌 自定义初始问题

PDF上传后可以自动提问，帮助快速了解论文：

```yaml
initial_questions:
  enabled: true
  questions:
    - "这篇论文讲了什么"
    - "这篇论文的核心创新点是什么"
    - "这篇论文使用了什么方法"
    - "这篇论文的实验结果如何"
```

**提示：** 可以注释掉不需要的问题，或添加自己的问题。

### 完整配置示例

查看 [config.example.yaml](config.example.yaml) 了解所有配置选项。

## 📖 使用流程

### 1. 启动并上传PDF

```bash
$ python main.py

╔═══════════════════════════════════════════════════════╗
║   🚀 智能论文阅读助手 v2.0                             ║
╚═══════════════════════════════════════════════════════╝

✅ Chrome 已启动，AI Studio 已就绪

📄 请拖拽PDF文件到终端（或输入路径）：
> /path/to/paper.pdf

✅ PDF上传成功
🔄 正在生成论文摘要...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 问题：这篇论文讲了什么

[AI回答，Markdown格式渲染]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 已索引 1,234 个笔记
```

### 2. 添加问题到队列

```bash
> q: Transformer的核心创新是什么？
✓ 问题已添加到队列 [1]

> q: Multi-Head Attention的工作原理
✓ 问题已添加到队列 [2]

> list
📋 当前队列 (2个问题):
 1. Transformer的核心创新是什么？
 2. Multi-Head Attention的工作原理

> run
🚀 开始处理队列...
```

### 3. 查看对话历史树 🆕

强大的交互式对话树，让你一目了然地看到所有提问和追问的层级关系：

```bash
> tree

╔══════════════════════════════════════════════════════════╗
║          📚 对话历史树                                    ║
║  总问题: 8 | 追问: 5 | 最大深度: 3                       ║
╚══════════════════════════════════════════════════════════╝

🌳 对话树
├── 👉 📝 论文主题 (11:30)  ▼ [2]
│   ├── 💬 核心创新 (11:32)
│   └── 💬 实验数据集 (11:35)  ▼ [1]
│       └── 💬 数据规模 (11:37)
├── 📝 方法论 (11:40)  ▼ [2]
│   ├── 💬 模型架构 (11:42)
│   └── 💬 训练策略 (11:45)
└── 📝 性能对比 (11:48)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
当前选中：
  ❓ 这篇论文讲了什么
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

↑↓ 选择 | ← 返回 | → 展开 | Enter 查看 | F 追问 | Q 退出
```

**树形导航操作：**
- **↑↓** 上下箭头：在节点间移动选择
- **←** 左箭头：折叠节点或返回父节点
- **→** 右箭头：展开子节点
- **Enter** 回车：查看完整问答内容
- **F** 键：在选中节点追问
- **Q** 键：退出树形视图

**在树中追问：**
```bash
# 按 F 键进入追问模式
> F

在节点 [核心创新] 追问
💬 追问模式  输入问题，或输入 'done' 结束
❯ 与BERT的区别是什么

[AI回答]
✓ 追问已添加到对话树
```

每个问答自动生成AI摘要，历史记录自动保存到 `data/qa_tree_{论文名}.json`

### 4. 保存到Obsidian

```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
操作选项：
[1] save   - 保存到Obsidian
[2] skip   - 跳过
[3] follow - 继续追问
[4] attach - 添加截图
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

> 1

🧠 正在使用AI分析归类位置...

📍 建议路径: 10_人工智能与科学/深度学习/Transformer.md
📝 归类理由: 内容涉及Transformer架构，属于深度学习领域
🔗 相关笔记: [BERT.md] [Attention机制.md]
🏷️  标签: #论文笔记 #深度学习 #Transformer

确认保存？[Y/n] y

✅ 保存成功！
📍 /path/to/obsidian/10_人工智能与科学/深度学习/Transformer.md
```

## 🎯 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `q: <问题>` | 添加问题到队列 | `q: 这篇论文的创新点是什么` |
| `list` | 查看当前队列 | `list` |
| `run` | 开始批量处理 | `run` |
| `tree` 🆕 | 查看对话历史树（交互式） | `tree` |
| `clear` | 清空队列 | `clear` |
| `s` 或 `save` | 保存当前回答 | `s` |
| `help` 或 `?` | 显示帮助 | `help` |
| `exit` | 退出程序 | `exit` |

### Tree命令说明

进入对话树后的键盘操作：

| 按键 | 功能 |
|------|------|
| `↑` `↓` | 上下移动选择节点 |
| `←` | 折叠节点 / 返回父节点 |
| `→` | 展开子节点 |
| `Enter` | 查看完整问答内容 |
| `F` | 在选中节点追问 |
| `Q` | 退出树形视图 |

## 🛠️ 辅助工具

### 📊 项目结构可视化

```bash
# 查看项目结构（精美的终端树形图）
python tree_view.py

# 指定目录和深度
python tree_view.py /path/to/dir --depth 4
```

**效果预览：**

```
📊 项目结构可视化
────────────────────────────────────────

📁 read/
├── 🐍 main.py (11.2KB)
├── ⚙️ config.yaml (1.2KB)
├── ⚙️ config.example.yaml (3.5KB)
├── 📦 modules/
│   ├── 🐍 browser.py (15.6KB)
│   ├── 🐍 cli.py (14.3KB)
│   ├── 🐍 knowledge.py (6.1KB)
│   ├── 🐍 obsidian.py (7.3KB)
│   └── 🐍 ai_adapter.py (5.8KB)
├── 💾 data/
├── 📜 logs/
└── 📝 README.md (12.4KB)

📦 统计信息: 8 个目录, 23 个文件, 总大小: 98.7KB
```

### 🔧 配置向导

```bash
python setup_helper.py
```

**功能：**
- ✅ 自动检测Chrome Profiles
- ✅ 自动查找Obsidian Vaults
- ✅ 交互式AI服务配置
- ✅ 自定义初始问题
- ✅ 生成完整的`config.yaml`

## 📁 项目结构

```
.
├── main.py                 # 主程序入口
├── setup_helper.py         # 🆕 配置向导工具
├── tree_view.py            # 🆕 项目结构可视化
├── config.yaml             # 配置文件（需自行创建）
├── config.example.yaml     # 配置模板
├── requirements.txt        # Python依赖
├── modules/
│   ├── browser.py          # 浏览器控制
│   ├── cli.py              # 终端交互
│   ├── knowledge.py        # AI智能归类
│   ├── obsidian.py         # Obsidian写入
│   └── ai_adapter.py       # 🆕 AI服务适配器
├── data/                   # 数据存储
└── logs/                   # 日志文件
```

## � 故障排除

### Chrome无法启动

**问题：** Chrome启动失败或无法连接

**解决方案：**
```bash
# 1. 确认Chrome正在运行
ps aux | grep Chrome

# 2. 手动启动Chrome（开启调试端口）
# macOS:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux:
google-chrome --remote-debugging-port=9222

# Windows:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# 3. 检查端口是否被占用
lsof -i :9222  # macOS/Linux
netstat -ano | findstr :9222  # Windows
```

### PDF上传失败

**问题：** PDF无法上传到AI Studio

**解决方案：**
1. 确认AI Studio页面已完全加载（等待5-10秒）
2. 检查PDF文件大小（建议<100MB）
3. 尝试手动在浏览器中上传一次
4. 检查网络连接

### AI API调用失败

**问题：** AI服务返回错误或超时

**解决方案：**

**百度千帆：**
```bash
# 测试API连接
curl -X POST "https://qianfan.baidubce.com/v2/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v3.2","messages":[{"role":"user","content":"hi"}]}'
```

**OpenAI：**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Ollama：**
```bash
# 确认服务运行
curl http://localhost:11434/api/tags

# 重启服务
ollama serve
```

### Obsidian路径错误

**问题：** 找不到Obsidian Vault

**解决方案：**
```bash
# 查找所有Obsidian Vaults
find ~ -name ".obsidian" -type d 2>/dev/null

# 确认路径是Vault根目录（包含.obsidian文件夹）
ls /path/to/vault/.obsidian
```

## ❓ 常见问题 (FAQ)

### 如何切换AI服务？

编辑`config.yaml`，修改`ai_service.provider`：

```yaml
ai_service:
  provider: "openai"  # 改为 baidu | openai | claude | ollama
```

### 如何禁用自动提问？

```yaml
initial_questions:
  enabled: false  # 改为false
```

### 如何自定义归档位置？

AI会根据你的Obsidian库结构自动建议位置。你也可以：
1. 在保存时手动修改路径
2. 通过调整Vault结构来引导AI的建议

### 支持哪些语言？

- 界面：中文
- 论文：支持任何语言（取决于AI服务）
- 问题：支持中英文混合

### 如何批量处理多个PDF？

目前需要逐个处理。未来版本会支持批量处理功能。

### 数据安全吗？

- PDF只上传到Google AI Studio（你的账号）
- 问答内容会发送到配置的AI服务
- 本地不保存敏感数据
- 支持本地LLM（Ollama）以完全离线运行

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 致谢

- [Rich](https://github.com/Textualize/rich) - 美化终端输出
- [SeleniumBase](https://github.com/seleniumbase/SeleniumBase) - 浏览器自动化
- [Loguru](https://github.com/Delgan/loguru) - 优雅的日志系统
