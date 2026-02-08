"""
Obsidian写入模块 - 负责生成和保存Markdown笔记
"""
import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger


class ObsidianWriter:
    """Obsidian笔记写入器"""
    
    def __init__(self, config: dict):
        """
        初始化写入器
        
        Args:
            config: 配置字典，包含obsidian配置
        """
        self.config = config
        self.vault_path = config['obsidian']['vault_path']
        self.assets_folder = config['obsidian']['assets_folder']
        self.default_tags = config['obsidian']['default_tags']
        
        # 确保assets文件夹存在
        self.assets_path = os.path.join(self.vault_path, self.assets_folder)
        os.makedirs(self.assets_path, exist_ok=True)
    
    def write_note(
        self,
        target_path: str,
        qa_chain: List[Dict],
        paper_title: str,
        attachments: List[str] = None,
        classification: Dict = None
    ) -> bool:
        """
        写入笔记到Obsidian
        
        Args:
            target_path: 目标路径（相对于vault）
            qa_chain: 问答链列表
            paper_title: 论文标题
            attachments: 附件路径列表
            classification: 归类信息
            
        Returns:
            bool: 是否成功
        """
        try:
            # 构建完整路径
            full_path = os.path.join(self.vault_path, target_path)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 生成笔记内容
            content = self._generate_note_content(
                qa_chain, paper_title, attachments, classification
            )
            
            # 写入文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.success(f"笔记已保存: {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存笔记失败: {e}")
            return False
    
    def _generate_note_content(
        self,
        qa_chain: List[Dict],
        paper_title: str,
        attachments: List[str] = None,
        classification: Dict = None
    ) -> str:
        """
        生成笔记内容
        
        Args:
            qa_chain: 问答链
            paper_title: 论文标题
            attachments: 附件列表
            classification: 归类信息
            
        Returns:
            str: Markdown格式的笔记内容
        """
        # 构建标签
        tags = self.default_tags.copy()
        if classification and classification.get('tags'):
            tags.extend(classification['tags'])
        
        # 生成frontmatter
        frontmatter = f"""---
tags: [{', '.join(tags)}]
source: {paper_title}
created: {datetime.now().isoformat()}
---

"""
        
        # 生成主标题（使用第一个问题作为标题）
        main_title = qa_chain[0]['question'] if qa_chain else "未命名笔记"
        content = frontmatter + f"# {main_title}\n\n"
        
        # 生成问答内容
        for i, qa in enumerate(qa_chain):
            if i == 0:
                # 第一个问答直接作为主内容
                content += f"{qa['answer']}\n\n"
            else:
                # 后续追问作为子章节
                content += f"## 追问 {i}: {qa['question']}\n\n"
                content += f"{qa['answer']}\n\n"
            
            content += "---\n\n"
        
        # 添加截图
        if attachments:
            content += "## 相关截图\n\n"
            for attachment in attachments:
                # 复制截图到assets文件夹
                asset_filename = self._copy_attachment(attachment)
                if asset_filename:
                    content += f"![{os.path.basename(attachment)}]({self.assets_folder}/{asset_filename})\n\n"
            
            content += "---\n\n"
        
        # 添加来源信息
        content += "## 来源信息\n\n"
        content += f"- **论文**：[[{paper_title}]]\n"
        content += f"- **提问时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        if len(qa_chain) > 1:
            content += f"- **对话轮数**：{len(qa_chain)}轮追问\n"
        
        content += "\n"
        
        # 添加相关链接
        if classification and classification.get('suggested_links'):
            content += "## 相关概念\n\n"
            for link in classification['suggested_links']:
                content += f"- [[{link}]]\n"
            content += "\n"
        
        return content
    
    def _copy_attachment(self, source_path: str) -> Optional[str]:
        """
        复制附件到assets文件夹
        
        Args:
            source_path: 源文件路径
            
        Returns:
            str: 新文件名，失败返回None
        """
        try:
            if not os.path.exists(source_path):
                logger.warning(f"附件不存在: {source_path}")
                return None
            
            # 生成新文件名（加上时间戳避免冲突）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = os.path.splitext(source_path)[1]
            base_name = os.path.splitext(os.path.basename(source_path))[0]
            new_filename = f"{base_name}_{timestamp}{ext}"
            
            # 复制文件
            dest_path = os.path.join(self.assets_path, new_filename)
            shutil.copy2(source_path, dest_path)
            
            logger.info(f"附件已复制: {new_filename}")
            return new_filename
            
        except Exception as e:
            logger.error(f"复制附件失败: {e}")
            return None
    
    def scan_vault_structure(self) -> Dict:
        """
        扫描Obsidian库结构
        
        Returns:
            dict: 目录结构信息
        """
        try:
            structure = {
                'folders': [],
                'notes': [],
                'total_notes': 0
            }
            
            for root, dirs, files in os.walk(self.vault_path):
                # 跳过隐藏文件夹和assets
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != self.assets_folder]
                
                # 记录文件夹
                rel_path = os.path.relpath(root, self.vault_path)
                if rel_path != '.':
                    structure['folders'].append(rel_path)
                
                # 记录markdown文件
                for file in files:
                    if file.endswith('.md'):
                        note_path = os.path.join(rel_path, file) if rel_path != '.' else file
                        structure['notes'].append(note_path)
                        structure['total_notes'] += 1
            
            logger.info(f"扫描完成: {structure['total_notes']}个笔记，{len(structure['folders'])}个文件夹")
            return structure
            
        except Exception as e:
            logger.error(f"扫描vault失败: {e}")
            return {'folders': [], 'notes': [], 'total_notes': 0}
