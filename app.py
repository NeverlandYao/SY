from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import os
import db_utils  # 导入数据库工具
import student_agent as sa
import data_processing as dp
# 移除未使用的绘图导入: matplotlib, seaborn, plotly
import numpy as np
# from io import BytesIO # 当前未使用
# import base64 # 当前未使用
import time
import traceback
from datetime import datetime # 添加于页脚年份

import db_utils  # 导入数据库工具
import os
app = Flask(__name__, template_folder='template')

# 全局变量
student_data = None
agent = None
system_ready = False

# --- 数据加载器初始化 ---
# 尝试初始化实际的 DataLoader
data_loader = None
# try:
#     # 假设你的实际 DataLoader 类在 .data_loader 模块中，并且需要文件路径
#     # from .data_loader import DataLoader
#     # EXCEL_FILE_PATH = os.environ.get('EXCEL_FILE_PATH', 'data/students_data.xlsx') # 从环境变量或默认路径获取文件
#     # if not os.path.exists(EXCEL_FILE_PATH):
#     #     print(f"错误: Excel 文件未找到: {EXCEL_FILE_PATH}")
#     #     # data_loader 保持 None
#     # else:
#     #     data_loader = DataLoader(EXCEL_FILE_PATH)
#     #     print("实际数据加载器初始化成功.")

# except Exception as e:
#     print(f"错误: 数据加载器初始化失败: {e}")
#     # data_loader 保持 None，这会在路由中被检查到
#     pass

# --- 类型颜色映射 (从 JS 移动以保持一致性) ---
type_color_mapping = {
    '优秀全面型': 'bg-success',
    '高压成绩型': 'bg-warning text-dark',
    '潜力型': 'bg-info text-dark',
    '警示型': 'bg-danger',
    '待分类': 'bg-secondary',
    'Excellent': 'bg-success',
    'High Pressure': 'bg-warning text-dark',
    'Potential': 'bg-info text-dark',
    'Warning': 'bg-danger',
    'Unclassified': 'bg-secondary'
}

# --- 数据映射函数 ---
def map_gender(value):
    """将性别代码映射为文本"""
    if value == 1:
        return "女"
    elif value == 2:
        return "男"
    if value is None or pd.isna(value):  # 检查 None 或 NaN (pandas可能会生成np.nan)
        return "未回答"
    return "未知"

def map_grade(value):
    """将年级代码映射为文本"""
    # 这是基于 PISA 通常情况的示例，具体需要查阅你的 Codebook
    grade_map = {
        7: "7年级", 8: "8年级", 9: "9年级", 10: "10年级",
        11: "11年级", 12: "12年级", 13: "13年级"
    }
    if value is None or pd.isna(value):
        return "未回答"
    # 使用 get 方法安全地获取映射值，如果不存在则返回默认值
    return grade_map.get(value, f"未知代码 ({value})")

def map_agreement(value):
    """将同意程度代码映射为文本"""
    agreement_map = {
        1: "非常同意",
        2: "同意",
        3: "不同意",
        4: "非常不同意"
    }
    if value is None or pd.isna(value):
         return "未回答"
    return agreement_map.get(value, "未回答或无效")


def process_student_data(student_data):
    """
    将单个学生的原始数据（字典）处理成结构化的画像数据（字典）。
    确保这里的 get() 调用使用了正确的原始字段名。
    """
    if not student_data or not isinstance(student_data, dict):
        # 这通常不应该发生，因为在路由中已经检查过 None
        return None

    processed_data = {}

    # --- 基本信息 ---
    processed_data["国际学生ID"] = student_data.get("CNTSTUID")
    processed_data["性别"] = map_gender(student_data.get("ST004D01T"))
    processed_data["学生年级"] = map_grade(student_data.get("ST001D01T"))

    # --- 学业成绩 ---
    processed_data["数学成绩 (分数)"] = student_data.get("PV1MATH")
    processed_data["阅读成绩 (分数)"] = student_data.get("PV1READ")
    processed_data["科学成绩 (分数)"] = student_data.get("PV1SCIE")

    # 计算平均成绩，只包括非 None 的分数
    scores = [
        score for score in [
            processed_data["数学成绩 (分数)"],
            processed_data["阅读成绩 (分数)"],
            processed_data["科学成绩 (分数)"]
        ] if score is not None and pd.notna(score) # 确保分数不是 NaN
    ]
    # 避免除以零错误
    processed_data["平均成绩 (分数)"] = sum(scores) / len(scores) if scores else None


    # --- 学习态度/观念 (示例) ---
    processed_data["对观点A的看法"] = map_agreement(student_data.get("ST099Q01TA"))
    processed_data["对观点B的看法"] = map_agreement(student_data.get("ST099Q02TA"))
    processed_data["对观点C的看法"] = map_agreement(student_data.get("ST099Q03TA"))
    processed_data["对观点D的看法"] = map_agreement(student_data.get("ST099Q04TA"))

    # --- 其他可能感兴趣的维度 ---
    # 示例：家庭背景、学习资源、幸福感等，根据可用字段添加
    # processed_data["家庭经济社会文化地位指数"] = student_data.get("ESCS")
    # processed_data["是否有自己的书桌"] = map_yes_no(student_data.get("ST011Q01TA"))
    # processed_data["学校归属感"] = student_data.get("BELONG")

    return processed_data

