"""
问题模板管理系统
"""
from typing import List, Dict, Optional
from pathlib import Path
import yaml
from loguru import logger


class QuestionTemplate:
    """问题模板"""
    
    def __init__(
        self,
        name: str,
        description: str,
        questions: List[str],
        category: str = "general",
        tags: List[str] = None,
        variables: List[str] = None
    ):
        self.name = name
        self.description = description
        self.questions = questions
        self.category = category
        self.tags = tags or []
        self.variables = variables or []
    
    def apply(self, context: Dict[str, str] = None) -> List[str]:
        """
        应用模板，替换变量
        
        Args:
            context: 变量上下文，如 {"paper_title": "Attention Is All You Need"}
        
        Returns:
            替换后的问题列表
        """
        if not context:
            return self.questions.copy()
        
        applied_questions = []
        for question in self.questions:
            # 替换变量
            for var, value in context.items():
                question = question.replace(f"{{{var}}}", value)
            applied_questions.append(question)
        
        return applied_questions
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            'questions': self.questions,
            'category': self.category,
            'tags': self.tags,
            'variables': self.variables
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QuestionTemplate':
        """从字典创建模板"""
        return cls(
            name=data['name'],
            description=data['description'],
            questions=data['questions'],
            category=data.get('category', 'general'),
            tags=data.get('tags', []),
            variables=data.get('variables', [])
        )


class TemplateManager:
    """模板管理器"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.custom_dir = self.templates_dir / "custom"
        self.custom_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, QuestionTemplate] = {}
        self._load_all_templates()
    
    def _load_all_templates(self):
        """加载所有模板"""
        # 加载预设模板
        for template_file in self.templates_dir.glob("*.yaml"):
            if template_file.parent == self.templates_dir:  # 只加载根目录的
                self._load_template(template_file)
        
        # 加载自定义模板
        for template_file in self.custom_dir.glob("*.yaml"):
            self._load_template(template_file)
        
        logger.info(f"已加载 {len(self.templates)} 个模板")
    
    def _load_template(self, template_path: Path):
        """加载单个模板"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            template = QuestionTemplate.from_dict(data)
            self.templates[template.name] = template
            logger.debug(f"加载模板: {template.name}")
        except Exception as e:
            logger.error(f"加载模板失败 {template_path}: {e}")
    
    def get_template(self, name: str) -> Optional[QuestionTemplate]:
        """获取模板"""
        return self.templates.get(name)
    
    def list_templates(self, category: str = None) -> List[QuestionTemplate]:
        """
        列出所有模板
        
        Args:
            category: 按分类筛选
        """
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def create_template(
        self,
        name: str,
        description: str,
        questions: List[str],
        category: str = "custom",
        tags: List[str] = None
    ) -> QuestionTemplate:
        """
        创建自定义模板
        
        Args:
            name: 模板名称
            description: 描述
            questions: 问题列表
            category: 分类
            tags: 标签
        
        Returns:
            创建的模板
        """
        template = QuestionTemplate(
            name=name,
            description=description,
            questions=questions,
            category=category,
            tags=tags or []
        )
        
        # 保存到自定义目录
        self._save_template(template, is_custom=True)
        
        # 添加到缓存
        self.templates[name] = template
        
        logger.info(f"创建自定义模板: {name}")
        return template
    
    def _save_template(self, template: QuestionTemplate, is_custom: bool = True):
        """保存模板到文件"""
        if is_custom:
            template_path = self.custom_dir / f"{template.name}.yaml"
        else:
            template_path = self.templates_dir / f"{template.name}.yaml"
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(template.to_dict(), f, allow_unicode=True, sort_keys=False)
            logger.debug(f"模板已保存: {template_path}")
        except Exception as e:
            logger.error(f"保存模板失败: {e}")
    
    def delete_template(self, name: str) -> bool:
        """删除自定义模板"""
        if name not in self.templates:
            return False
        
        template = self.templates[name]
        if template.category != "custom":
            logger.warning(f"无法删除预设模板: {name}")
            return False
        
        # 删除文件
        template_path = self.custom_dir / f"{name}.yaml"
        if template_path.exists():
            template_path.unlink()
        
        # 从缓存删除
        del self.templates[name]
        
        logger.info(f"已删除模板: {name}")
        return True
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set(t.category for t in self.templates.values())
        return sorted(categories)
