# 智能论文阅读助手

一个基于AI的论文阅读助手，帮助你高效阅读论文并自动整理知识到Obsidian。

## ✨ 核心功能

- 📄 **PDF直接上传** - 无需转文本，直接上传到AI Studio
- 💬 **问题队列** - 批量提问，支持追问模式
- 🎨 **美化终端** - Rich库实现的Markdown渲染
- 🧠 **智能归类** - DeepSeek自动分析归档位置
- 📁 **自动创建文件夹** - 根据内容创建新分类
- 🖼️ **截图支持** - 手动添加论文截图到笔记

## 🚀 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/your-repo/read.git
cd read
pip install -r requirements.txt
```

### 2. 配置

复制 `config.yaml` 并编辑，填入你的配置信息：

```yaml
chrome:
  profile_name: "Default"  # 你的Chrome Profile名称
  # profile_path: "" # 可选：手动指定Chrome Profile路径
  
obsidian:
  vault_path: "/path/to/your/obsidian/vault"  # 你的Obsidian库路径
  
deepseek:
  api_key: "your-api-key"  # 你的 API Key
```

### 3. 运行

```bash
python main.py
```

## 📖 使用流程

### 启动和上传PDF

```bash
$ python main.py

╔═══════════════════════════════════════════════════════╗
║   🚀 智能论文阅读助手 v1.0                             ║
╚═══════════════════════════════════════════════════════╝

📄 请拖拽PDF文件到终端（或输入路径）：
> /path/to/paper.pdf

✅ PDF上传成功
✅ Obsidian库扫描完成
```

### 添加问题到队列

```bash
> q: Transformer的核心创新是什么？
✓ 问题已添加到队列 [1]

> run
```

### 批量处理

```bash
🚀 开始处理队列中的 1 个问题...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/1] Transformer的核心创新是什么？
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[AI回答显示，支持Markdown格式]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
操作选项：
[1] save   - 保存到Obsidian
[2] skip   - 跳过
[3] follow - 继续追问
[4] attach - 添加截图
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 保存到Obsidian

```bash
> 1  # 选择保存

🧠 正在使用DeepSeek分析归类位置...
✅ 保存成功！
```

## 🎯 命令参考

| 命令 | 说明 |
|------|------|
| `q: <问题>` | 添加问题到队列 |
| `list` | 查看当前队列 |
| `run` | 开始批量处理 |
| `clear` | 清空队列 |
| `exit` | 退出程序 |

## 📁 项目结构

```
.
├── main.py                 # 主程序入口
├── config.yaml             # 配置文件
├── requirements.txt        # Python依赖
├── modules/
│   ├── browser.py          # 浏览器控制
│   ├── cli.py              # 终端交互
│   ├── knowledge.py        # DeepSeek智能归类
│   └── obsidian.py         # Obsidian写入
├── data/                   # 数据存储
```

## 🔧 配置说明

### Chrome配置

需确保安装 Google Chrome，并启用远程调试端口（默认9222）。
启动Chrome命令示例（MacOS）：
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### DeepSeek API

需要申请 DeepSeek API Key，并填入 `config.yaml`。

### Obsidian

设置 Obsidian 仓库路径，助手会自动将笔记保存到该路径下。

## 🐛 故障排除

### Chrome无法启动

- 确认Chrome是否正在运行且开启了debug端口。
- 检查端口9222是否被占用。

### PDF上传失败

- 确认AI Studio页面已完全加载
- 手动检查上传按钮是否可见

### DeepSeek API调用失败

- 检查API Key是否正确。
- 查看网络连接。

## 📝 开发计划

- [ ] 阅读统计和报告生成
- [ ] 多PDF并行处理
- [ ] 问题模板系统
- [ ] 知识图谱可视化

## 📄 许可证

MIT License