# --- 初始化 ---
def initialize_system():
    global student_data, agent, system_ready, data_loader

    db_utils.create_database()
    db_utils.create_students_table()
    db_utils.create_recommendations_table()

    try:
        data_file_path = 'student_profiles.csv'
        excel_file_path = 'Model_py.xlsx'

        if os.path.exists(data_file_path):
            student_data = pd.read_csv(data_file_path)
            print(f"Loaded processed data from {data_file_path}, {len(student_data)} records.")
        # elif os.path.exists(excel_file_path):
            print(f"Processing raw data from {excel_file_path}...")
            raw_data = dp.load_data(excel_file_path)
            if raw_data is None:
                raise ValueError("Failed to load raw data.")
            clean_data = dp.clean_data(raw_data)
            if clean_data is None:
                raise ValueError("Failed to clean data.")
            processed_data = dp.calculate_dimensions(clean_data)
            if processed_data is None:
                raise ValueError("Failed to calculate dimensions.")
            student_data = dp.identify_student_types(processed_data)
            if student_data is None:
                raise ValueError("Failed to identify student types.")

            # 确保 student_id 存在于处理后
            if 'student_id' not in student_data.columns:
                student_data['student_id'] = range(1, len(student_data) + 1)

            student_data.to_csv(data_file_path, index=False)
            print(f"数据处理完成，已保存到 {data_file_path}")
        else:
            print(f"错误: 未找到 {data_file_path} 或 {excel_file_path}。")
            system_ready = False
            return False  # 指示失败
        student_data['student_id'] = student_data['CNTSTUID']
        # print(student_data)
        # 确保 student_id 即使从没有它的 CSV 加载也存在
        if 'student_id' not in student_data.columns:
            print("警告: CSV 中缺少 'student_id' 列，生成序列 ID。")
            student_data['student_id'] = range(1, len(student_data) + 1)
        else:
            # 确保 student_id 是整数类型
            student_data['student_id'] = student_data['student_id'].astype(int)

        # 初始化学生代理
        agent = sa.StudentAgent(data_file_path)
        print("学生代理初始化完成")
        system_ready = True
        return True

    except Exception as e:
        print(f"系统初始化失败: {e}")
        traceback.print_exc()
        system_ready = False
        return False

# 启动时初始化
db_utils.create_database()
db_utils.create_students_table()
db_utils.create_recommendations_table()
initialize_system()

# --- 路由 ---
@app.route('/')
def index():
    """渲染主仪表板页面。"""
    global student_data, system_ready, data_loader

    if not system_ready:
        return render_template('error.html', message="系统初始化失败，请检查控制台输出。")

    # if data_loader is None: # 移除此检查，因为student_data是主数据源
    #     return jsonify({
    #         "status": "API 运行中",
    #         "data_loader_status": "数据加载器初始化失败",
    #         "message": "访问 /api/students 获取所有学生数据 或 /api/students/<student_id> 获取单个学生数据"
    #     })

    # 准备概述部分的数据
    students_list = []
    dimension_cols = ['知识维度_综合得分', '认知维度_综合得分', '情感维度_综合得分', '行为维度_综合得分']
    valid_dimension_cols = [col for col in dimension_cols if col in student_data.columns]

    if student_data is not None:
        # print(student_data)
        for _, row in student_data.iterrows():
            student_dict = {
                'student_id': int(row['student_id']),
                'student_type': row.get('学生类型', '待分类'),
                'knowledge_score': row.get('知识维度_综合得分'),
                'cognitive_score': row.get('认知维度_综合得分'),
                'affective_score': row.get('情感维度_综合得分'),
                'behavioral_score': row.get('行为维度_综合得分')

            }
            students_list.append(student_dict)
    else:
        students_list = [] # 如果 student_data 为 None，则初始化为空列表

    return render_template('index.html', students=students_list)


