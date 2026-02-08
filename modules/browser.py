"""
浏览器控制模块 - 负责Chrome自动化和AI Studio交互
"""
import time
import os
from typing import Optional, List
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger


class AIStudioController:
    """AI Studio浏览器控制器"""
    
    def __init__(self, config: dict):
        """
        初始化控制器
        
        Args:
            config: 配置字典，包含chrome和ai_studio配置
        """
        self.config = config
        self.driver: Optional[Driver] = None
        self.conversation_history: List[dict] = []
        
    def start(self) -> bool:
        """
        启动Chrome并打开AI Studio
        
        Returns:
            bool: 启动是否成功
        """
        try:
            chrome_config = self.config['chrome']
            profile_path = chrome_config.get('profile_path')
            port = chrome_config.get('remote_debugging_port', 9222)
            
            logger.info("正在启动Chrome...")
            
            # 使用Chrome Profile保持登录状态（参考用户的工作代码）
            if profile_path and os.path.exists(profile_path):
                logger.info(f"使用Chrome Profile: {chrome_config.get('profile_name', 'default')}")
                logger.info(f"调试端口: {port}")
                
                self.driver = Driver(
                    uc=True,
                    user_data_dir=profile_path,
                    chromium_arg=f"--remote-debugging-port={port}",
                    headless=False
                )
            else:
                logger.warning("未找到Chrome Profile，使用临时profile（需要重新登录）")
                self.driver = Driver(uc=True, headless=False)
            
            logger.success("✅ Chrome启动成功")
            
            # 导航到AI Studio
            ai_studio_url = self.config['ai_studio']['url']
            logger.info(f"正在导航到: {ai_studio_url}")
            self.driver.get(ai_studio_url)
            logger.success("✅ 已导航到AI Studio")
            
            # 等待页面加载
            logger.info("等待页面加载...")
            time.sleep(5)
            
            logger.success("✅ Chrome启动成功，AI Studio已就绪")
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动Chrome失败: {e}")
            logger.exception(e)
            return False
    
    def upload_pdf(self, pdf_path: str) -> bool:
        """
        上传PDF到AI Studio
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            bool: 上传是否成功
        """
        try:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF文件不存在: {pdf_path}")
                return False
            
            logger.info(f"正在上传PDF: {os.path.basename(pdf_path)}")
            
            # 策略: 使用 JS 模拟拖拽上传 (最稳健的方法)
            # 因为 standard input[type='file'] 可能不存在或被隐藏，且 showOpenFilePicker 难以自动化
            try:
                logger.info("尝试使用 JS 模拟拖拽上传...")
                
                # 1. 定位目标元素 (Textarea 或 body)
                target_selector = "textarea"
                try:
                    target = self.driver.find_element(By.CSS_SELECTOR, target_selector)
                except:
                    target = self.driver.find_element(By.TAG_NAME, "body")
                
                # 2. 注入隐藏的 input[type=file]
                JS_CREATE_INPUT = """
                var target = arguments[0];
                var input = document.createElement('input');
                input.type = 'file';
                input.style.display = 'none';
                document.body.appendChild(input);
                return input;
                """
                
                file_input = self.driver.execute_script(JS_CREATE_INPUT, target)
                
                # 3. 发送文件路径到临时 input
                file_input.send_keys(pdf_path)
                
                # 4. 触发 Drop 事件
                JS_TRIGGER_DROP = """
                var target = arguments[0];
                var input = arguments[1];
                var files = input.files;
                
                var dt = new DataTransfer();
                for (var i = 0; i < files.length; i++) {
                    dt.items.add(files[i]);
                }
                
                var evt = new DragEvent('drop', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    dataTransfer: dt
                });
                
                target.dispatchEvent(evt);
                """
                
                # 同时触发 dragenter/dragover 以便激活 UI 状态
                JS_DRAG_ENTER_OVER = """
                var target = arguments[0];
                var dt = new DataTransfer();
                ['dragenter', 'dragover'].forEach(function(e) {
                    var evt = new DragEvent(e, {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        dataTransfer: dt
                    });
                    target.dispatchEvent(evt);
                });
                """
                
                self.driver.execute_script(JS_DRAG_ENTER_OVER, target)
                time.sleep(0.5)
                self.driver.execute_script(JS_TRIGGER_DROP, target, file_input)
                
                logger.success("已触发文件拖拽事件")
                
                # 5. 等待确保文件被处理 (根据用户反馈，AI Studio会自动处理加载)
                time.sleep(3)
                
                # 清理临时 input
                self.driver.execute_script("arguments[0].remove();", file_input)
                
                return True
                
            except Exception as e:
                logger.error(f"JS 拖拽上传失败: {e}")
                return False
            
        except Exception as e:
            logger.error(f"上传PDF失败: {e}")
            return False
    
    def ask_question(self, question: str, context: Optional[List[dict]] = None) -> Optional[str]:
        """
        提交问题并获取回答
        
        Args:
            question: 问题文本
            context: 对话上下文（用于追问）
            
        Returns:
            str: AI的回答（Markdown格式），失败返回None
        """
        try:
            logger.info(f"提交问题: {question[:50]}...")
            
            # 查找输入框
            input_selector = "textarea.cdk-textarea-autosize"
            wait = WebDriverWait(self.driver, 20)
            input_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, input_selector))
            )
            
            # 清空并输入问题
            self.driver.execute_script("arguments[0].value = '';", input_box)
            input_box.send_keys(question)
            time.sleep(1)
            
            # 记录提问前的回答数量
            initial_count = len(self.driver.find_elements(By.CSS_SELECTOR, "ms-prompt-renderer"))
            
            # 点击Run按钮
            run_btn = None
            try:
                # 尝试1: 直接找 ms-run-button 下的 button
                run_btns = self.driver.find_elements(By.CSS_SELECTOR, "ms-run-button button")
                
                for btn in run_btns:
                    if "run" in btn.text.lower():
                        run_btn = btn
                        break
                
                # 尝试2: 如果上面没找到，找页面上所有包含 Run 的 button
                if not run_btn:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        if btn.text and "run" in btn.text.lower() and "gemini" not in btn.text.lower():
                             run_btn = btn
                             break
                
                if run_btn:
                    self.driver.execute_script("arguments[0].click();", run_btn)
                    logger.info("✅ 已点击Run按钮")
                else:
                    raise Exception("Element not found")

            except Exception as e:
                logger.error(f"无法找到Run按钮: {e}")
                
                # 调试代码：仅在彻底失败时打印
                logger.debug("Debugging buttons...")
                # ... (原有调试代码保持不变，或者略去)
                return None
            
            # 获取配置的超时时间
            timeout = self.config.get('ai_studio', {}).get('wait_timeout', 180)
            
            # 等待回答生成（传入run_btn用于补救重试）
            answer = self._wait_for_answer(initial_count, max_wait=timeout, run_button=run_btn)
            
            if answer:
                # 保存到对话历史
                self.conversation_history.append({
                    'question': question,
                    'answer': answer,
                    'timestamp': time.time()
                })
                logger.success("获取回答成功")
                return answer
            else:
                logger.warning("未能获取回答")
                return None
                
        except Exception as e:
            logger.error(f"提交问题失败: {e}")
            return None
    
    def _wait_for_answer(self, initial_count: int, max_wait: int = 180, run_button=None) -> Optional[str]:
            """
            等待AI回答生成 - 精准定位 ms-text-chunk 版
            """
            try:
                success = False
                answer_text = None
                last_text_length = 0
                stable_count = 0  # 内容稳定计数器
                
                logger.info("开始等待回答生成 (Target: ms-text-chunk)...")

                # 增加检查次数
                for step in range(max_wait // 3):
                    time.sleep(3)
                    
                    # 强制滚动到底部，触发懒加载
                    try:
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    except:
                        pass
                    
                    # --- 核心修改：直接定位 ms-text-chunk ---
                    # 逻辑：找出页面上所有的文本块，取最后一个（即最新的回答）
                    try:
                        text_chunks = self.driver.find_elements(By.CSS_SELECTOR, "ms-text-chunk")
                        
                        if text_chunks:
                            latest_chunk = text_chunks[-1]
                            
                            # 使用 JS 获取 innerText，这比 .text 更可靠，且只包含该标签内的文本
                            # 这样就完美避开了外层的 menu_open, tokens 等 UI 噪音
                            current_text = self.driver.execute_script("return arguments[0].innerText;", latest_chunk)
                            
                            if current_text:
                                current_text = current_text.strip()
                            else:
                                current_text = ""
                        else:
                            current_text = ""
                            
                    except Exception as e:
                        logger.debug(f"获取文本块失败: {e}")
                        current_text = ""

                    # --- 长度监控逻辑 ---
                    current_length = len(current_text)
                    
                    # 如果超时未响应，尝试补救点击 Run
                    if step == 10 and last_text_length == 0 and run_button:
                        logger.info("30秒未检测到内容变化，尝试重新点击Run按钮...")
                        try:
                            self.driver.execute_script("arguments[0].click();", run_button)
                        except:
                            pass

                    # 记录内容变化
                    if current_length != last_text_length:
                        # 只有当长度增加，或者原本是0现在有了内容时，才视为有效变化
                        if current_length > last_text_length or (last_text_length == 0 and current_length > 0):
                            logger.debug(f"检测到内容变化: {last_text_length} -> {current_length} 字符")
                            last_text_length = current_length
                            stable_count = 0
                            
                            if current_length > 10: # 只要有内容就算开始
                                answer_text = current_text
                    else:
                        # 内容没有变化
                        if current_length > 10:
                            stable_count += 1
                            # 连续 2 轮（6秒）没有变化，且有内容，认为生成结束
                            if stable_count >= 2:
                                logger.info(f"✅ 成功获取回答（长度: {current_length} 字符，内容已稳定）")
                                answer_text = current_text
                                success = True
                                break
                    
                    if step % 5 == 0 and step > 0:
                        logger.info(f"等待回答中... ({step * 3}s / {max_wait}s, 当前长度: {last_text_length})")
                
                if success:
                    return answer_text
                else:
                    logger.warning(f"等待超时，最终长度: {last_text_length}")
                    if last_text_length > 10 and answer_text:
                        logger.info(f"⚠️  超时但返回已有内容")
                        return answer_text
                    else:
                        # 超时且没有获取到任何内容，可能是网络问题
                        logger.error("❌ 等待回答超时，未获取到任何内容")
                        logger.warning("⚠️  可能存在网络问题，请检查网络连接后手动点击 AI Studio 页面的 Run 按钮重试")
                    return None
                    
            except Exception as e:
                logger.error(f"等待回答时出错: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                return None 
    def get_conversation_history(self) -> List[dict]:
        """获取对话历史"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except:
                pass
