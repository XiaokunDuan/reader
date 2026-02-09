"""
交互式对话树可视化界面
"""
from typing import List, Optional, Callable
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.markdown import Markdown
from pynput import keyboard
import time
from loguru import logger

from modules.qa_tree import QANode, QATree


console = Console()


class QATreeView:
    """交互式对话树视图"""
    
    def __init__(self, qa_tree: QATree):
        self.qa_tree = qa_tree
        self.selected_node: Optional[QANode] = None
        self.expanded_nodes: set = set()  # 展开的节点
        self.all_nodes: List[QANode] = []
        self.current_index = 0
        self.running = False
        self.action: Optional[str] = None  # 用户选择的操作
        
        self._build_node_list()
    
    def _build_node_list(self):
        """构建可选择的节点列表（展开状态下的所有可见节点）"""
        self.all_nodes = []
        
        def traverse(nodes: List[QANode], depth: int = 0):
            for node in nodes:
                self.all_nodes.append(node)
                # 如果节点展开且有子节点，递归添加
                if node in self.expanded_nodes and node.children:
                    traverse(node.children, depth + 1)
        
        traverse(self.qa_tree.roots)
        
        if self.all_nodes and not self.selected_node:
            self.selected_node = self.all_nodes[0]
            self.current_index = 0
    
    def show(self, on_followup: Callable[[QANode], None] = None):
        """
        显示交互式树形视图
        
        Args:
            on_followup: 追问回调函数，接收被选中的节点
        """
        self.running = True
        self.on_followup = on_followup
        
        # 初始展开所有根节点
        for root in self.qa_tree.roots:
            self.expanded_nodes.add(root)
        self._build_node_list()
        
        # 渲染初始界面
        self._render()
        
        # 监听键盘事件
        try:
            with keyboard.Listener(on_press=self._on_key_press) as listener:
                while self.running:
                    time.sleep(0.1)
                listener.stop()
        except Exception as e:
            if "not trusted" in str(e) or "Input event monitoring" in str(e):
                console.print()
                console.print(Panel(
                    "[bold red]权限错误：需要辅助功能权限[/bold red]\n\n"
                    "macOS 需要授予终端（或 Python）[bold]辅助功能 (Accessibility)[/bold] 权限才能监听键盘事件。\n\n"
                    "[yellow]解决方法：[/yellow]\n"
                    "1. 打开 [bold]系统设置 (System Settings)[/bold]\n"
                    "2. 进入 [bold]隐私与安全性 (Privacy & Security)[/bold] -> [bold]辅助功能 (Accessibility)[/bold]\n"
                    "3. 找到并开启您的终端应用（如 Terminal, iTerm2, VSCode）或 Python\n"
                    "4. 如果已经开启，请尝试移除并重新添加\n\n"
                    "[dim]提示：此交互式视图需要键盘监听功能。[/dim]",
                    title="⚠️ 权限提示",
                    border_style="red"
                ))
                # 简单回退：等待用户按回车退出
                input("按回车键退出视图...")
            else:
                logger.error(f"键盘监听失败: {e}")
        
        return self.action, self.selected_node
    
    def _render(self):
        """渲染树形界面"""
        console.clear()
        
        # 标题
        stats = self.qa_tree.get_stats()
        title = Panel.fit(
            f"[bold cyan]📚 对话历史树[/bold cyan]\n"
            f"[dim]总问题: {stats['total_questions']} | "
            f"追问: {stats['total_followups']} | "
            f"最大深度: {stats['max_depth']}[/dim]",
            border_style="cyan",
            box=box.DOUBLE
        )
        console.print(title)
        console.print()
        
        # 构建树
        tree = Tree("🌳 [bold magenta]对话树[/bold magenta]", guide_style="dim")
        
        for root in self.qa_tree.roots:
            self._add_node_to_tree(tree, root, is_root=True)
        
        console.print(tree)
        console.print()
        
        # 显示当前选中节点的详细信息
        if self.selected_node:
            self._show_node_details(self.selected_node)
        
        # 操作提示
        help_text = Text()
        help_text.append("↑↓ ", style="bold cyan")
        help_text.append("选择 | ", style="dim")
        help_text.append("← ", style="bold cyan")
        help_text.append("返回 | ", style="dim")
        help_text.append("→ ", style="bold cyan")
        help_text.append("展开 | ", style="dim")
        help_text.append("Enter ", style="bold cyan")
        help_text.append("查看完整 | ", style="dim")
        help_text.append("F ", style="bold cyan")
        help_text.append("追问 | ", style="dim")
        help_text.append("Q ", style="bold cyan")
        help_text.append("退出", style="dim")
        
        console.print(Panel(help_text, border_style="yellow", box=box.SIMPLE))
    
    def _add_node_to_tree(self, tree: Tree, node: QANode, is_root: bool = False):
        """递归添加节点到树"""
        # 判断是否被选中
        is_selected = (node == self.selected_node)
        is_expanded = node in self.expanded_nodes
        
        # 节点图标
        if is_root:
            icon = "📝"
        else:
            icon = "💬"
        
        if is_selected:
            icon = "👉 " + icon
        
        # 节点文本
        label = Text()
        
        # 摘要
        summary = node.summary if node.summary else node.question[:20]
        
        if is_selected:
            label.append(f"{icon} {summary}", style="bold yellow on blue")
        else:
            label.append(f"{icon} {summary}", style="green" if is_root else "cyan")
        
        # 时间
        time_str = node.timestamp.strftime("%H:%M")
        label.append(f" ({time_str})", style="dim")
        
        # 子节点数量
        if node.children:
            expand_icon = "▼" if is_expanded else "▶"
            label.append(f" {expand_icon} [{len(node.children)}]", style="yellow")
        
        # 添加到树
        branch = tree.add(label)
        
        # 如果展开，递归添加子节点
        if is_expanded and node.children:
            for child in node.children:
                self._add_node_to_tree(branch, child)
    
    def _show_node_details(self, node: QANode):
        """显示节点详细信息"""
        depth = node.get_depth()
        
        details = Text()
        details.append(f"{'  ' * depth}❓ ", style="bold")
        details.append(node.question[:80], style="cyan")
        if len(node.question) > 80:
            details.append("...", style="dim")
        
        console.print(Panel(details, title="[bold]当前选中[/bold]", border_style="green"))
    
    def _on_key_press(self, key):
        """处理键盘事件"""
        try:
            # 方向键
            if key == keyboard.Key.up:
                self._move_up()
            elif key == keyboard.Key.down:
                self._move_down()
            elif key == keyboard.Key.left:
                self._collapse_or_parent()
            elif key == keyboard.Key.right:
                self._expand()
            elif key == keyboard.Key.enter:
                self._show_full_content()
            elif hasattr(key, 'char'):
                if key.char == 'q' or key.char == 'Q':
                    self.action = "quit"
                    self.running = False
                elif key.char == 'f' or key.char == 'F':
                    self.action = "followup"
                    self.running = False
        except Exception as e:
            logger.error(f"键盘事件处理错误: {e}")
    
    def _move_up(self):
        """向上移动"""
        if self.current_index > 0:
            self.current_index -= 1
            self.selected_node = self.all_nodes[self.current_index]
            self._render()
    
    def _move_down(self):
        """向下移动"""
        if self.current_index < len(self.all_nodes) - 1:
            self.current_index += 1
            self.selected_node = self.all_nodes[self.current_index]
            self._render()
    
    def _expand(self):
        """展开节点"""
        if self.selected_node and self.selected_node.children:
            if self.selected_node not in self.expanded_nodes:
                self.expanded_nodes.add(self.selected_node)
                self._build_node_list()
                self._render()
    
    def _collapse_or_parent(self):
        """折叠节点或返回父节点"""
        if self.selected_node:
            if self.selected_node in self.expanded_nodes:
                # 如果当前节点已展开，折叠它
                self.expanded_nodes.remove(self.selected_node)
                self._build_node_list()
                self._render()
            elif self.selected_node.parent:
                # 否则跳转到父节点
                self.selected_node = self.selected_node.parent
                self.current_index = self.all_nodes.index(self.selected_node)
                self._render()
    
    def _show_full_content(self):
        """显示完整的问答内容"""
        if not self.selected_node:
            return
        
        console.clear()
        
        # 问题
        question_panel = Panel(
            Text(self.selected_node.question, style="bold cyan"),
            title="[bold]❓ 问题[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        )
        console.print(question_panel)
        console.print()
        
        # 回答（Markdown渲染）
        answer_md = Markdown(self.selected_node.answer)
        answer_panel = Panel(
            answer_md,
            title="[bold]💡 回答[/bold]",
            border_style="green",
            box=box.ROUNDED
        )
        console.print(answer_panel)
        console.print()
        
        # 元数据
        meta = Table(show_header=False, box=box.SIMPLE)
        meta.add_column("Key", style="dim")
        meta.add_column("Value", style="white")
        
        meta.add_row("时间", self.selected_node.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        meta.add_row("深度", str(self.selected_node.get_depth()))
        meta.add_row("子问题", str(len(self.selected_node.children)))
        
        console.print(meta)
        console.print()
        
        # 提示
        console.print("[dim]按任意键退出tree模式...[/dim]")
        
        # 等待按键
        try:
            input()
        except:
            pass
        
        self.running = False
    
    def _on_return_from_details(self):
        """从详情页返回"""
        self.running = False


def show_qa_tree_interactive(qa_tree: QATree, on_followup: Callable[[QANode], None] = None):
    """
    显示交互式对话树
    
    Args:
        qa_tree: 对话树
        on_followup: 追问回调函数
    
    Returns:
        tuple: (action, selected_node)
    """
    if not qa_tree.roots:
        console.print("[yellow]对话树为空，还没有任何提问记录[/yellow]")
        return None, None
    
    view = QATreeView(qa_tree)
    return view.show(on_followup=on_followup)