@app.route('/api/student/<int:student_id>')
def get_student_basic_data(student_id):
    """API endpoint to get basic data and detailed metrics for a single student."""
    global student_data, system_ready

    if not system_ready or student_data is None:
        return jsonify({"error": "System not ready"}), 500

    # 验证 student_id
    if student_id not in student_data['student_id'].values:
        return jsonify({"error": f"找不到学生ID {student_id}"}), 404

    try:
        # 1. 从 DataFrame 获取基本信息和详细指标
        student_row = student_data[student_data['student_id'] == student_id].iloc[0]
        detail_metrics = []
        for col in student_row.index:
            # 包括具有下划线但不属于主要维度分数或 ID/Type 的列
            if '_' in col and '综合得分' not in col and col not in ['student_id', '学生类型']:
                value = student_row[col]
                if pd.notna(value):
                    # 尝试四舍五入（如果为数字），否则保持原样
                    try:
                        value = round(float(value), 2)
                    except (ValueError, TypeError):
                        pass  # 如果不是 float/int，则保留原始值
                    detail_metrics.append({'name': col, 'value': value})

        # --- 合并为一个响应对象 ---
        response_data = {
            "student_id": int(student_row.get('student_id')),
            "student_type": student_row.get('学生类型', '待分类'),
            # 将分数缩放到 0-100 以用于前端
            "knowledge_score": int(student_row.get('知识维度_综合得分', 0) * 100) if pd.notna(student_row.get('知识维度_综合得分')) else 0,
            "cognitive_score": int(student_row.get('认知维度_综合得分', 0) * 100) if pd.notna(student_row.get('认知维度_综合得分')) else 0,
            "affective_score": int(student_row.get('情感维度_综合得分', 0) * 100) if pd.notna(student_row.get('情感维度_综合得分')) else 0,
            "behavioral_score": int(student_row.get('行为维度_综合得分', 0) * 100) if pd.notna(student_row.get('行为维度_综合得分')) else 0,
            "detail_metrics": detail_metrics,
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"获取学生基本数据出错: {e}")
        traceback.print_exc()
        return jsonify({"error": f"无法获取学生 {student_id} 的基本数据: {str(e)}"}), 500

@app.route('/api/student/<int:student_id>/details')
def get_student_details(student_id):
    """API endpoint to get detailed analysis, recommendations, etc. for a single student."""
    global student_data, agent, system_ready

    if not system_ready or agent is None or student_data is None:
        return jsonify({"error": "System not ready"}), 500

    # 验证 student_id
    if student_id not in student_data['student_id'].values:
        return jsonify({"error": f"找不到学生ID {student_id}"}), 404

    try:
        # --- 获取详细数据组件 ---
        # 1. 基本分析（包括 0-1 范围内的分数和专家诊断）
        analysis = agent.analyze_student(student_id)
        if not analysis:  # analyze_student 可能返回 None 如果 ID 最初无效（双重检查）
            return jsonify({"error": f"无法分析学生 {student_id}"}), 500

        # 2. 推荐
        recommendations = agent.generate_recommendations(student_id)

        # 3. 干预计划 (如果已实现)
        # intervention_plan = agent.generate_intervention_plan(student_id)

        # 4. 学习资源 (如果已实现)
        # learning_resources = agent.generate_learning_resources(student_id)

        # --- 合并为一个响应对象 ---
        response_data = {
            "student_id": analysis.get('student_id'),
            "expert_diagnosis": analysis.get('expert_diagnosis', '暂无分析'),
            "recommendations": recommendations,
            # "intervention_plan": intervention_plan,
            # "learning_resources": learning_resources
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"获取学生详细数据出错: {e}")
        traceback.print_exc()
        return jsonify({"error": f"无法获取学生 {student_id} 的详细数据: {str(e)}"}), 500


# 移除旧的 /student/<id> 和 /api/recommendations/<id> 路由
# 简单的错误模板路由（可选，但建议使用）
@app.route('/error')
def error_page():
    message = request.args.get('message', '发生意外错误。')
    return render_template('error.html', message=message)

