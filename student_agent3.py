import pandas as pd
import numpy as np
from openai import OpenAI
import json
import time
from config import MODELSCOPE_CONFIG  # 导入配置


class StudentAgent:
    """学生智能代理系统，集成大模型能力的教育智能体网络"""

    def __init__(self, data_path):
        """初始化学生代理系统

        Args:
            data_path: 学生数据文件路径
        """
        # 初始化数据
        self.data = pd.read_csv(data_path)
        self.student_profiles = {}

        # 检查是否有CNTSTUID列，如果没有，抛出异常
        if 'CNTSTUID' not in self.data.columns:
            raise ValueError("数据中未找到CNTSTUID列")

        # 初始化大模型客户端 using config
        self.client = OpenAI(
            api_key=MODELSCOPE_CONFIG['api_key'],
            base_url=MODELSCOPE_CONFIG['base_url']
        )

        # 定义专家智能体系统
        self.expert_agents = {
            "学生画像智能体": {
                "role": "你是一位专业的学生画像分析师，擅长根据学生的学习数据和多维度得分，运用大语言模型生成全面、深入的学生画像。",
                "responsibility": "分析学生的知识、认知、情感、行为等维度得分及相关数据，生成个性化的学生画像报告。"
            },
            "教育诊断专家": {
                "role": "你是一位拥有20年经验的教育诊断专家，精通学习分析、教育测量与评估。你擅长从学生数据中发现潜在问题和优势，并提供深入的分析观点.",
                "responsibility": "分析学生的学习数据，识别优势和不足，提供专业的诊断报告"
            },
            "学科教学专家": {
                "role": "你是一位资深的学科教学专家，熟悉各学科的核心知识体系和学习难点，精通不同认知水平的教学策略。你拥有丰富的教学经验和学科专业知识.",
                "responsibility": "根据学生在知识维度的表现，提供针对性的学科学习建议和资源推荐"
            },
            "认知心理学家": {
                "role": "你是一位认知心理学家，精通思维过程、元认知策略、注意力和记忆力训练。你了解不同认知能力的发展规律和提升方法.",
                "responsibility": "分析学生的认知特点，提供认知能力培养和思维方式优化的专业建议"
            },
            "教育心理咨询师": {
                "role": "你是一位专业的教育心理咨询师，擅长情绪管理、动机激发和心理健康促进。你熟悉青少年心理发展规律和常见情绪问题的干预方法.",
                "responsibility": "关注学生的情感状态，提供情绪管理、压力应对和心理健康建议"
            },
            "学习行为指导专家": {
                "role": "你是一位学习行为指导专家，精通习惯养成、时间管理和自我调节学习策略。你擅长设计行为干预计划和激励机制.",
                "responsibility": "根据学生的行为模式，提供习惯培养、行为改变和学习环境优化的具体策略"
            },
            "教育人工智能专家": {
                "role": "你是一位教育人工智能专家，精通个性化学习系统、自适应学习技术和数字教育资源。你了解如何利用技术提升学习效果.",
                "responsibility": "整合各专家的建议，设计系统性的智能干预方案，并推荐适合的数字化学习资源和工具"
            }
        }

        # 教育理论知识库
        self.education_theories = {
            "bloom_taxonomy": ["记忆", "理解", "应用", "分析", "评价", "创造"],
            "learning_styles": ["视觉型", "听觉型", "动觉型"],
            "multiple_intelligence": ["语言智能", "逻辑-数学智能", "空间智能", "音乐智能",
                                     "身体-动觉智能", "人际智能", "内省智能", "自然探索智能"],
            "self_determination": ["自主性", "胜任感", "关联性"],
            "growth_mindset": ["努力", "挑战", "反馈", "策略", "坚持"]
        }

        print("学生智能代理系统初始化完成，集成了6位专业教育智能体")
        # print(self.data.head())

    def analyze_student(self, student_id):
        """分析特定学生的数据并生成个性化评估"""
        # 验证学生ID是否在有效范围内
        if student_id not in self.data['CNTSTUID'].values:
            print(f"错误: 找不到ID为 {student_id} 的学生")
            print(f"有效的学生ID范围: {min(self.data['CNTSTUID'])}-{max(self.data['CNTSTUID'])}")
            return None

        student_data = self.data[self.data['CNTSTUID'] == student_id]

        # 检查必要的列是否存在
        required_columns = ['知识维度_综合得分', '认知维度_综合得分', '情感维度_综合得分', '行为维度_综合得分', '学生类型']
        missing_columns = [col for col in required_columns if col not in student_data.columns]

        if missing_columns:
            print(f"警告: 以下必要列缺失: {missing_columns}")
            print("可用的列: ", student_data.columns.tolist())
            # 为缺失的列创建默认值
            for col in missing_columns:
                if col == '学生类型':
                    student_data[col] = "未分类"
                else:
                    student_data[col] = 0.5  # 默认中等水平

        # 基础分析
        analysis = {
            'student_id': student_id,
            'knowledge_score': student_data['知识维度_综合得分'].values[0] if '知识维度_综合得分' in student_data.columns else 0.5,
            'cognitive_score': student_data['认知维度_综合得分'].values[0] if '认知维度_综合得分' in student_data.columns else 0.5,
            'affective_score': student_data['情感维度_综合得分'].values[0] if '情感维度_综合得分' in student_data.columns else 0.5,
            'behavioral_score': student_data['行为维度_综合得分'].values[0] if '行为维度_综合得分' in student_data.columns else 0.5,
            'student_type': student_data['学生类型'].values[0] if '学生类型' in student_data.columns else "未分类"
        }

        # 获取更详细的指标
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

        # 让学生画像智能体生成学生画像
        try:
            profile_analysis_query = (
                f"请根据以下学生的学习数据和维度得分，生成一份详细的学生画像报告：\n"
                f"{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
                f"请在画像中整合知识、认知、情感、行为四个维度的分析，突出学生的特点、优势和潜在问题。报告应结构清晰，语言专业但易于理解。"
            )
            student_profile_report = self._consult_expert("学生画像智能体", profile_analysis_query)
            analysis['student_profile_report'] = student_profile_report
        except Exception as e:
            print(f"学生画像智能体分析出错: {e}")
            analysis['student_profile_report'] = "无法生成学生画像报告"

        # 让教育诊断专家进行深度分析
        try:
            expert_analysis = self._consult_expert(
                "教育诊断专家",
                f"我需要你分析一位学生的学习情况，以下是该学生的数据：\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
                f"请你详细分析这位学生的特点、优势、不足和发展方向。请关注以下维度：知识维度、认知维度、情感维度和行为维度."
            )
            analysis['expert_diagnosis'] = expert_analysis
        except Exception as e:
            print(f"教育诊断专家分析出错: {e}")
            analysis['expert_diagnosis'] = "无法获取专家分析"

        # 保存分析结果
        self.student_profiles[student_id] = analysis
        # analysis.pop('expert_diagnosis', None)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        return analysis

    def _consult_expert(self, expert_name, query, model="Qwen/Qwen2.5-7B-Instruct-1M"):
        """咨询特定领域的专家智能体

        Args:
            expert_name: 专家名称
            query: 查询内容
            model: 使用的模型ID

        Returns:
            str: 专家意见
        """
        if expert_name not in self.expert_agents:
            raise ValueError(f"未知的专家: {expert_name}")

        expert = self.expert_agents[expert_name]

        print(f"正在咨询{expert_name}...")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        'role': 'system',
                        'content': f"{expert['role']}\n\n你的职责：{expert['responsibility']}\n\n"
                                   f"请提供专业、深入、具体且可操作的建议。请基于教育学、心理学等相关理论进行分析, 同时考虑实际应用价值。回答应结构清晰，语言专业但易于理解."
                    },
                    {
                        'role': 'user',
                        'content': query
                    }
                ],
                stream=True
            )

            answer = ""
            done_reasoning = False

            for chunk in response:
                try:
                    reasoning_chunk = chunk.choices[0].delta.reasoning_content or ""
                    answer_chunk = chunk.choices[0].delta.content or ""

                    if reasoning_chunk:
                        print(reasoning_chunk, end='', flush=True)
                    elif answer_chunk:
                        if not done_reasoning:
                            print('\n\n === 专家回答 ===\n')
                            done_reasoning = True
                        answer += answer_chunk
                except Exception as e:
                    # 处理流式输出中可能的错误
                    continue

            print(f"\n{expert_name}已完成分析")
            return answer

        except Exception as e:
            print(f"咨询专家时出错: {e}")
            return f"咨询{expert_name}失败: {str(e)}"

    def generate_recommendations(self, student_id):
        """使用多专家系统为学生生成个性化学习建议

        Args:
            student_id: 学生ID

        Returns:
            dict: 包含多个维度的专家建议
        """
        if student_id not in self.student_profiles:
            self.analyze_student(student_id)

        if student_id not in self.student_profiles:
            return {"error": "无法获取学生数据"}

        profile = self.student_profiles[student_id]

        # 创建分维度的建议结构
        recommendations = {
            "总体评估": [],
            "知识维度": [],
            "认知维度": [],
            "情感维度": [],
            "行为维度": [],
            "学习策略": [],
            "教师支持": [],
            "家庭支持": []
        }

        # 执行多专家协作工作流
        try:
            # 1. 学科教学专家提供知识维度建议
            knowledge_query = (
                f"学生ID {student_id} 的知识维度得分为 {profile['knowledge_score']:.2f}/1.0\n"
                f"学生类型: {profile['student_type']}。\n"
            )

            # 添加详细指标（如果有）
            detail_keys = [k for k in profile.keys() if k.startswith('知识_')]
            for k in detail_keys:
                knowledge_query += f"{k}: {profile[k]:.2f}\n"

            knowledge_query += f"\\n请针对这位学生的知识维度情况，提供1-2条具体、可操作的学习建议. 每条建议需包含具体方法、预期效果和理论依据."

            knowledge_recs = self._consult_expert("学科教学专家", knowledge_query)
            recommendations["知识维度"] = self._parse_recommendations(knowledge_recs)

            # 2. 认知心理学家提供认知维度建议
            cognitive_query = (
                f"学生ID {student_id} 的认知维度得分为 {profile['cognitive_score']:.2f}/1.0\n"
                f"学生类型: {profile['student_type']}。\n"
            )

            detail_keys = [k for k in profile.keys() if k.startswith('认知_')]
            for k in detail_keys:
                cognitive_query += f"{k}: {profile[k]:.2f}\n"

            cognitive_query += f"\\n请针对这位学生的认知维度情况，提供1-2条提升思维能力、学习策略和元认知能力的建议. 每条建议需包含具体训练方法、应用场景和理论依据."

            cognitive_recs = self._consult_expert("认知心理学家", cognitive_query)
            recommendations["认知维度"] = self._parse_recommendations(cognitive_recs)

            # 3. 教育心理咨询师提供情感维度建议
            affective_query = (
                f"学生ID {student_id} 的情感维度得分为 {profile['affective_score']:.2f}/1.0\n"
                f"学生类型: {profile['student_type']}。\n"
            )

            detail_keys = [k for k in profile.keys() if k.startswith('情感_')]
            for k in detail_keys:
                affective_query += f"{k}: {profile[k]:.2f}\n"

            affective_query += "\\n请针对这位学生的情感状况，提供1-2条改善学习情绪、提升动机和增强心理韧性的建议. 每条建议需包含心理学原理解释和实际应用方法."

            affective_recs = self._consult_expert("教育心理咨询师", affective_query)
            recommendations["情感维度"] = self._parse_recommendations(affective_recs)

            # 4. 学习行为指导专家提供行为维度建议
            behavioral_query = (
                f"学生ID {student_id} 的行为维度得分为 {profile['behavioral_score']:.2f}/1.0\n"
                f"学生类型: {profile['student_type']}。\n"
            )

            detail_keys = [k for k in profile.keys() if k.startswith('行为_')]
            for k in detail_keys:
                behavioral_query += f"{k}: {profile[k]:.2f}\n"

            behavioral_query += "\\n请针对这位学生的学习行为模式，提供1-2条培养良好学习习惯、提高时间管理能力和改善学习环境的具体建议. 请包含习惯养成的科学方法和监测机制."

            behavioral_recs = self._consult_expert("学习行为指导专家", behavioral_query)
            recommendations["行为维度"] = self._parse_recommendations(behavioral_recs)

            # 5. 教育人工智能专家整合所有建议，提供系统性学习策略
            integration_query = (
                f"学生ID {student_id} 的完整学习画像:\\n"
                f"- 学生类型: {profile['student_type']}\\n"
                f"- 知识维度: {profile['knowledge_score']:.2f}\\n"
                f"- 认知维度: {profile['cognitive_score']:.2f}\\n"
                f"- 情感维度: {profile['affective_score']:.2f}\\n"
                f"- 行为维度: {profile['behavioral_score']:.2f}\\n\\n"
                f"各维度专家已提供了针对性建议. 现在请你作为教育人工智能专家，整合这些见解,\\n"
                f"设计一个系统化的学习提升方案，包括技术工具支持、教师指导建议和家庭配合策略. \\n"
                f"请特别关注数字化学习资源的推荐和智能学习工具的应用.\\n"
            )

            ai_recs = self._consult_expert("教育人工智能专家", integration_query)

            # 解析AI专家的建议到不同类别
            ai_parsed = self._parse_recommendations(ai_recs)
            for rec in ai_parsed:
                if "工具" in rec or "软件" in rec or "资源" in rec or "技术" in rec:
                    recommendations["学习策略"].append(rec)
                elif "教师" in rec or "老师" in rec or "课堂" in rec or "指导" in rec:
                    recommendations["教师支持"].append(rec)
                elif "家长" in rec or "家庭" in rec or "父母" in rec:
                    recommendations["总体评估"].append(rec)

        except Exception as e:
            print(f"生成建议时出错: {e}")
            import traceback
            traceback.print_exc()
            recommendations["error"] = f"生成建议时出错: {str(e)}"

        return recommendations

    def _parse_recommendations(self, recommendations_text):
        """解析专家建议文本为结构化数据

        Args:
            recommendations_text: 专家建议文本

        Returns:
            list: 建议列表
        """
        # 简单的解析逻辑，将文本按条目分割
        if not recommendations_text:
            return []

        # 替换常见的编号模式
        for pattern in ["1. ", "2. ", "3. ", "4. ", "5. ", "1）", "2）", "3）", "4）", "5）", "①", "②", "③", "④", "⑤"]:
            recommendations_text = recommendations_text.replace(pattern, "|||")

        # 分割并清理
        items = [item.strip() for item in recommendations_text.split("|||") if item.strip()]

        # 移除可能的标题行
        if items and any(keyword in items[0].lower() for keyword in ["建议", "推荐", "总结", "分析", "策略"]):
            items = items[1:]

        return items

    def generate_intervention_plan(self, student_id):
        """生成具体的干预计划

        Args:
            student_id: 学生ID

        Returns:
            dict: 包含短期、中期和长期干预措施的计划
        """
        if student_id not in self.student_profiles:
            self.analyze_student(student_id)

        if student_id not in self.student_profiles:
            return {"error": "无法获取学生数据"}

        profile = self.student_profiles[student_id]

        # 创建干预计划查询
        intervention_query = (
            f"我需要为一位学生制定全面的干预计划. 学生情况:\n"
            f"- 学生ID: {student_id}\n"
            f"- 学生类型: {profile['student_type']}\n"
            f"- 知识维度得分: {profile['knowledge_score']:.2f}/1.0\n"
            f"- 认知维度得分: {profile['cognitive_score']:.2f}/1.0\n"
            f"- 情感维度得分: {profile['affective_score']:.2f}/1.0\n"
            f"- 行为维度得分: {profile['behavioral_score']:.2f}/1.0\n\n"
            f"请设计一个分阶段的干预计划，包括：\n"
            f"1. 短期干预计划（1-2周）：明确目标、具体行动和监测指标\n"
            f"2. 中期干预计划（1-2个月）：明确目标、具体行动和监测指标\n"
            f"3. 长期干预计划（一学期或更长）：明确目标、具体行动和监测指标\n\n"
            f"请确保计划具体可行，有明确的时间节点和可测量的成果指标. 每个阶段的干预措施应该循序渐进，相互衔接."
        )

        try:
            # 使用教育AI专家制定计划
            plan_text = self._consult_expert("教育人工智能专家", intervention_query)

            # 解析计划文本
            # 假设 plan_text 的格式为 "短期计划：目标... 具体行动... 中期计划：目标... 具体行动... 长期计划：目标... 具体行动..."
            plan = {}
            if plan_text:
                # 简单的分割，实际应用中需要更复杂的解析
                parts = plan_text.split("中期计划：")
                if len(parts) > 1:
                    short_term_part = parts[0].split("短期计划：")
                    if len(short_term_part) > 1:
                        short_term = short_term_part[1].strip()
                        plan["short_term"] = {"目标": [], "具体行动": []}
                        if "目标" in short_term and "具体行动" in short_term:
                            short_term_goals_part = short_term.split("目标：")[1].split("具体行动：")
                            if len(short_term_goals_part) > 1:
                                short_term_goals = short_term_goals_part[0].strip().split("。")
                                plan["short_term"]["目标"] = [goal.strip() for goal in short_term_goals if goal.strip()]
                                short_term_actions = short_term_goals_part[1].strip().split("。")
                                plan["short_term"]["具体行动"] = [action.strip() for action in short_term_actions if action.strip()]

                    medium_term_part = parts[1].split("长期计划：")
                    if len(medium_term_part) > 1:
                        medium_term = medium_term_part[0].strip()
                        plan["medium_term"] = {"目标": []}
                        if "目标" in medium_term:
                            medium_term_goals = medium_term.split("目标：")[1].strip().split("。")
                            plan["medium_term"]["目标"] = [goal.strip() for goal in medium_term_goals if goal.strip()]

                    long_term = medium_term_part[1].strip()
                    plan["long_term"] = {"目标": []}
                    if "目标" in long_term:
                        long_term_goals = long_term.split("目标：")[1].strip().split("。")
                        plan["long_term"]["目标"] = [goal.strip() for goal in long_term_goals if goal.strip()]

            return plan

        except Exception as e:
            print(f"生成干预计划时出错: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"生成干预计划时出错: {str(e)}"}


if __name__ == "__main__":
    agent = StudentAgent(data_path="student_profiles.csv")
    student_id = 34400002
    recommendations = agent.generate_recommendations(student_id)

    if "error" in recommendations:
        print(f"Error generating recommendations: {recommendations['error']}")
    else:
        print(f"Recommendations for student {student_id}:")
        for dimension, recs in recommendations.items():
            print(f"\n--- {dimension} ---")
            if isinstance(recs, list):
                for i, rec in enumerate(recs):
                    print(f"{i+1}. {rec}")
            else:
                print(recs)