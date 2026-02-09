"""
知识管理模块 - 使用AI进行智能归类
"""
import json
from typing import Dict, Optional
from loguru import logger
from modules.ai_adapter import create_ai_adapter, AIServiceAdapter


class KnowledgeAnalyzer:
    """知识分析器 - 使用AI进行智能归类"""
    
    def __init__(self, config: dict, vault_structure: Dict = None):
        """
        初始化分析器
        
        Args:
            config: 配置字典
            vault_structure: Obsidian库结构
        """
        self.config = config
        self.vault_structure = vault_structure or {'folders': [], 'notes': []}
        
        # 使用AI适配器
        self.ai_adapter: AIServiceAdapter = create_ai_adapter(config)
        logger.info(f"知识分析器初始化完成，使用AI服务: {config.get('ai_service', {}).get('provider', 'baidu')}")

    
    def analyze_placement(
        self,
        qa_chain: list,
        paper_title: str
    ) -> Optional[Dict]:
        """
        分析知识点应该放在哪里
        
        Args:
            qa_chain: 问答链
            paper_title: 论文标题
            
        Returns:
            dict: 归类结果，包含target_path, reasoning等
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(qa_chain, paper_title)
            
            # 调用DeepSeek API
            logger.info("正在使用DeepSeek分析归类位置...")
            response = self._call_api(prompt)
            
            if response:
                result = self._parse_response(response)
                logger.success(f"归类分析完成: {result.get('target_path', 'N/A')}")
                return result
            else:
                logger.warning("DeepSeek API调用失败，使用默认归类")
                return self._default_classification(qa_chain)
                
        except Exception as e:
            logger.error(f"分析归类失败: {e}")
            return self._default_classification(qa_chain)
    
    def _build_prompt(self, qa_chain: list, paper_title: str) -> str:
        """构建DeepSeek提示词"""
        
        # 提取问答内容
        qa_text = ""
        for i, qa in enumerate(qa_chain):
            qa_text += f"问题{i+1}: {qa['question']}\n"
            qa_text += f"回答{i+1}: {qa['answer'][:500]}...\n\n"  # 限制长度
        
        # 构建目录结构摘要
        folders_summary = "\n".join(self.vault_structure.get('folders', [])[:50])  # 只显示前50个
        
        prompt = f"""
分析以下问答对应该归类到Obsidian知识库的哪个位置。

## 问答内容
{qa_text}

## 来源论文
{paper_title}

## 当前Obsidian目录结构
{folders_summary}

## 任务要求
请根据内容主题进行归类，你的任务是：
1. **分析内容主题**：这个问答讲的是什么领域/概念？
2. **决定归档位置**：
   - 如果现有文件夹合适，选择最匹配的
   - 如果现有分类都不合适，可以创建新文件夹（格式：XX_分类名称）
3. **报告最终位置**：明确说明笔记将写到哪里

## 注意事项
- 不需要判断是否是新概念，所有内容都视为新的
- 可以创建新的文件夹和子目录
- 必须给出清晰的文件路径
- 文件名要简洁且描述性强

## 返回格式
请严格按照以下JSON格式返回（不要包含其他文字）：
{{
    "target_path": "相对路径（如：10_人工智能与科学/深度学习/Transformer.md）",
    "is_new_folder": true或false,
    "folder_created": "新创建的文件夹路径（如果有，否则为null）",
    "reasoning": "归类理由（简短说明为什么放这里）",
    "suggested_links": ["相关笔记1", "相关笔记2"],
    "tags": ["标签1", "标签2"]
}}
"""
        return prompt
    
    def _call_api(self, prompt: str) -> Optional[str]:
        """
        调用AI API
        
        Args:
            prompt: 提示词
            
        Returns:
            str: API响应文本
        """
        try:
            logger.info("正在调用AI服务...")
            response = self.ai_adapter.call_api(prompt)
            
            if response:
                logger.success("AI服务调用成功")
                return response
            else:
                logger.warning("AI服务调用失败")
                return None
                
        except Exception as e:
            logger.error(f"调用AI服务时出错: {e}")
            return None

    
    def _parse_response(self, response: str) -> Dict:
        """
        解析API响应
        
        Args:
            response: API响应文本
            
        Returns:
            dict: 解析后的归类结果
        """
        try:
            # 尝试提取JSON（可能被markdown代码块包裹）
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            
            # 验证必需字段
            if 'target_path' not in result:
                raise ValueError("缺少target_path字段")
            
            return result
            
        except Exception as e:
            logger.error(f"解析API响应失败: {e}")
            logger.debug(f"原始响应: {response}")
            return self._default_classification([])
    
    def _default_classification(self, qa_chain: list) -> Dict:
        """
        默认归类（当API失败时使用）
        
        Args:
            qa_chain: 问答链
            
        Returns:
            dict: 默认归类结果
        """
        # 使用第一个问题作为文件名
        if qa_chain:
            question = qa_chain[0]['question']
            # 简化文件名
            filename = question[:30].replace('?', '').replace('/', '-') + '.md'
        else:
            filename = "未命名笔记.md"
        
        return {
            "target_path": f"00_工作流/论文笔记/{filename}",
            "is_new_folder": False,
            "folder_created": None,
            "reasoning": "API调用失败，使用默认归类",
            "suggested_links": [],
            "tags": ["待整理"]
        }
    
    def update_vault_structure(self, structure: Dict):
        """更新vault结构信息"""
        self.vault_structure = structure
