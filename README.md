# Reader

AI-assisted reading workspace for long-form content.

Reader turns papers, PDFs, web pages, videos, and images into an interactive reading session with structured Q&A, tree-based follow-up, and Obsidian-ready notes.

## Why this project exists

Most reading tools stop at highlighting or summarizing. Reader is built for a different workflow:

- load one piece of content
- ask layered questions
- keep the reasoning path
- export the result into a knowledge base instead of losing it in chat history

It is especially useful for paper reading, research digestion, dense web articles, and video-based learning.

## Key capabilities

- Multi-source ingestion for PDFs, local documents, images, web URLs, and YouTube links
- AI-backed summarization and iterative Q&A across the loaded content
- Tree view for branching follow-up questions instead of a flat chat log
- Obsidian integration with AI-assisted note placement
- Rich-powered terminal interface for readable long-form output
- Setup helper for bootstrapping Chrome, Obsidian, and model configuration

## Quick start

### Requirements

- Python 3.10+
- macOS recommended for the current interactive workflow
- Google Chrome
- Obsidian

### Install

```bash
git clone https://github.com/XiaokunDuan/reader.git
cd reader
pip install -r requirements.txt
```

### Configure

Use the setup wizard:

```bash
python setup_helper.py
```

Or copy the example config and edit it manually:

```bash
cp config.example.yaml config.yaml
```

### Run

```bash
python main.py
```

## Workflow

1. Start the app and load a local file or URL.
2. Let Reader generate the first summary.
3. Ask follow-up questions in sequence or branch them in tree view.
4. Save the final result to the right location in your Obsidian vault.

## Supported model backends

Reader supports multiple providers through its configuration layer:

- Baidu Qianfan / DeepSeek
- OpenAI-compatible APIs
- Anthropic Claude
- Ollama

## Project structure

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

## Notes

- On macOS, the interactive tree view may request Accessibility permission for keyboard navigation.
- Chrome remote debugging is part of the current flow; the setup wizard helps detect the required profile.
- This project is optimized for a single-user local workflow rather than multi-user deployment.

## Documentation

- Chinese README: [README.zh-CN.md](./README.zh-CN.md)

## License

MIT
