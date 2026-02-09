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
from modules.qa_tree import QATree, QATreeManager
from modules.qa_tree_view import show_qa_tree_interactive
from modules.templates import TemplateManager
from modules.statistics import ReadingStats


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
        
        # 对话树
        self.qa_tree = QATree()
        self.qa_tree_manager = QATreeManager()
        self.current_tree_node = None  # 当前对话树节点（用于追问）
        
        # 模板管理
        self.template_manager = TemplateManager()
        
        # 统计模块
        self.stats = ReadingStats()
        
        # 状态
        self.current_pdf = None
        self.current_paper_title = None
        self.current_file_type = None  # 新增: 记录文件类型
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
            
            # 获取输入（PDF/文件 或 URL）
            if initial_pdf_path:
                input_path = initial_pdf_path
                self.cli.show_info(f"使用命令行提供的输入")
            else:
                input_path = self.cli.prompt_input_path()  # 更新为通用输入
            
            # 检测是URL还是文件
            is_url = self.browser.is_url(input_path)
            
            if is_url:
                # 处理URL
                url_type = self.browser.detect_url_type(input_path)
                self.cli.show_info(f"检测到 {url_type} 链接")
                
                with self.cli.status("正在发送链接到 AI Studio..."):
                    upload_success = self.browser.send_url(input_path)
                    self.current_file_type = url_type
                
                if not upload_success:
                    self.cli.show_error("链接发送失败")
                    return
                
                self.current_pdf = input_path
                # 从URL提取标题
                from urllib.parse import urlparse
                parsed = urlparse(input_path)
                self.current_paper_title = parsed.netloc + parsed.path[:30]
                
            else:
                # 处理文件
                if not os.path.exists(input_path):
                    self.cli.show_error(f"文件不存在: {input_path}")
                    return
                
                with self.cli.status("正在上传文件到 AI Studio..."):
                    upload_success, file_type = self.browser.upload_file(input_path)
                    self.current_file_type = file_type
                
                if not upload_success:
                    self.cli.show_error("文件上传失败")
                    return
                
                self.current_pdf = input_path
                self.current_paper_title = os.path.splitext(os.path.basename(input_path))[0]
            
            # 开始统计会话
            self.stats.start_session(self.current_paper_title, self.current_file_type)
            self.cli.current_paper_title = self.current_paper_title  # 同步给 CLI
            self.cli.show_success(f"内容已加载")
            
            # 根据内容类型选择初始问题
            initial_config = self.config.get('initial_questions', {})
            if initial_config.get('enabled', True):
                # 根据文件类型选择合适的问题
                file_type = self.current_file_type
                
                if file_type in ['youtube', 'video', 'video_site']:
                    default_question = "这个视频讲了什么"
                    status_text = "正在分析视频内容..."
                elif file_type in ['audio']:
                    default_question = "这段音频讲了什么"
                    status_text = "正在分析音频内容..."
                elif file_type in ['image']:
                    default_question = "这张图片展示了什么"
                    status_text = "正在分析图片内容..."
                elif file_type in ['webpage', 'academic', 'github']:
                    default_question = "这个网页讲了什么"
                    status_text = "正在分析网页内容..."
                else:
                    default_question = "这篇论文讲了什么"
                    status_text = "正在生成论文摘要..."
                
                questions = initial_config.get('questions', [default_question])
                # 如果配置中有问题但第一个是默认值，替换为类型相关的问题
                if questions and questions[0] == "这篇论文讲了什么" and file_type in ['youtube', 'video', 'video_site', 'audio', 'image', 'webpage', 'academic', 'github']:
                    questions[0] = default_question
                
                if questions:
                    first_question = questions[0]
                    
                    with self.cli.status(status_text):
                        answer = self.browser.ask_question(first_question)
                    
                    if answer:
                        self.cli.show_answer(first_question, answer)
                        self.qa_chain = [{'question': first_question, 'answer': answer}]
                        self.attachments = []
                        
                        if len(questions) > 1:
                            self.cli.show_info(f"还有 {len(questions)-1} 个初始问题已加入队列")
                            for q in questions[1:]:
                                self.cli.add_question(q)
                        
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
            
            elif cmd_type == "upload":
                # 处理上传新内容
                if not param:
                    param = self.cli.prompt_input_path()
                
                if param:
                    self._handle_upload_new_content(param)
            
            elif cmd_type == "clear":
                self.cli.clear_queue()
            
            elif cmd_type == "tree":
                self._show_qa_tree()
            
            elif cmd_type == "template":
                self._handle_template_command(param)
            
            elif cmd_type == "help":
                self.cli.show_help()
            
            elif cmd_type == "exit":
                # 保存对话树
                if self.current_paper_title and self.qa_tree.roots:
                    self.qa_tree_manager.save_tree(self.qa_tree, self.current_paper_title)
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
            
            # 记录问题到统计
            self.stats.add_question()
            
            # 添加到对话树（根节点）
            tree_node = self.qa_tree.add_question(
                question=question,
                answer=answer,
                parent=None,
                ai_adapter=self.knowledge.ai_adapter if self.knowledge else None
            )
            self.current_tree_node = tree_node
            
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
                
                # 添加到对话树（作为当前节点的子节点）
                if self.current_tree_node:
                    child_node = self.qa_tree.add_question(
                        question=follow_question,
                        answer=answer,
                        parent=self.current_tree_node,
                        ai_adapter=self.knowledge.ai_adapter if self.knowledge else None
                    )
                    self.current_tree_node = child_node
                
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
    
    def _show_qa_tree(self):
        """显示对话历史树"""
        if not self.qa_tree.roots:
            self.cli.show_warning("对话树为空，还没有任何提问记录")
            return
        
        # 显示交互式树形视图
        action, selected_node = show_qa_tree_interactive(
            self.qa_tree,
            on_followup=None
        )
        
        # 处理用户操作
        if action == "followup" and selected_node:
            self.cli.show_info(f"在节点 [{selected_node.summary}] 追问")
            
            # 设置当前节点为选中节点
            self.current_tree_node = selected_node
            
            # 进入追问模式
            while True:
                follow_question = self.cli.prompt_follow_up()
                
                if not follow_question:
                    self.cli.show_info("追问结束")
                    break
                
                with self.cli.status("正在提交追问..."):
                    answer = self.browser.ask_question(follow_question)
                
                if answer:
                    self.cli.show_answer(follow_question, answer)
                    
                    # 添加到对话树
                    child_node = self.qa_tree.add_question(
                        question=follow_question,
                        answer=answer,
                        parent=self.current_tree_node,
                        ai_adapter=self.knowledge.ai_adapter if self.knowledge else None
                    )
                    self.current_tree_node = child_node
                    
                    # 保存对话树
                    if self.current_paper_title:
                        self.qa_tree_manager.save_tree(self.qa_tree, self.current_paper_title)
                    
                    self.cli.show_success("追问已添加到对话树")
                else:
                    self.cli.show_error("未能获取回答")
            
            # 返回后重新显示树
            self._show_qa_tree()
    
    def _handle_template_command(self, param: str):
        """处理模板命令"""
        if not param:
            # 默认列出所有模板
            param = "list"
        
        parts = param.split(maxsplit=1)
        subcommand = parts[0]
        
        if subcommand == "list":
            # 列出所有模板
            templates = self.template_manager.list_templates()
            
            if not templates:
                self.cli.show_warning("没有可用的模板")
                return
            
            self.cli.show_template_list(templates)
        
        elif subcommand == "use":
            # 使用模板
            if len(parts) < 2:
                self.cli.show_error("请指定模板名称，如: template use paper_reading")
                return
            
            template_name = parts[1]
            template = self.template_manager.get_template(template_name)
            
            if not template:
                self.cli.show_error(f"模板不存在: {template_name}")
                self.cli.show_info("使用 'template list' 查看所有模板")
                return
            
            # 应用模板
            context = {"paper_title": self.current_paper_title or "该文献"}
            questions = template.apply(context)
            
            # 清空队列并添加模板问题
            self.cli.clear_queue()
            for question in questions:
                self.cli.add_question(question)
            
            self.cli.show_success(f"已应用模板: {template.name} ({len(questions)}个问题)")
            self.cli.show_info("使用 'run' 执行问题队列")
        
        elif subcommand == "create":
            # 创建自定义模板
            self.cli.show_info("创建自定义模板")
            self._create_custom_template()
        
        else:
            self.cli.show_error(f"未知的模板命令: {subcommand}")
            self.cli.show_info("支持的命令: list, use, create")
    
    def _create_custom_template(self):
        """创建自定义模板的交互流程"""
        from rich.prompt import Prompt
        
        name = Prompt.ask("模板名称")
        description = Prompt.ask("模板描述")
        
        self.cli.show_info("输入问题列表（每行一个问题，输入空行结束）:")
        questions = []
        while True:
            question = Prompt.ask(f"问题 {len(questions) + 1}", default="")
            if not question:
                break
            questions.append(question)
        
        if not questions:
            self.cli.show_warning("未添加任何问题，取消创建")
            return
        
        # 创建模板
        template = self.template_manager.create_template(
            name=name,
            description=description,
            questions=questions,
            category="custom"
        )
        
        self.cli.show_success(f"自定义模板已创建: {template.name}")
        self.cli.show_info(f"包含 {len(questions)} 个问题")
    
    def _handle_upload_new_content(self, input_path: str):
        """处理上传新内容"""
        # 1. 结束当前会话
        if self.stats.current_session:
            self.stats.end_session()
        
        # 2. 检测类型
        is_url = self.browser.is_url(input_path)
        
        # 3. 上传/发送
        if is_url:
            url_type = self.browser.detect_url_type(input_path)
            self.cli.show_info(f"检测到 {url_type} 链接")
            
            with self.cli.status("正在切换内容..."):
                upload_success = self.browser.send_url(input_path)
                self.current_file_type = url_type
            
            if not upload_success:
                self.cli.show_error("链接发送失败")
                return
            
            self.current_pdf = input_path
            from urllib.parse import urlparse
            parsed = urlparse(input_path)
            self.current_paper_title = parsed.netloc + parsed.path[:30]
            
        else:
            if not os.path.exists(input_path):
                self.cli.show_error(f"文件不存在: {input_path}")
                return
            
            with self.cli.status("正在上传新文件..."):
                upload_success, file_type = self.browser.upload_file(input_path)
                self.current_file_type = file_type
            
            if not upload_success:
                self.cli.show_error("文件上传失败")
                return
            
            self.current_pdf = input_path
            self.current_paper_title = os.path.splitext(os.path.basename(input_path))[0]
        
        # 4. 更新状态
        self.cli.current_paper_title = self.current_paper_title
        self.stats.start_session(self.current_paper_title, self.current_file_type)
        self.cli.show_success("内容已更新")
        
        # 5. 提示是否生成摘要
        from rich.prompt import Confirm
        if Confirm.ask("是否生成内容摘要？", default=True):
            # 根据类型选择问题
            if self.current_file_type in ['youtube', 'video', 'video_site']:
                q = "这个视频讲了什么"
            elif self.current_file_type in ['audio']:
                q = "这段音频讲了什么"
            elif self.current_file_type in ['image']:
                q = "这张图片展示了什么"
            elif self.current_file_type in ['webpage', 'academic', 'github']:
                q = "这个网页讲了什么"
            else:
                q = "这篇论文讲了什么"
            
            with self.cli.status("正在分析内容..."):
                answer = self.browser.ask_question(q)
            
            if answer:
                self.cli.show_answer(q, answer)
                self.stats.add_question()
                # 添加到对话树
                self.qa_tree.add_question(q, answer, ai_adapter=None)
    
    def cleanup(self):
        """清理资源"""
        logger.info("正在清理资源...")
        # 结束统计会话
        if self.stats.current_session:
            self.stats.end_session()
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
