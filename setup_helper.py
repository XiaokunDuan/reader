#!/usr/bin/env python3
"""
配置向导 - 自动检测路径并生成config.yaml
"""
import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional, List
import yaml
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


class SetupHelper:
    """配置向导助手"""
    
    def __init__(self):
        self.config = {}
        self.system = platform.system()
    
    def run(self):
        """运行配置向导"""
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]🚀 智能论文阅读助手 - 配置向导[/bold cyan]\n"
            "[dim]自动检测路径并生成配置文件[/dim]",
            border_style="cyan"
        ))
        console.print()
        
        # 1. Chrome配置
        self._setup_chrome()
        
        # 2. Obsidian配置
        self._setup_obsidian()
        
        # 3. AI服务配置
        self._setup_ai_service()
        
        # 4. 初始问题配置
        self._setup_initial_questions()
        
        # 5. 保存配置
        self._save_config()
        
        console.print()
        console.print("[bold green]✅ 配置完成！[/bold green]")
        console.print("[dim]现在可以运行:[/dim] [bold]python main.py[/bold]")
    
    def _setup_chrome(self):
        """配置Chrome"""
        console.print("[bold]📌 步骤 1/4: Chrome 配置[/bold]")
        console.print()
        
        # 自动检测Chrome路径
        chrome_paths = self._detect_chrome_profiles()
        
        if chrome_paths:
            console.print("[green]✓[/green] 检测到以下Chrome Profiles:")
            
            table = Table(show_header=True, box=box.SIMPLE)
            table.add_column("序号", style="cyan")
            table.add_column("Profile名称", style="yellow")
            table.add_column("路径", style="dim")
            
            for i, (name, path) in enumerate(chrome_paths, 1):
                table.add_row(str(i), name, str(path))
            
            console.print(table)
            console.print()
            
            choice = Prompt.ask(
                "请选择要使用的Profile",
                choices=[str(i) for i in range(1, len(chrome_paths) + 1)],
                default="1"
            )
            
            profile_name, profile_path = chrome_paths[int(choice) - 1]
        else:
            console.print("[yellow]⚠[/yellow]  未检测到Chrome Profiles，请手动输入")
            profile_name = Prompt.ask("Profile名称", default="Default")
            profile_path = Prompt.ask("Profile路径（留空用默认）", default="")
        
        # 调试端口
        debug_port = Prompt.ask(
            "远程调试端口",
            default="9222"
        )
        
        self.config['chrome'] = {
            'profile_name': profile_name,
            'profile_path': str(profile_path) if profile_path else "",
            'remote_debugging_port': int(debug_port)
        }
        
        console.print()
    
    def _setup_obsidian(self):
        """配置Obsidian"""
        console.print("[bold]📌 步骤 2/4: Obsidian 配置[/bold]")
        console.print()
        
        # 自动检测Obsidian Vault
        vaults = self._detect_obsidian_vaults()
        
        if vaults:
            console.print("[green]✓[/green] 检测到以下Obsidian Vaults:")
            
            table = Table(show_header=True, box=box.SIMPLE)
            table.add_column("序号", style="cyan")
            table.add_column("Vault名称", style="yellow")
            table.add_column("路径", style="dim")
            
            for i, vault in enumerate(vaults, 1):
                vault_name = vault.name
                table.add_row(str(i), vault_name, str(vault))
            
            console.print(table)
            console.print()
            
            choice = Prompt.ask(
                "请选择要使用的Vault",
                choices=[str(i) for i in range(1, len(vaults) + 1)] + ["0"],
                default="1"
            )
            
            if choice == "0":
                vault_path = Prompt.ask("请输入Vault路径")
            else:
                vault_path = str(vaults[int(choice) - 1])
        else:
            console.print("[yellow]⚠[/yellow]  未检测到Obsidian Vaults")
            vault_path = Prompt.ask("请输入Vault路径")
        
        self.config['obsidian'] = {
            'vault_path': vault_path,
            'assets_folder': 'assets',
            'default_tags': ['论文笔记', 'AI生成']
        }
        
        console.print()
    
    def _setup_ai_service(self):
        """配置AI服务"""
        console.print("[bold]📌 步骤 3/4: AI 服务配置[/bold]")
        console.print()
        
        console.print("支持的AI服务:")
        console.print("  [cyan]1.[/cyan] 百度千帆 (DeepSeek)")
        console.print("  [cyan]2.[/cyan] OpenAI (GPT-4)")
        console.print("  [cyan]3.[/cyan] Anthropic Claude")
        console.print("  [cyan]4.[/cyan] Ollama (本地LLM)")
        console.print()
        
        provider_choice = Prompt.ask(
            "选择AI服务",
            choices=["1", "2", "3", "4"],
            default="1"
        )
        
        provider_map = {
            "1": "baidu",
            "2": "openai",
            "3": "claude",
            "4": "ollama"
        }
        
        provider = provider_map[provider_choice]
        
        if provider == "baidu":
            api_key = Prompt.ask("百度API Key")
            self.config['ai_service'] = {
                'provider': 'baidu',
                'baidu': {
                    'base_url': 'https://qianfan.baidubce.com/v2',
                    'api_key': api_key,
                    'model': 'deepseek-v3.2',
                    'timeout': 30,
                    'max_retries': 3
                }
            }
        elif provider == "openai":
            api_key = Prompt.ask("OpenAI API Key")
            model = Prompt.ask("模型名称", default="gpt-4")
            base_url = Prompt.ask("Base URL (兼容API可修改)", default="https://api.openai.com/v1")
            self.config['ai_service'] = {
                'provider': 'openai',
                'openai': {
                    'api_key': api_key,
                    'model': model,
                    'base_url': base_url,
                    'timeout': 30,
                    'max_retries': 3
                }
            }
        elif provider == "claude":
            api_key = Prompt.ask("Anthropic API Key")
            model = Prompt.ask("模型名称", default="claude-3-5-sonnet-20241022")
            self.config['ai_service'] = {
                'provider': 'claude',
                'claude': {
                    'api_key': api_key,
                    'model': model,
                    'timeout': 30,
                    'max_retries': 3
                }
            }
        elif provider == "ollama":
            base_url = Prompt.ask("Ollama服务地址", default="http://localhost:11434")
            model = Prompt.ask("模型名称", default="llama3")
            self.config['ai_service'] = {
                'provider': 'ollama',
                'ollama': {
                    'base_url': base_url,
                    'model': model,
                    'timeout': 30,
                    'max_retries': 3
                }
            }
        
        # 保留旧的deepseek配置以兼容旧代码
        if provider == "baidu":
            self.config['deepseek'] = self.config['ai_service']['baidu']
        
        console.print()
    
    def _setup_initial_questions(self):
        """配置初始问题"""
        console.print("[bold]📌 步骤 4/4: 初始问题配置[/bold]")
        console.print()
        
        console.print("PDF上传后可以自动提问，帮助快速了解论文")
        enable = Confirm.ask("是否启用自动提问?", default=True)
        
        if enable:
            console.print()
            console.print("默认问题: [cyan]这篇论文讲了什么[/cyan]")
            use_custom = Confirm.ask("是否自定义问题?", default=False)
            
            if use_custom:
                questions = []
                console.print("[dim]输入问题（留空结束）[/dim]")
                i = 1
                while True:
                    q = Prompt.ask(f"问题 {i}", default="")
                    if not q:
                        break
                    questions.append(q)
                    i += 1
                
                if not questions:
                    questions = ["这篇论文讲了什么"]
            else:
                questions = ["这篇论文讲了什么"]
        else:
            questions = []
        
        self.config['initial_questions'] = {
            'enabled': enable,
            'questions': questions
        }
        
        console.print()
    
    def _save_config(self):
        """保存配置文件"""
        # 添加其他默认配置
        self.config.update({
            'ai_studio': {
                'url': 'https://aistudio.google.com/prompts/new_chat',
                'wait_timeout': 120,
                'upload_timeout': 60
            },
            'interaction': {
                'default_mode': 'realtime',
                'auto_save_threshold': 0.7,
                'enable_follow_up': True,
                'max_follow_up_depth': 5
            },
            'data': {
                'queue_file': 'data/queue.json',
                'history_file': 'data/history.json',
                'cache_dir': 'data/cache'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/app.log',
                'max_size_mb': 10,
                'backup_count': 5
            }
        })
        
        # 保存到config.yaml
        config_path = Path('config.yaml')
        
        if config_path.exists():
            backup = Confirm.ask(
                "[yellow]config.yaml已存在，是否备份?[/yellow]",
                default=True
            )
            if backup:
                backup_path = Path('config.yaml.backup')
                config_path.rename(backup_path)
                console.print(f"[dim]已备份到: {backup_path}[/dim]")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.config,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False
            )
        
        console.print(f"[green]✓[/green] 配置已保存到: [bold]{config_path}[/bold]")
    
    def _detect_chrome_profiles(self) -> List[tuple]:
        """检测Chrome Profiles"""
        profiles = []
        
        if self.system == "Darwin":  # macOS
            base_path = Path.home() / "Library/Application Support/Google/Chrome"
        elif self.system == "Windows":
            base_path = Path.home() / "AppData/Local/Google/Chrome/User Data"
        elif self.system == "Linux":
            base_path = Path.home() / ".config/google-chrome"
        else:
            return profiles
        
        if not base_path.exists():
            return profiles
        
        # 查找所有Profile目录
        for item in base_path.iterdir():
            if item.is_dir():
                # Default 或 Profile N
                if item.name == "Default" or item.name.startswith("Profile"):
                    profiles.append((item.name, item))
        
        return profiles
    
    def _detect_obsidian_vaults(self) -> List[Path]:
        """检测Obsidian Vaults"""
        vaults = []
        
        # 常见的Obsidian Vault位置
        search_paths = [
            Path.home() / "Documents",
            Path.home() / "Obsidian",
            Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents",  # iCloud
            Path.home() / "Repos",
            Path.home() / "Projects",
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            # 搜索包含.obsidian文件夹的目录
            try:
                for item in search_path.rglob(".obsidian"):
                    if item.is_dir():
                        vault_path = item.parent
                        if vault_path not in vaults:
                            vaults.append(vault_path)
            except (PermissionError, OSError):
                continue
        
        return vaults[:10]  # 最多返回10个


def main():
    """主函数"""
    try:
        helper = SetupHelper()
        helper.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]配置已取消[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]错误: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
