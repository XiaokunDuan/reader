"""
阅读统计模块
"""
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from pathlib import Path
import json
from loguru import logger
from collections import defaultdict


class PaperSession:
    """单次阅读会话"""
    
    def __init__(
        self,
        paper_title: str,
        file_type: str = "document",
        questions: int = 0,
        start_time: datetime = None
    ):
        self.paper_title = paper_title
        self.file_type = file_type
        self.questions = questions
        self.start_time = start_time or datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration: Optional[timedelta] = None
    
    def finish(self):
        """结束会话"""
        self.end_time = datetime.now()
        self.duration = self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        return {
            'paper_title': self.paper_title,
            'file_type': self.file_type,
            'questions': self.questions,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration.total_seconds() if self.duration else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PaperSession':
        session = cls(
            paper_title=data['paper_title'],
            file_type=data.get('file_type', 'document'),
            questions=data['questions'],
            start_time=datetime.fromisoformat(data['start_time'])
        )
        if data.get('end_time'):
            session.end_time = datetime.fromisoformat(data['end_time'])
            session.duration = timedelta(seconds=data['duration_seconds'])
        return session


class ReadingStats:
    """阅读统计"""
    
    def __init__(self, stats_file: str = "data/reading_stats.json"):
        self.stats_file = Path(stats_file)
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.sessions: List[PaperSession] = []
        self.current_session: Optional[PaperSession] = None
        
        self._load_stats()
    
    def _load_stats(self):
        """加载统计数据"""
        if not self.stats_file.exists():
            return
        
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.sessions = [
                PaperSession.from_dict(s) for s in data.get('sessions', [])
            ]
            logger.info(f"已加载 {len(self.sessions)} 条阅读记录")
        except Exception as e:
            logger.error(f"加载统计数据失败: {e}")
    
    def _save_stats(self):
        """保存统计数据"""
        try:
            data = {
                'sessions': [s.to_dict() for s in self.sessions],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug("统计数据已保存")
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")
    
    def start_session(self, paper_title: str, file_type: str = "document"):
        """开始新会话"""
        self.current_session = PaperSession(
            paper_title=paper_title,
            file_type=file_type
        )
        logger.info(f"开始阅读会话: {paper_title}")
    
    def add_question(self):
        """记录一个问题"""
        if self.current_session:
            self.current_session.questions += 1
    
    def end_session(self):
        """结束当前会话"""
        if self.current_session:
            self.current_session.finish()
            self.sessions.append(self.current_session)
            self._save_stats()
            logger.info(f"会话结束: {self.current_session.paper_title}, "
                       f"问题数: {self.current_session.questions}, "
                       f"时长: {self.current_session.duration}")
            self.current_session = None
    
    def get_total_papers(self) -> int:
        """获取总论文数"""
        return len(self.sessions)
    
    def get_total_questions(self) -> int:
        """获取总问题数"""
        return sum(s.questions for s in self.sessions)
    
    def get_total_time(self) -> timedelta:
        """获取总阅读时间"""
        total = timedelta()
        for s in self.sessions:
            if s.duration:
                total += s.duration
        return total
    
    def get_papers_by_date(self) -> Dict[date, List[str]]:
        """按日期统计论文"""
        papers_by_date = defaultdict(list)
        for s in self.sessions:
            day = s.start_time.date()
            papers_by_date[day].append(s.paper_title)
        return dict(papers_by_date)
    
    def get_file_type_distribution(self) -> Dict[str, int]:
        """文件类型分布"""
        distribution = defaultdict(int)
        for s in self.sessions:
            distribution[s.file_type] += 1
        return dict(distribution)
    
    def get_recent_sessions(self, days: int = 7) -> List[PaperSession]:
        """获取最近N天的会话"""
        cutoff = datetime.now() - timedelta(days=days)
        return [s for s in self.sessions if s.start_time > cutoff]
    
    def generate_summary(self) -> Dict:
        """生成统计摘要"""
        recent = self.get_recent_sessions(7)
        
        return {
            'total_papers': self.get_total_papers(),
            'total_questions': self.get_total_questions(),
            'total_time': str(self.get_total_time()),
            'papers_this_week': len(recent),
            'questions_this_week': sum(s.questions for s in recent),
            'file_types': self.get_file_type_distribution(),
            'avg_questions_per_paper': (
                self.get_total_questions() / self.get_total_papers()
                if self.get_total_papers() > 0 else 0
            )
        }
    
    def export_csv(self, output_path: str):
        """导出为CSV"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Paper Title', 'File Type', 'Questions',
                'Start Time', 'Duration (minutes)'
            ])
            
            for s in self.sessions:
                duration_minutes = (
                    s.duration.total_seconds() / 60
                    if s.duration else 0
                )
                writer.writerow([
                    s.paper_title,
                    s.file_type,
                    s.questions,
                    s.start_time.strftime('%Y-%m-%d %H:%M'),
                    f"{duration_minutes:.1f}"
                ])
        
        logger.info(f"统计数据已导出: {output_path}")
