"""
终端交互界面模块 - Premium CLI Design
"""
import os
from typing import List, Optional, Dict
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.align import Align
from rich import box
from rich.status import Status


# ═══════════════════════════════════════════════════════════════════════════════
# 主题配色系统
# ═══════════════════════════════════════════════════════════════════════════════

THEME = {
    'primary': 'cyan',
    'secondary': 'magenta',
    'accent': 'bright_blue',
    'success': 'bright_green',
    'warning': 'bright_yellow',
    'error': 'bright_red',
    'muted': 'dim white',
    'border': 'bright_black',
    'highlight': 'bold bright_white',
}

# 渐变色配置 (用于 Banner)
GRADIENT_COLORS = [
    "#00d9ff",  # Cyan
    "#00c4ff",
    "#00afff",
    "#009aff",
    "#0085ff",
    "#6b70ff",
    "#9b5bff",
    "#c846ff",
    "#f531ff",  # Magenta
]


class CLI:
    """命令行交互界面 - Premium Edition"""
    
    def __init__(self):
        self.console = Console()
        self.question_queue: List[str] = []
        self.current_qa: Optional[Dict] = None
        self.attachments: List[str] = []
        self.current_paper_title: Optional[str] = None
    
    def _gradient_text(self, text: str, colors: list = None) -> Text:
        """创建渐变色文本"""
        if colors is None:
            colors = GRADIENT_COLORS
        
        result = Text()
        text_len = len(text)
        
        for i, char in enumerate(text):
            # 计算当前位置对应的颜色索引
            color_idx = int(i / text_len * (len(colors) - 1))
            result.append(char, style=Style(color=colors[color_idx]))
        
        return result
    
    def show_banner(self):
        """显示高级启动横幅"""
        # ASCII Art "READER"
        ascii_art = """
 ██████╗  ███████╗  █████╗  ██████╗  ███████╗ ██████╗ 
 ██╔══██╗ ██╔════╝ ██╔══██╗ ██╔══██╗ ██╔════╝ ██╔══██╗
 ██████╔╝ █████╗   ███████║ ██║  ██║ █████╗   ██████╔╝
 ██╔══██╗ ██╔══╝   ██╔══██║ ██║  ██║ ██╔══╝   ██╔══██╗
 ██║  ██║ ███████╗ ██║  ██║ ██████╔╝ ███████╗ ██║  ██║
 ╚═╝  ╚═╝ ╚══════╝ ╚═╝  ╚═╝ ╚═════╝  ╚══════╝ ╚═╝  ╚═╝
        """.strip()
        
        # 为 ASCII Art 添加渐变
        lines = ascii_art.split('\n')
        gradient_art = Text()
        for line in lines:
            gradient_art.append_text(self._gradient_text(line))
            gradient_art.append('\n')
        
        # 副标题
        subtitle = Text()
        subtitle.append("🚀 ", style="bold")
        subtitle.append("智能论文阅读助手", style=f"bold {THEME['primary']}")
        subtitle.append("  •  ", style=THEME['muted'])
        subtitle.append("v1.0", style=THEME['muted'])
        subtitle.append("\n")
        subtitle.append("Intelligent Paper Reading Assistant", style=THEME['muted'])
        
        # 组合内容
        content = Group(
            Align.center(gradient_art),
            Text(),  # 空行
            Align.center(subtitle),
        )
        
        # 创建外框 Panel
        panel = Panel(
            content,
            box=box.ROUNDED,
            border_style=THEME['border'],
            padding=(1, 4),
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def prompt_pdf_path(self) -> str:
        """提示用户输入PDF路径（向后兼容）"""
        return self.prompt_input_path()
    
    def prompt_input_path(self) -> str:
        """提示用户输入文件路径或URL"""
        self.console.print()
        prompt_text = Text()
        prompt_text.append("📎 ", style="bold")
        prompt_text.append("请输入内容来源", style=f"bold {THEME['primary']}")
        self.console.print(prompt_text)
        
        # 支持的类型提示
        types_hint = Text()
        types_hint.append("   支持: ", style=THEME['muted'])
        types_hint.append("📄 PDF/文档 ", style=THEME['muted'])
        types_hint.append("│ ", style=THEME['border'])
        types_hint.append("🖼️  图片 ", style=THEME['muted'])
        types_hint.append("│ ", style=THEME['border'])
        types_hint.append("🎬 视频 ", style=THEME['muted'])
        types_hint.append("│ ", style=THEME['border'])
        types_hint.append("🔗 YouTube/网页链接", style=THEME['muted'])
        self.console.print(types_hint)
        
        input_path = Prompt.ask(f"[{THEME['secondary']}]❯[/] 路径或URL").strip()
        
        # 处理拖拽文件时可能带的引号
        input_path = input_path.strip("'\"")
        
        return input_path
    
    def add_question(self, question: str):
        """添加问题到队列"""
        self.question_queue.append(question)
        self.console.print(
            f"[{THEME['success']}]✓[/] 问题已添加  [{THEME['muted']}]队列: {len(self.question_queue)}[/]"
        )
    
    def show_queue(self):
        """显示当前问题队列"""
        if not self.question_queue:
            self.console.print(f"[{THEME['muted']}]队列为空[/]")
            return
        
        table = Table(
            title="[bold]当前问题队列[/]",
            box=box.ROUNDED,
            border_style=THEME['border'],
            title_style=THEME['primary'],
            header_style=f"bold {THEME['primary']}",
        )
        table.add_column("#", style=THEME['muted'], width=4, justify="right")
        table.add_column("问题", style="white")
        
        for i, q in enumerate(self.question_queue, 1):
            display_q = q[:70] + "..." if len(q) > 70 else q
            table.add_row(str(i), display_q)
        
        self.console.print(table)
    
    def clear_queue(self):
        """清空问题队列"""
        self.question_queue = []
        self.console.print(f"[{THEME['success']}]✓[/] 队列已清空")
    
    def show_answer(self, question: str, answer: str, index: int = 1, total: int = 1):
        """显示问答对 - 改进的视觉效果"""
        self.console.print()
        
        # 问题标题栏
        header = Text()
        header.append(f" {index}/{total} ", style=f"bold black on {THEME['primary']}")
        header.append(" ", style="")
        header.append(question, style=f"bold {THEME['highlight']}")
        
        self.console.print(header)
        self.console.print(f"[{THEME['border']}]{'─' * min(80, self.console.width - 4)}[/]")
        self.console.print()
        
        # 使用 Rich 的 Markdown 渲染答案
        md = Markdown(answer)
        self.console.print(md)
        self.console.print()
    
    def show_options(self, enable_follow: bool = True) -> str:
        """显示操作选项 - 现代化 inline 菜单"""
        self.console.print(f"[{THEME['border']}]{'─' * min(80, self.console.width - 4)}[/]")
        
        # 构建 inline 选项
        options = Text()
        options.append("  ")
        
        opt_list = [
            ("s", "save", "保存"),
            ("n", "next", "下一个"),
        ]
        if enable_follow:
            opt_list.insert(1, ("f", "follow", "追问"))
        opt_list.extend([
            ("a", "attach", "截图"),
            ("x", "skip", "跳过"),
        ])
        
        for i, (key, _, label) in enumerate(opt_list):
            if i > 0:
                options.append("  │  ", style=THEME['border'])
            options.append(f"[{key}]", style=f"bold {THEME['secondary']}")
            options.append(f" {label}", style=THEME['muted'])
        
        self.console.print(options)
        self.console.print()
        
        choice = Prompt.ask(
            f"[{THEME['secondary']}]❯[/] 选择",
            choices=["s", "f", "n", "a", "x"],
            default="n"
        )
        
        choice_map = {
            "s": "save",
            "n": "next",
            "f": "follow",
            "a": "attach",
            "x": "skip",
        }
        
        return choice_map.get(choice, "next")
    
    def prompt_follow_up(self) -> Optional[str]:
        """提示用户输入追问"""
        self.console.print()
        self.console.print(
            f"[{THEME['secondary']}]💬 追问模式[/]  "
            f"[{THEME['muted']}]输入问题，或输入 'done' 结束[/]"
        )
        
        follow_up = Prompt.ask(f"[{THEME['secondary']}]❯[/] 追问").strip()
        
        if follow_up.lower() == 'done':
            return None
        
        return follow_up
    
    def prompt_attachment(self) -> Optional[str]:
        """提示用户添加截图"""
        self.console.print()
        self.console.print(
            f"[{THEME['primary']}]📸 添加截图[/]  "
            f"[{THEME['muted']}]拖拽文件或输入路径，'cancel' 取消[/]"
        )
        
        path = Prompt.ask(f"[{THEME['secondary']}]❯[/] 路径").strip()
        
        if path.lower() == 'cancel':
            return None
        
        path = path.strip("'\"")
        
        if os.path.exists(path):
            self.attachments.append(path)
            self.console.print(
                f"[{THEME['success']}]✓[/] 已添加: [{THEME['muted']}]{os.path.basename(path)}[/]"
            )
            return path
        else:
            self.console.print(f"[{THEME['error']}]✗[/] 文件不存在")
            return None
    
    def show_classification_result(self, result: dict):
        """显示 DeepSeek 的归类结果"""
        panel_content = Text()
        panel_content.append("目标路径\n", style=f"bold {THEME['primary']}")
        panel_content.append(f"{result['target_path']}\n\n", style="white")
        
        panel_content.append("归类理由\n", style=f"bold {THEME['primary']}")
        panel_content.append(f"{result['reasoning']}\n\n", style=THEME['muted'])
        
        if result.get('tags'):
            panel_content.append("标签  ", style=f"bold {THEME['primary']}")
            for tag in result['tags']:
                panel_content.append(f"#{tag} ", style=THEME['secondary'])
        
        if result.get('is_new_folder'):
            panel_content.append(f"\n\n[{THEME['warning']}]⚠ 将创建新文件夹[/]")
        
        panel = Panel(
            panel_content,
            title=f"[bold {THEME['success']}]🧠 归类分析[/]",
            box=box.ROUNDED,
            border_style=THEME['success'],
            padding=(1, 2),
        )
        
        self.console.print()
        self.console.print(panel)
    
    def confirm_save(self) -> bool:
        """确认是否保存"""
        return Confirm.ask(f"[{THEME['secondary']}]确认保存？[/]", default=True)
    
    def show_success(self, message: str):
        """显示成功消息"""
        self.console.print(f"[{THEME['success']}]✓[/] {message}")
    
    def show_error(self, message: str):
        """显示错误消息"""
        self.console.print(f"[{THEME['error']}]✗[/] {message}")
    
    def show_warning(self, message: str):
        """显示警告消息"""
        self.console.print(f"[{THEME['warning']}]![/] {message}")
    
    def show_info(self, message: str):
        """显示信息消息"""
        self.console.print(f"[{THEME['muted']}]›[/] {message}")
    
    def show_progress(self, message: str):
        """显示进度消息 (静态版本，用于非 context manager 场景)"""
        self.console.print(f"[{THEME['primary']}]⟳[/] {message}")
    
    def status(self, message: str) -> Status:
        """返回一个 Status context manager，用于显示 spinner 动画"""
        return self.console.status(
            f"[{THEME['primary']}]{message}[/]",
            spinner="dots",
            spinner_style=THEME['secondary']
        )
    
    def show_template_list(self, templates: list):
        """显示模板列表"""
        from rich.table import Table
        
        table = Table(
            title="[bold]📋 问题模板[/]",
            box=box.ROUNDED,
            border_style=THEME['border'],
            title_style=THEME['primary'],
            header_style=f"bold {THEME['primary']}",
        )
        table.add_column("名称", style=THEME['secondary'], width=20)
        table.add_column("描述", style="white", width=40)
        table.add_column("分类", style=THEME['muted'], width=10)
        table.add_column("问题数", style=THEME['accent'], width=8, justify="center")
        
        for template in templates:
            table.add_row(
                template.name,
                template.description[:40] + "..." if len(template.description) > 40 else template.description,
                template.category,
                str(len(template.questions))
            )
        
        self.console.print("\n")
        self.console.print(table)
        self.console.print(f"\n[{THEME['muted']}]使用示例: template use paper_reading[/]")
        self.console.print(f"[{THEME['muted']}]创建模板: template create[/]")
    
    def interactive_mode(self) -> str:
        """交互式命令输入模式"""
        self.console.print()
        
        # 构建提示符
        prompt_parts = []
        if self.current_paper_title:
            # 显示缩短的论文标题
            short_title = self.current_paper_title[:30] + "..." if len(self.current_paper_title) > 30 else self.current_paper_title
            prompt_parts.append(f"[{THEME['muted']}]{short_title}[/]")
        
        prompt = f"[bold {THEME['secondary']}]❯[/]"
        
        cmd = Prompt.ask(prompt).strip()
        return cmd
    
    def parse_command(self, cmd: str) -> tuple:
        """解析用户命令"""
        if cmd.startswith("q:"):
            return ("add_question", cmd[2:].strip())
        elif cmd.startswith("follow:"):
            return ("follow", cmd[7:].strip())
        elif cmd.startswith("attach "):
            return ("attach", cmd[7:].strip())
        elif cmd.startswith("edit "):
            return ("edit", cmd[5:].strip())
        elif cmd.startswith("remove "):
            return ("remove", cmd[7:].strip())
        elif cmd.startswith("template "):
            return ("template", cmd[9:].strip())
        elif cmd == "template":
            return ("template", "list")
        elif cmd.startswith("upload "):
            return ("upload", cmd[7:].strip())
        elif cmd == "upload":
            return ("upload", None)
        elif cmd == "list":
            return ("list", None)
        elif cmd == "run":
            return ("run", None)
        elif cmd == "clear":
            return ("clear", None)
        elif cmd == "tree":
            return ("tree", None)
        elif cmd == "stats":
            return ("stats", None)
        elif cmd in ["exit", "quit"]:
            return ("exit", None)
        elif cmd == "help" or cmd == "?":
            return ("help", None)
        else:
            return ("unknown", cmd)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = Text()
        help_text.append("\n可用命令:\n\n", style=f"bold {THEME['primary']}")
        
        commands = [
            ("q: <问题>", "添加问题到队列"),
            ("list", "查看问题队列"),
            ("run", "执行队列中的问题"),
            ("upload", "更换/上传内容 (支持URL)"),
            ("tree", "查看对话历史树"),
            ("template", "模板管理 (list/use/create)"),
            ("clear", "清空问题队列"),
            ("exit", "退出程序"),
        ]
        
        for cmd, desc in commands:
            help_text.append(f"  {cmd:15}", style=THEME['secondary'])
            help_text.append(f"  {desc}\n", style=THEME['muted'])
        
        self.console.print(help_text)
