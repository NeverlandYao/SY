import pandas as pd
import numpy as np
from openai import OpenAI
import json
import time
import re
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
            "中心调度智能体": {
                "role": "你是一个教育系统的中心调度与决策核心，承担权重分配与冲突协调功能。",
                "responsibility": "统筹各领域专家的诊断意见，基于'风险优先协议'（Risk-First Protocol）进行多目标优化决策。当学科提升建议与心理健康风险发生冲突时，负责动态调整各维度的干预权重，输出最终的平衡方案。"
            },
            "学科教学专家": {
                "role": "你是一位资深的学科教学专家，擅长维果茨基ZPD理论与布鲁姆认知分类学。",
                "responsibility": "[识别认知断层] 分析PVMATH（数学成绩）与ST276Q（问题解决能力）的背离，定位高分低能或基础薄弱点。[设计ZPD任务] 生成略高于当前水平的阶梯式学习任务，推荐微课与拓展阅读。"
            },
            "认知心理学家": {
                "role": "你是一位认知心理学家，精通Flavell元认知理论与SRL自我调节学习。",
                "responsibility": "[评估品质思维] 分析ST307Q（任务坚持）与ST326Q（分心/数字使用）的关系，区分策略缺失与意志力薄弱。[训练元认知策略] 制定番茄工作法、出声思维任务，引导学生监控思维过程。"
            },
            "教育心理咨询师": {
                "role": "你是一位教育心理咨询师，基于Pekrun控制-价值理论与积极心理学。",
                "responsibility": "[情绪风险反馈] 识别ST297Q（高焦虑）或ST034Q（低归属感）等阻断性情感因素。[提供情绪处方] 生成引导话术、考前放松预案，建议参与特定社团活动以重建归属感。"
            },
            "学习行为指导专家": {
                "role": "你是一位学习行为指导专家，运用行为主义强化理论与助推理论。",
                "responsibility": "[投入度监测] 关联ST062Q（缺勤）与ST326Q（数字资源使用），发现低效时间管理模式。[优化行为习惯] 制定数字化设备使用公约，设计打卡-反馈激励机制，利用助推策略优化时间分配。"
            }
        }

        # 可用的 Action 类型
        self.AVAILABLE_ACTIONS = ["直接回复", "咨询其他LLM", "发送告警", "记录事件", "推荐资源", "执行特定函数"]

        print("学生智能代理系统初始化完成")

    def _consult_expert(self, expert_name, query, available_actions=None, model="Qwen/Qwen2.5-7B-Instruct-1M"):
        """咨询特定领域的专家智能体，并允许选择执行不同的 action

        Args:
            expert_name: 专家名称
            query: 查询内容
            available_actions: 可供选择的动作列表，例如 ["直接回复", "咨询其他LLM"]
            model: 使用的模型ID

        Returns:
            dict: 包含选择的 action 和专家的意见
        """
        if expert_name not in self.expert_agents:
            raise ValueError(f"未知的专家: {expert_name}")

        expert = self.expert_agents[expert_name]

        print(f"正在咨询{expert_name}...")

        messages = [
            {
                'role': 'system',
                'content': f"{expert['role']}\n\n你的职责：{expert['responsibility']}\n\n"
                           f"请提供专业、深入、具体且可操作的建议。请基于教育学、心理学等相关理论进行分析, 同时考虑实际应用价值。回答应结构清晰，语言专业但易于理解。\n\n"
            }
        ]

        if available_actions:
            actions_description = "\n根据当前情况，你可以选择执行以下操作：\n"
            for i, action in enumerate(available_actions):
                actions_description += f"{i+1}. **{action}**"
                if action == "咨询其他LLM":
                    actions_description += " - 如果你需要更深入的分析或来自特定领域模型的信息，请选择此项，并在你的回复中明确你希望咨询的 LLM 的名称或功能。"
                elif action == "发送告警":
                    actions_description += " - 如果你识别到需要立即关注的风险或问题，请选择此项，并在你的回复中包含告警的级别和详细信息。"
                elif action == "记录事件":
                    actions_description += " - 如果你需要记录某些重要的学生行为或状态，请选择此项，并在你的回复中包含要记录的事件描述。"
                elif action == "推荐资源":
                    actions_description += " - 如果你知道有对学生有帮助的学习资源或工具，请选择此项，并在你的回复中包含资源类型和描述。"
                elif action == "执行特定函数":
                    actions_description += " - 如果你需要调用预定义的函数来执行特定操作，请选择此项，并在你的回复中说明要调用的函数名称和参数。"
                actions_description += "\n"
            messages[0]['content'] += actions_description + "\n请在你的回复的**第一行**清晰地指出你选择的**操作名称**。如果选择 '直接回复'，则直接开始你的回答。"

        messages.append({'role': 'user', 'content': query})

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )

            selected_action = None
            llm_response = ""
            first_line = True

            for chunk in response:
                try:
                    content = chunk.choices[0].delta.content or ""
                    if content:
                        if first_line and available_actions:
                            # 检查第一行是否包含可用的动作
                            for act in available_actions:
                                if content.strip().startswith(act):
                                    selected_action = act
                                    # 移除第一行的动作描述
                                    content = content.replace(act, "", 1).strip()
                                    break
                            first_line = False

                        llm_response += content
                        # 打印实时响应
                except Exception as e:
                    continue

            print(f"\n{expert_name}已完成分析")

            # 处理最终响应
            final_response = llm_response.strip()
            if selected_action and final_response.startswith(selected_action):
                 # 如果第一行包含选定的动作，移除它
                 pattern = r"^" + re.escape(selected_action) + r"[\s\W]*"
                 final_response = re.sub(pattern, "", final_response).strip()


            return {"action": selected_action, "response": final_response}

        except Exception as e:
            print(f"咨询专家时出错: {e}")
            return {"action": None, "response": f"咨询{expert_name}失败: {str(e)}"}

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
        if items and any(keyword in items[0].lower() for keyword in ["直接回复","建议", "推荐", "总结", "分析", "策略"]):
            items = items[1:]

        # 进一步清理空行或只有空白字符的条目
        items = [item for item in items if item and item.strip()]

        return items

    def analyze_student(self, student_id):
        """分析特定学生的数据并生成个性化评估"""
        # 验证学生ID是否在有效范围内
        if student_id not in self.data['CNTSTUID'].values:
            print(f"错误: 找不到ID为 {student_id} 的学生")
            print(f"有效的学生ID范围: {min(self.data['CNTSTUID'])}-{max(self.data['CNTSTUID'])}")
            return None

        student_data = self.data[self.data['CNTSTUID'] == int(student_id)]

        # 检查学生数据是否为空
        if student_data.empty:
            print(f"错误: 找不到ID为 {student_id} 的学生")
            print(f"有效的学生ID范围: {min(self.data['CNTSTUID'])}-{max(self.data['CNTSTUID'])}")
            return None

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
            'student_id': int(student_id),
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

        risk_level = "低风险"
        risk_factors = []

        # 示例风险判断逻辑
        if analysis['affective_score'] < 0.3:
            risk_level = "中风险"
            risk_factors.append("情感维度得分较低，可能存在心理健康风险")
        if analysis['behavioral_score'] < 0.4 and analysis['student_type'] == "特殊关注学生":
            risk_level = "高风险"
            risk_factors.append("行为维度得分较低，且为特殊关注学生，需要高度关注")

        analysis['risk_level'] = risk_level
        analysis['risk_factors'] = risk_factors

        # 让中心调度智能体生成学生画像，包含风险信息
        try:
            profile_analysis_query = (
                f"请根据以下学生的学习数据和维度得分，生成一份详细的学生画像报告，**并在报告中明确指出学生的风险等级和风险因素**：\n"
                f"{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
                f"请在画像中整合知识、认知、情感、行为四个维度的分析，突出学生的特点、优势和潜在问题，**并重点分析可能存在的风险。**报告应结构清晰，语言专业但易于理解。"
            )
            student_profile_report = self._consult_expert("中心调度智能体", profile_analysis_query)['response']
            analysis['student_profile_report'] = student_profile_report
        except Exception as e:
            print(f"中心调度智能体分析出错: {e}")
            analysis['student_profile_report'] = "无法生成学生画像报告"

        # 让中心调度智能体进行深度分析与冲突协调
        try:
            expert_analysis = self._consult_expert(
                "中心调度智能体",
                f"我需要你作为中心调度核心，分析一位学生的学习情况，并统筹各维度可能存在的矛盾（如学业压力与心理健康冲突）。以下是该学生的数据：\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
                f"请你详细分析这位学生的特点、优势、不足。请基于'风险优先协议'，识别潜在的教育目标冲突，并给出权衡后的综合诊断意见。"
            )['response']
            analysis['expert_diagnosis'] = expert_analysis
        except Exception as e:
            print(f"中心调度智能体分析出错: {e}")
            analysis['expert_diagnosis'] = "无法获取专家分析"

        # 保存分析结果
        self.student_profiles[student_id] = analysis
        print(json.dumps(analysis, indent=2, ensure_ascii=False))

        # 在分析过程中，如果识别到高风险，可以触发 "发送告警" action
        # 简化：直接由中心调度智能体在报告中指出，或此处仅作简单判断
        if analysis['risk_level'] == "高风险":
             pass # 告警逻辑保留或由中心调度智能体内部处理

        return analysis

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
            "知识维度": [],
            "认知维度": [],
            "情感维度": [],
            "行为维度": [],
            "知识诊断": []
        }

        # 1. 学科教学专家提供知识维度建议，并判断是否需要进一步诊断
        knowledge_query = (
            f"学生ID {student_id} 的知识维度得分为 {profile['knowledge_score']:.2f}/1.0\n"
            f"学生类型: {profile['student_type']}。\n"
        )
        detail_keys = [k for k in profile.keys() if k.startswith('知识_')]
        for k in detail_keys:
            knowledge_query += f"{k}: {profile[k]:.2f}\n"
        knowledge_query += "\\n请针对这位学生的知识维度情况，用2-3句话提供建议。"

        knowledge_response = self._consult_expert("学科教学专家", knowledge_query, available_actions=["直接回复", "咨询其他LLM", "推荐资源"])
        action = knowledge_response['action']
        response = knowledge_response['response']

        if action == "直接回复":
            recommendations["知识维度"] = self._parse_recommendations(response)
        elif action == "咨询其他LLM":
            if "知识诊断LLM" in response: # LLM 在回复中
                diagnosis_query = f"请对学生ID {student_id} 的知识维度进行更深入的诊断分析，当前的知识维度得分为 {profile['knowledge_score']:.2f}，详细指标如下：\n"
                for k in detail_keys:
                    diagnosis_query += f"{k}: {profile[k]:.2f}\n"
                diagnosis_response = self._consult_expert("知识诊断LLM", diagnosis_query)['response']
                recommendations["知识诊断"] = self._parse_recommendations(diagnosis_response)
            else:
                recommendations["知识维度"].append(f"学科教学专家建议咨询其他LLM：{response}")
        elif action == "推荐资源":
            recommendations["知识维度"].append(f"学科教学专家推荐资源：{response}")
        else:
            recommendations["知识维度"].append(response) # 默认将回复作为建议

        # 2. 认知心理学家提供认知维度建议
        cognitive_query = (
            f"学生ID {student_id} 的认知维度得分为 {profile['cognitive_score']:.2f}/1.0\n"
            f"学生类型: {profile['student_type']}。\n"
        )
        detail_keys = [k for k in profile.keys() if k.startswith('认知_')]
        for k in detail_keys:
            cognitive_query += f"{k}: {profile[k]:.2f}\n"
        cognitive_query += "\\n请针对这位学生的认知维度情况，用2-3句话提供建议，仅仅提供建议即可。"

        cognitive_response = self._consult_expert("认知心理学家", cognitive_query)
        print(cognitive_response)
        recommendations["认知维度"] = cognitive_response['response']

        # 3. 教育心理咨询师提供情感维度建议
        affective_query = (
            f"学生ID {student_id} 的情感维度得分为 {profile['affective_score']:.2f}/1.0\n"
            f"学生类型: {profile['student_type']}。\n"
        )
        detail_keys = [k for k in profile.keys() if k.startswith('情感_')]
        for k in detail_keys:
            affective_query += f"{k}: {profile[k]:.2f}\n"
        affective_query += "\\n请针对这位学生的情感状况，提供1-2条改善学习情绪、提升动机和增强心理韧性的建议，仅仅提供建议即可."
        if profile.get('risk_level') in ["中风险", "高风险"]:
            affective_query += " **请特别关注学生的情感状态和心理健康，提供具体的支持建议。**"

        affective_response = self._consult_expert("教育心理咨询师", affective_query)
        print(affective_response)
        # recommendations["情感维度"] = self._parse_recommendations(affective_response['response'])
        recommendations["情感维度"] = affective_response['response']

        # 4. 学习行为指导专家提供行为维度建议
        behavioral_query = (
            f"学生ID {student_id} 的行为维度得分为 {profile['behavioral_score']:.2f}/1.0\n"
            f"学生类型: {profile['student_type']}。\n"
        )
        detail_keys = [k for k in profile.keys() if k.startswith('行为_')]
        for k in detail_keys:
            behavioral_query += f"{k}: {profile[k]:.2f}\n"
        behavioral_query += "\\n请针对这位学生的学习行为模式，提供1-2条培养良好学习习惯、提高时间管理能力和改善学习环境的具体建议."

        behavioral_response = self._consult_expert("学习行为指导专家", behavioral_query)
        print(behavioral_response)
        # recommendations["行为维度"] = self._parse_recommendations(behavioral_response['response'])
        recommendations["行为维度"] = behavioral_response['response']

        
        # 将特定维度的建议列表合并为字符串
        # 确保在返回之前处理所有相关维度
        for dim_key in ["知识维度", "认知维度", "情感维度", "行为维度", "知识诊断"]: # Updated list of dimensions
            if dim_key in recommendations and recommendations[dim_key] and isinstance(recommendations[dim_key], list):
                # 对于主要维度，如果列表不为空但解析后为空字符串（例如只有一个空元素），则设为“暂无具体建议”
                if dim_key in ["知识维度", "认知维度", "情感维度", "行为维度"]:
                    processed_list = [item for item in recommendations[dim_key] if item.strip()]
                    if not processed_list:
                        recommendations[dim_key] = "暂无具体建议。"
                    else:
                        recommendations[dim_key] = "\n".join(processed_list)
                else: # 其他类别直接join
                     recommendations[dim_key] = "\n".join(recommendations[dim_key])
            elif dim_key in recommendations and not recommendations[dim_key]: # 如果列表为空
                 if dim_key in ["知识维度", "认知维度", "情感维度", "行为维度"]:
                    recommendations[dim_key] = "暂无具体建议。"
                 else:
                    recommendations[dim_key] = "" # 其他类别设为空字符串
            # 如果维度键不存在于recommendations中 (例如 "知识诊断" 可能不存在)，则不进行操作或可以初始化为空字符串
            elif dim_key not in recommendations and dim_key in ["知识维度", "认知维度", "情感维度", "行为维度"]:
                 recommendations[dim_key] = "未能生成建议。"


        return recommendations

    def _log_student_event(self, student_id, event_type, details):
        print(f"记录事件 - 学生ID: {student_id}, 类型: {event_type}, 详情: {details}")
        # 这里可以添加将事件记录到数据库或日志文件的逻辑
