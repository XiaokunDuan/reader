"""
智能论文阅读助手 - 主程序入口
"""
import os
import sys
import yaml
from loguru import logger

from modules.browser import AIStudioController
from modules.cli import CLI
from modules.obsidian import ObsidianWriter
from modules.knowledge import KnowledgeAnalyzer


class PaperReadingAssistant:
    """论文阅读助手主程序"""
    
    def __init__(self, config_path: str = "config.yaml", verbose: bool = False):
        """初始化"""
        # 加载配置
        self.config = self._load_config(config_path)
        self.verbose = verbose
        
        # 配置日志
        self._setup_logging()
        
        # 初始化各模块
        self.cli = CLI()
        self.browser = AIStudioController(self.config)
        self.obsidian = ObsidianWriter(self.config)
        self.knowledge = None  # 延迟初始化
        
        # 状态
        self.current_pdf = None
        self.current_paper_title = None
        self.qa_chain = []
        self.attachments = []
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """配置日志 - 默认安静模式，仅写入文件"""
        log_config = self.config.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        log_file = log_config.get('file', 'logs/app.log')
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置loguru
        logger.remove()  # 移除默认handler
        
        # 只有在 verbose 模式下才输出到 stderr
        if self.verbose:
            logger.add(
                sys.stderr,
                level=log_level,
                format="<dim>{time:HH:mm:ss}</dim> | <level>{level: <8}</level> | <level>{message}</level>"
            )
        
        # 始终写入日志文件
        logger.add(
            log_file,
            rotation=f"{log_config.get('max_size_mb', 10)} MB",
            retention=log_config.get('backup_count', 5),
            level=log_level
        )
    
    def run(self, initial_pdf_path: str = None):
        """主运行循环"""
        try:
            # 显示欢迎信息
            self.cli.show_banner()
            
            # 启动浏览器 (使用 Spinner)
            with self.cli.status("正在启动 Chrome..."):
                success = self.browser.start()
            
            if not success:
                self.cli.show_error("Chrome 启动失败")
                return
            
            self.cli.show_success("Chrome 已启动，AI Studio 已就绪")
            
            # 上传PDF
            if initial_pdf_path:
                pdf_path = initial_pdf_path
                self.cli.show_info(f"使用命令行提供的 PDF")
            else:
                pdf_path = self.cli.prompt_pdf_path()
            
            if not os.path.exists(pdf_path):
                self.cli.show_error(f"PDF 文件不存在: {pdf_path}")
                return
            
            # 上传 PDF (使用 Spinner)
            with self.cli.status("正在上传 PDF 到 AI Studio..."):
                upload_success = self.browser.upload_pdf(pdf_path)
            
            if not upload_success:
                self.cli.show_error("PDF 上传失败")
                return
            
            self.current_pdf = pdf_path
            self.current_paper_title = os.path.splitext(os.path.basename(pdf_path))[0]
            self.cli.current_paper_title = self.current_paper_title  # 同步给 CLI
            self.cli.show_success(f"PDF 上传成功")
            
            # 自动提问：这篇论文讲了什么 (使用 Spinner)
            initial_question = "这篇论文讲了什么"
            with self.cli.status("正在生成论文摘要..."):
                answer = self.browser.ask_question(initial_question)
            
            if answer:
                self.cli.show_answer(initial_question, answer)
                # 初始化问答链，方便用户直接保存摘要
                self.qa_chain = [{'question': initial_question, 'answer': answer}]
                self.attachments = []
                # 提示用户可以保存或继续
                self.cli.show_info("输入 [s] 保存摘要，或 [q: 问题] 继续提问")
            else:
                self.cli.show_error("获取摘要失败")

            # 扫描Obsidian库结构（用于DeepSeek分析）
            with self.cli.status("正在扫描 Obsidian 库..."):
                vault_structure = self.obsidian.scan_vault_structure()
                self.knowledge = KnowledgeAnalyzer(self.config, vault_structure)
            
            self.cli.show_success(f"已索引 {vault_structure['total_notes']} 个笔记")
            
            # 进入交互模式
            self.cli.show_help()
            
            self._interactive_loop()
            
        except KeyboardInterrupt:
            self.cli.show_warning("用户中断")
        except Exception as e:
            self.cli.show_error(f"程序异常: {e}")
            logger.exception(e)
        finally:
            self.cleanup()
    
    def _interactive_loop(self):
        """交互式命令循环"""
        while True:
            cmd = self.cli.interactive_mode()
            cmd_type, param = self.cli.parse_command(cmd)
            
            if cmd_type == "add_question":
                self.cli.add_question(param)
            
            elif cmd_type == "list":
                self.cli.show_queue()
            
            elif cmd_type == "run":
                if not self.cli.question_queue:
                    self.cli.show_warning("队列为空，请先添加问题")
                    continue
                self._process_queue()
            
            elif cmd_type == "clear":
                self.cli.clear_queue()
            
            elif cmd_type == "help":
                self.cli.show_help()
            
            elif cmd_type == "exit":
                self.cli.show_info("再见！")
                break
            
            else:
                self.cli.show_warning(f"未知命令: {cmd}")
                self.cli.show_info("输入 help 或 ? 查看帮助")
    
    def _process_queue(self):
        """处理问题队列"""
        total = len(self.cli.question_queue)
        
        for i, question in enumerate(self.cli.question_queue, 1):
            # 提交问题 (使用 Spinner)
            with self.cli.status(f"正在处理问题 [{i}/{total}]..."):
                answer = self.browser.ask_question(question)
            
            if not answer:
                self.cli.show_error("未能获取回答，跳过")
                continue
            
            # 显示回答
            self.cli.show_answer(question, answer, i, total)
            
            # 初始化当前问答链
            self.qa_chain = [{'question': question, 'answer': answer}]
            self.attachments = []
            
            # 处理用户选择
            self._handle_user_choice()
        
        # 清空队列
        self.cli.clear_queue()
        self.cli.show_success("所有问题处理完成！")
    
    def _handle_user_choice(self):
        """处理用户对当前回答的选择"""
        while True:
            choice = self.cli.show_options(enable_follow=True)
            
            if choice == "save":
                self._save_current_qa()
                break
            
            elif choice == "skip":
                self.cli.show_info("已跳过")
                break
            
            elif choice == "follow":
                self._handle_follow_up()
            
            elif choice == "attach":
                attachment = self.cli.prompt_attachment()
                if attachment:
                    self.attachments.append(attachment)
            
            elif choice == "next":
                break
            
            else:
                self.cli.show_warning("暂不支持该选项")
    
    def _handle_follow_up(self):
        """处理追问"""
        while True:
            follow_question = self.cli.prompt_follow_up()
            
            if not follow_question:
                self.cli.show_info("追问结束")
                break
            
            with self.cli.status("正在提交追问..."):
                answer = self.browser.ask_question(follow_question)
            
            if answer:
                self.cli.show_answer(follow_question, answer)
                self.qa_chain.append({'question': follow_question, 'answer': answer})
            else:
                self.cli.show_error("未能获取回答")
    
    def _save_current_qa(self):
        """保存当前问答到Obsidian"""
        try:
            # 使用DeepSeek分析归类
            with self.cli.status("正在使用 DeepSeek 分析归类位置..."):
                classification = self.knowledge.analyze_placement(
                    self.qa_chain,
                    self.current_paper_title
                )
            
            # 显示归类结果
            self.cli.show_classification_result(classification)
            
            # 确认保存
            if not self.cli.confirm_save():
                self.cli.show_info("已取消保存")
                return
            
            # 写入笔记
            with self.cli.status("正在保存笔记..."):
                success = self.obsidian.write_note(
                    target_path=classification['target_path'],
                    qa_chain=self.qa_chain,
                    paper_title=self.current_paper_title,
                    attachments=self.attachments,
                    classification=classification
                )
            
            if success:
                full_path = os.path.join(
                    self.config['obsidian']['vault_path'],
                    classification['target_path']
                )
                self.cli.show_success("保存成功！")
                self.cli.show_info(f"📍 {full_path}")
            else:
                self.cli.show_error("保存失败")
                
        except Exception as e:
            self.cli.show_error(f"保存过程出错: {e}")
            logger.exception(e)
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理资源...")
        self.browser.close()


import argparse

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能论文阅读助手")
    parser.add_argument("--pdf", help="PDF文件路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    args = parser.parse_args()
    
    app = PaperReadingAssistant(verbose=args.verbose)
    app.run(initial_pdf_path=args.pdf)

if __name__ == "__main__":
    main()
