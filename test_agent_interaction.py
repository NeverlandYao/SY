import sys
import os
import json
import time
from student_agent import StudentAgent

# Redirect stdout to capture logs nicely if needed, but for now just print
def log_step(step, agent_name, action, content):
    print(f"STEP_START|{step}|{agent_name}|{action}")
    print(f"CONTENT_START\n{content}\nCONTENT_END")
    print(f"STEP_END")

def run_experiment():
    print("Initializing StudentAgent...")
    try:
        agent = StudentAgent('student_profiles.csv')
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    student_id = 34400004
    print(f"Starting Collaborative Reasoning Experiment for Student {student_id}")

    # Verify student exists
    if student_id not in agent.data['CNTSTUID'].values:
        print(f"Student {student_id} not found!")
        return
    
    # Get student basic analysis first to pass to agents
    # We can reuse the logic from analyze_student to get the 'analysis' dict
    # But analyze_student prints a lot. We'll just extract the data preparation part.
    
    student_data = agent.data[agent.data['CNTSTUID'] == student_id]
    
    # Construct analysis dict manually to avoid running the full default analysis
    analysis = {
        'student_id': int(student_id),
        'knowledge_score': student_data['知识维度_综合得分'].values[0] if '知识维度_综合得分' in student_data.columns else 0.5,
        'cognitive_score': student_data['认知维度_综合得分'].values[0] if '认知维度_综合得分' in student_data.columns else 0.5,
        'affective_score': student_data['情感维度_综合得分'].values[0] if '情感维度_综合得分' in student_data.columns else 0.5,
        'behavioral_score': student_data['行为维度_综合得分'].values[0] if '行为维度_综合得分' in student_data.columns else 0.5,
        'student_type': student_data['学生类型'].values[0] if '学生类型' in student_data.columns else "未分类"
    }
    
    detail_metrics = [
            '知识维度_学科成绩', '知识维度_问题解决', '知识维度_学习资源',
            '认知维度_任务坚持', '认知维度_批判思考', '认知维度_注意力',
            '情感维度_数学焦虑', '情感维度_学校归属感', '情感维度_学习动机',
            '行为维度_数字资源使用', '行为维度_出勤情况'
    ]
    for metric in detail_metrics:
        if metric in student_data.columns:
            metric_key = metric.replace('维度_', '_')
            analysis[metric_key] = student_data[metric].values[0]
            
    student_json = json.dumps(analysis, ensure_ascii=False, indent=2)

    # --- Step 1: Central Controller (Simulated) schedules Profile Agent ---
    log_step("Step 1", "中心控制器", "调度", "检测到Cluster B类型学生输入，调度'学生画像智能体'进行全维画像构建。")
    
    query_profile = f"请根据以下数据生成学生画像，重点分析其'高压成绩型'特征：\n{student_json}"
    response_profile = agent._consult_expert("学生画像智能体", query_profile)['response']
    log_step("Step 1-Result", "学生画像智能体", "生成画像", response_profile)

    # --- Step 2: Academic Expert proposes Advancement ---
    log_step("Step 2", "中心控制器", "调度", "基于画像结果，调度'学科教学专家'制定提升方案。")
    
    query_academic = f"基于学生画像：\n{response_profile}\n\n该学生成绩优秀但压力大。请提出针对性的学科提升（提优）建议。请明确具体的学习目标和高难度任务。"
    response_academic = agent._consult_expert("学科教学专家", query_academic)['response']
    log_step("Step 2-Result", "学科教学专家", "提优建议", response_academic)

    # --- Step 3: Psychology Expert proposes Burden Reduction ---
    log_step("Step 3", "中心控制器", "调度", "监测到高压力风险，并发调度'教育心理咨询师'进行风险干预。")
    
    query_psych = f"基于学生画像：\n{response_profile}\n\n该学生存在高压力风险。请提出具体的减负和心理疏导建议。请强调减少作业量和降低期望值。"
    response_psych = agent._consult_expert("教育心理咨询师", query_psych)['response']
    log_step("Step 3-Result", "教育心理咨询师", "减负建议", response_psych)

    # --- Step 4: Conflict Resolution by AI Education Expert (Coordinator) ---
    log_step("Step 4", "中心控制器", "冲突检测与协调", "检测到'学科教学专家'（增加负荷）与'教育心理咨询师'（减少负荷）建议存在目标冲突。调度'教育人工智能专家'进行多目标优化决策。")
    
    query_conflict = (
        f"当前存在决策冲突：\n"
        f"1. 学科专家建议：{response_academic}\n"
        f"2. 心理专家建议：{response_psych}\n\n"
        f"请作为决策核心，综合考虑'高压成绩型'学生的特点，依据'风险优先协议'（即心理健康风险高于学业提升），"
        f"给出一个平衡的最终实施方案。说明你是如何调整两者权重的。"
    )
    response_final = agent._consult_expert("教育人工智能专家", query_conflict)['response']
    log_step("Step 4-Result", "教育人工智能专家", "最终决策", response_final)

if __name__ == "__main__":
    run_experiment()
