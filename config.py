import os
from dotenv import load_dotenv

load_dotenv()

# 中文字体映射（原data.py中的label_map全局化）
LABEL_MAP = {
    '知识维度_综合得分': 'Knowledge',
    '认知维度_综合得分': 'Cognition', 
    '情感维度_综合得分': 'Affection',
    '行为维度_综合得分': 'Behavior',
    '学生类型': 'Student Type',
    '优秀全面型': 'Excellent',
    '高压成绩型': 'High Pressure',
    '潜力型': 'Potential',
    '警示型': 'Warning',
    '待分类': 'Unclassified',
    '知识维度_学科成绩': 'Academic Performance',
    '知识维度_问题解决': 'Problem Solving',
    '知识维度_学习资源': 'Learning Resources',
    '认知维度_任务坚持': 'Task Persistence',
    '认知维度_批判思考': 'Critical Thinking',
    '认知维度_注意力': 'Attention',
    '情感维度_数学焦虑': 'Math Anxiety',
    '情感维度_学校归属感': 'School Belonging',
    '情感维度_学习动机': 'Learning Motivation',
    '行为维度_数字资源使用': 'Digital Resource Usage',
    '行为维度_出勤情况': 'Attendance'
}

# 智能体配置
MODELSCOPE_CONFIG = {
    'base_url': 'https://api-inference.modelscope.cn/v1/',
    'api_key': os.getenv('MODELSCOPE_API_KEY'),
    'model_id': 'Qwen/Qwen3-32B'
}

# 可视化配置
VISUAL_STYLE = {
    'radar_colors': ['#1f77b4', '#ff7f0e'],
    'font_sizes': {'title': 14, 'labels': 10},
    'dimension_order': ['知识', '认知', '情感', '行为', '创新', '协作']
}

# 数据库配置
db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'student_portrait_system')
}
