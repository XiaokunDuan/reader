"""
对话树数据结构和管理
"""
from datetime import datetime
from typing import List, Optional, Dict
import json
from pathlib import Path
from loguru import logger
from modules.ai_adapter import AIServiceAdapter


class QANode:
    """问答节点"""
    
    def __init__(
        self,
        question: str,
        answer: str,
        summary: str = None,
        parent: 'QANode' = None
    ):
        self.question = question
        self.answer = answer
        self.summary = summary or question[:15] + "..."
        self.timestamp = datetime.now()
        self.children: List[QANode] = []
        self.parent = parent
    
    def add_child(self, child: 'QANode'):
        """添加子节点（追问）"""
        child.parent = self
        self.children.append(child)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'question': self.question,
            'answer': self.answer,
            'summary': self.summary,
            'timestamp': self.timestamp.isoformat(),
            'children': [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: Dict, parent: 'QANode' = None) -> 'QANode':
        """从字典创建节点"""
        node = cls(
            question=data['question'],
            answer=data['answer'],
            summary=data.get('summary'),
            parent=parent
        )
        node.timestamp = datetime.fromisoformat(data['timestamp'])
        
        # 递归创建子节点
        for child_data in data.get('children', []):
            child = cls.from_dict(child_data, parent=node)
            node.children.append(child)
        
        return node
    
    def get_depth(self) -> int:
        """获取节点深度"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth


class QATree:
    """对话树"""
    
    def __init__(self):
        self.roots: List[QANode] = []
        self.current_node: Optional[QANode] = None
    
    def add_question(
        self,
        question: str,
        answer: str,
        parent: QANode = None,
        ai_adapter: AIServiceAdapter = None
    ) -> QANode:
        """
        添加问答节点
        
        Args:
            question: 问题
            answer: 回答
            parent: 父节点（追问时指定）
            ai_adapter: AI适配器（用于生成摘要）
        """
        # 生成AI摘要
        summary = self._generate_summary(question, ai_adapter)
        
        node = QANode(question, answer, summary, parent)
        
        if parent:
            parent.add_child(node)
        else:
            self.roots.append(node)
        
        self.current_node = node
        return node
    
    def _generate_summary(
        self,
        question: str,
        ai_adapter: AIServiceAdapter = None
    ) -> str:
        """生成问题摘要"""
        if not ai_adapter:
            # 没有AI适配器，使用简单截断
            return question[:15] + "..." if len(question) > 15 else question
        
        try:
            prompt = f"""请用15字以内概括这个问题的核心要点：

问题：{question}

要求：
- 简洁明了
- 突出关键词  
- 便于快速识别

只返回摘要文本，不要其他内容。"""
            
            summary = ai_adapter.call_api(prompt)
            if summary:
                # 限制长度
                summary = summary.strip()[:20]
                return summary
            else:
                return question[:15] + "..."
        except Exception as e:
            logger.warning(f"生成摘要失败: {e}")
            return question[:15] + "..."
    
    def get_all_nodes(self) -> List[QANode]:
        """获取所有节点（广度优先）"""
        nodes = []
        queue = list(self.roots)
        
        while queue:
            node = queue.pop(0)
            nodes.append(node)
            queue.extend(node.children)
        
        return nodes
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        all_nodes = self.get_all_nodes()
        
        max_depth = 0
        for node in all_nodes:
            depth = node.get_depth()
            max_depth = max(max_depth, depth)
        
        return {
            'total_questions': len(all_nodes),
            'root_questions': len(self.roots),
            'max_depth': max_depth,
            'total_followups': len(all_nodes) - len(self.roots)
        }
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'roots': [root.to_dict() for root in self.roots],
            'stats': self.get_stats()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QATree':
        """从字典创建树"""
        tree = cls()
        for root_data in data.get('roots', []):
            root = QANode.from_dict(root_data)
            tree.roots.append(root)
        return tree


class QATreeManager:
    """对话树管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def save_tree(self, tree: QATree, paper_title: str):
        """保存对话树"""
        filename = f"qa_tree_{paper_title}.json"
        filepath = self.data_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(tree.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"对话树已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存对话树失败: {e}")
    
    def load_tree(self, paper_title: str) -> Optional[QATree]:
        """加载对话树"""
        filename = f"qa_tree_{paper_title}.json"
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            logger.info(f"对话树不存在: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            tree = QATree.from_dict(data)
            logger.info(f"对话树已加载: {filepath}")
            return tree
        except Exception as e:
            logger.error(f"加载对话树失败: {e}")
            return None
    
    def list_trees(self) -> List[str]:
        """列出所有对话树"""
        trees = []
        for filepath in self.data_dir.glob("qa_tree_*.json"):
            # 提取论文标题
            title = filepath.stem.replace("qa_tree_", "")
            trees.append(title)
        return trees
