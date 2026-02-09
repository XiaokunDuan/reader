#!/usr/bin/env python3
"""
项目结构树形可视化工具 - 精美的终端展示
"""
import os
from pathlib import Path
from typing import List
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich import box
from rich.text import Text

console = Console()


class ProjectTreeView:
    """项目树形可视化"""
    
    # 忽略的目录和文件
    IGNORE_PATTERNS = {
        '.git', '__pycache__', '.pytest_cache', 'node_modules',
        '.venv', 'venv', 'env', '.env', '.DS_Store',
        '*.pyc', '.idea', '.vscode', '.gemini', '.claude'
    }
    
    # 文件类型图标映射
    FILE_ICONS = {
        '.py': '🐍',
        '.md': '📝',
        '.yaml': '⚙️',
        '.yml': '⚙️',
        '.json': '📋',
        '.txt': '📄',
        '.log': '📜',
        '.sh': '⚡',
        '.jpg': '🖼️',
        '.png': '🖼️',
        '.pdf': '📕',
    }
    
    # 目录特殊图标
    DIR_ICONS = {
        'modules': '📦',
        'data': '💾',
        'logs': '📜',
        'tests': '🧪',
        'docs': '📚',
        'scripts': '⚡',
        'downloaded_files': '📥',
    }
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.file_count = 0
        self.dir_count = 0
        self.total_size = 0
    
    def should_ignore(self, path: Path) -> bool:
        """判断是否应该忽略"""
        name = path.name
        
        # 检查精确匹配
        if name in self.IGNORE_PATTERNS:
            return True
        
        # 检查通配符模式
        for pattern in self.IGNORE_PATTERNS:
            if '*' in pattern:
                ext = pattern.replace('*', '')
                if name.endswith(ext):
                    return True
        
        return False
    
    def get_file_icon(self, path: Path) -> str:
        """获取文件图标"""
        if path.is_dir():
            return self.DIR_ICONS.get(path.name, '📁')
        else:
            ext = path.suffix.lower()
            return self.FILE_ICONS.get(ext, '📄')
    
    def get_size_str(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def add_tree_node(self, tree: Tree, path: Path, max_depth: int = 3, current_depth: int = 0):
        """递归添加树节点"""
        if current_depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return
        
        for item in items:
            # 跳过忽略的文件/目录
            if self.should_ignore(item):
                continue
            
            # 获取图标
            icon = self.get_file_icon(item)
            
            if item.is_dir():
                # 目录
                self.dir_count += 1
                
                # 计算目录下的文件数
                try:
                    item_count = len([x for x in item.rglob('*') if not self.should_ignore(x)])
                    label = Text()
                    label.append(f"{icon} ", style="bold")
                    label.append(f"{item.name}/", style="bold cyan")
                    label.append(f" ({item_count} items)", style="dim")
                except:
                    label = Text()
                    label.append(f"{icon} ", style="bold")
                    label.append(f"{item.name}/", style="bold cyan")
                
                branch = tree.add(label)
                self.add_tree_node(branch, item, max_depth, current_depth + 1)
            else:
                # 文件
                self.file_count += 1
                
                try:
                    size = item.stat().st_size
                    self.total_size += size
                    size_str = self.get_size_str(size)
                    
                    label = Text()
                    label.append(f"{icon} ", style="bold")
                    label.append(item.name, style="green")
                    label.append(f" ({size_str})", style="dim yellow")
                except:
                    label = Text()
                    label.append(f"{icon} ", style="bold")
                    label.append(item.name, style="green")
                
                tree.add(label)
    
    def show(self, max_depth: int = 3):
        """显示项目树"""
        console.clear()
        
        # 标题
        title_panel = Panel.fit(
            "[bold cyan]📊 项目结构可视化[/bold cyan]\n"
            f"[dim]{self.root_path}[/dim]",
            border_style="cyan",
            box=box.DOUBLE
        )
        console.print(title_panel)
        console.print()
        
        # 创建树
        icon = self.get_file_icon(self.root_path)
        tree = Tree(
            f"{icon} [bold magenta]{self.root_path.name}/[/bold magenta]",
            guide_style="dim"
        )
        
        # 递归添加节点
        self.add_tree_node(tree, self.root_path, max_depth)
        
        # 显示树
        console.print(tree)
        console.print()
        
        # 统计信息
        stats_text = Text()
        stats_text.append("📦 统计信息: ", style="bold")
        stats_text.append(f"{self.dir_count} 个目录, ", style="cyan")
        stats_text.append(f"{self.file_count} 个文件, ", style="green")
        stats_text.append(f"总大小: {self.get_size_str(self.total_size)}", style="yellow")
        
        console.print(Panel(stats_text, border_style="dim", box=box.SIMPLE))


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="项目结构树形可视化工具")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="要展示的目录路径（默认: 当前目录）"
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=3,
        help="最大显示深度（默认: 3）"
    )
    
    args = parser.parse_args()
    
    try:
        viewer = ProjectTreeView(args.path)
        viewer.show(max_depth=args.depth)
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()