# --- Flask 路由 ---
#-------------------

@app.route('/api/students/', methods=['GET'])
def get_all_students():
    """
    获取所有学生的处理后数据列表。
    注意：对于大型数据集，直接返回全部数据可能不是最佳实践，
    可以考虑分页或流式传输。
    """
    global student_data

    if student_data is None:
        return jsonify({"error": "Backend service not ready, student data failed to load."}), 500

    try:
        # 直接从 student_data DataFrame 获取数据，并转换为字典列表
        students_list = []
        for _, row in student_data.iterrows():
            student = {
                'student_id': int(row['student_id']),
                'student_type': row.get('学生类型', '待分类'),
                'knowledge_score': row.get('知识维度_综合得分'),
                'cognitive_score': row.get('认知维度_综合得分'),
                'affective_score': row.get('情感维度_综合得分'),
                'behavioral_score': row.get('行为维度_综合得分')
            }
            students_list.append(student)
        return jsonify(students_list)

    except Exception as e:
        print(f"获取所有学生数据时发生错误: {e}")
        return jsonify({"error": "处理学生数据时发生内部错误", "details": str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student_by_id(student_id):
    """
    根据学生ID获取单个学生的处理后数据。
    """
    global student_data

    if student_data is None:
        return jsonify({"error": "Backend service not ready, student data failed to load."}), 500

    try:
        # 从 student_data DataFrame 中筛选学生数据
        student = student_data[student_data['student_id'] == student_id].iloc[0].to_dict()
        if not student:
            return jsonify({"message": f"未找到学生ID: {student_id}"}), 404

        # 从 student_data DataFrame 中筛选学生数据
        student_row = student_data[student_data['student_id'] == student_id].iloc[0]

        # 确保所有需要的分数都存在
        knowledge_score = student_row.get('知识维度_综合得分', None)
        cognitive_score = student_row.get('认知维度_综合得分', None)
        affective_score = student_row.get('情感维度_综合得分', None)
        behavioral_score = student_row.get('行为维度_综合得分', None)

        student = {
            "国际学生ID": int(student_row["student_id"]),
            "学生年级": student_row["学生类型"] if "学生类型" in student_row else "待分类",
            "平均成绩 (分数)": student_row["平均成绩 (分数)"] if "平均成绩 (分数)" in student_row else None,
            "数学成绩 (分数)": student_row["数学成绩 (分数)"] if "数学成绩 (分数)" in student_row else None,
            "科学成绩 (分数)": student_row["科学成绩 (分数)"] if "科学成绩 (分数)" in student_row else None,
            "阅读成绩 (分数)": student_row["阅读成绩 (分数)"] if "阅读成绩 (分数)" in student_row else None,
            "knowledge_score": float(knowledge_score) if knowledge_score is not None else None,
            "cognitive_score": float(cognitive_score) if cognitive_score is not None else None,
            "affective_score":  float(affective_score) if affective_score is not None else None,
            "behavioral_score": float(behavioral_score) if behavioral_score is not None else None
        }
        return jsonify(student)

    except IndexError: #  处理 student_id 不存在的情况
        return jsonify({"message": f"未找到学生ID: {student_id}"}), 404
    except Exception as e:
        print(f"获取学生ID {student_id} 数据时发生错误: {e}")
        return jsonify({"error": "获取学生数据时发生内部错误", "details": str(e)}), 500

@app.route('/api/student/<int:student_id>/plan', methods=['GET'])
def get_student_plan(student_id):
    """API endpoint to get personalized advice for a single student."""
    global agent, system_ready, student_data

    if not system_ready or agent is None or student_data is None:
        return jsonify({"error": "System not ready or agent not initialized"}), 500

    # 验证 student_id
    if student_id not in student_data['student_id'].values:
        return jsonify({"error": f"找不到学生ID {student_id}"}), 404

    try:
        # 调用 StudentAgent 生成建议
        advice = agent.generate_recommendations(student_id)
        if advice.get("error"):
             return jsonify(advice), 500

        return jsonify(advice)

    except Exception as e:
        print(f"获取学生计划出错: {e}")
        traceback.print_exc()
        return jsonify({"error": f"无法获取学生 {student_id} 的计划: {str(e)}"}), 500

if __name__ == '__main__':
    # 设置 host='0.0.0.0' 以使其可在网络上访问（如果需要）
    app.run(debug=True, host='0.0.0.0', port=5010)
