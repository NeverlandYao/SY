import data_processing as dp
import visualization as vis
import student_agent as sa
import pandas as pd
import argparse  # 添加命令行参数解析

def analyze_student_detailed(agent, student_id):
    """为指定学生生成并显示详细分析报告"""
    analysis = agent.analyze_student(student_id)
    
    if not analysis:
        return
    
    print("\n" + "="*50)
    print(f"学生 {student_id} 详细分析报告")
    print("="*50)
    
    # 1. 基本信息
    print("\n基本信息:")
    print(f"学生类型: {analysis['student_type']}")
    print(f"知识维度得分: {analysis['knowledge_score']:.2f}")
    print(f"认知维度得分: {analysis['cognitive_score']:.2f}")
    print(f"情感维度得分: {analysis['affective_score']:.2f}")
    print(f"行为维度得分: {analysis['behavioral_score']:.2f}")

    # 2. 学生画像报告
    if 'student_profile_report' in analysis:
        print("\n学生画像报告:")
        print(analysis['student_profile_report'])
    
    # 3. 详细建议
    recommendations = agent.generate_recommendations(student_id)
    
    print("\n详细个性化建议:")
    for category, recs in recommendations.items():
        if category != "error" and recs:
            print(f"\n--- {category} ---")
            for i, rec in enumerate(recs, 1):
                if isinstance(rec, dict):
                    print(f"\n{i}. ", end="")
                    if '描述' in rec:
                        print(f"{rec['描述']}")
                    elif '策略名称' in rec:
                        print(f"{rec['策略名称']}")
                    
                    # 打印详细信息
                    for key, value in rec.items():
                        if key not in ['描述', '策略名称']:
                            print(f"   • {key}: {value}")
                else:
                    print(f"\n{i}. {rec}")
    
    # 3. 干预计划
    intervention_plan = agent.generate_intervention_plan(student_id)

    print("\n\n个性化干预计划:")
    # 短期计划
    print("\n--- 短期干预计划 (1-2周) ---")
    if isinstance(intervention_plan, dict) and "short_term" in intervention_plan and isinstance(intervention_plan.get("short_term", {}), dict):
        print("目标:")
        for i, goal in enumerate(intervention_plan["short_term"].get("目标", []), 1):
            print(f"  {i}. {goal}")
        print("\n具体行动:")
        for i, action in enumerate(intervention_plan["short_term"].get("具体行动", []), 1):
            print(f"  {i}. {action}")

    # 中期计划 (简要)
    print("\n--- 中期干预计划 (1-2个月) ---")
    if isinstance(intervention_plan, dict) and "medium_term" in intervention_plan and isinstance(intervention_plan.get("medium_term", {}), dict):
        print("目标:")
        for i, goal in enumerate(intervention_plan["medium_term"].get("目标", []), 1):
            print(f"  {i}. {goal}")

    # 长期计划 (简要)
    if isinstance(intervention_plan, dict) and "long_term" in intervention_plan and isinstance(intervention_plan.get("long_term", {}), dict):
        print("\n--- 长期干预计划 (一学期或更长) ---")
        print("目标:")
        for i, goal in enumerate(intervention_plan["long_term"].get("目标", []), 1):
            print(f"  {i}. {goal}")
    
    # 4. 推荐学习资源
    resources = agent.generate_learning_resources(student_id)
    
    print("\n\n推荐学习资源:")
    for category, res_list in resources.items():
        if res_list:
            print(f"\n--- {category} ---")
            for i, res in enumerate(res_list, 1):
                print(f"\n{i}. {res['名称']}")
                print(f"   推荐理由: {res['推荐理由']}")
    
    print("\n" + "="*50)
    print("详细分析报告结束")
    print("="*50 + "\n")

def main():
    """主函数，执行数据分析流程"""
    # 添加命令行参数
    parser = argparse.ArgumentParser(description='学生分析系统')
    parser.add_argument('--student', type=int, help='要详细分析的学生ID')
    parser.add_argument('--detailed', action='store_true', help='是否显示详细分析')
    args = parser.parse_args()
    
    # 加载并处理数据
    raw_data = dp.load_data('Model_py.xlsx')
    clean_data = dp.clean_data(raw_data)
    processed_data = dp.calculate_dimensions(clean_data)
    final_data = dp.identify_student_types(processed_data)
    
    # 保存处理后的数据
    final_data.to_csv('student_profiles.csv', index=False)
    print("数据处理完成，已保存到 student_profiles.csv")
    
    # 生成可视化
    try:
        vis.plot_overall_distribution(final_data)
        vis.plot_dimension_correlations(final_data)
        vis.plot_student_types(final_data)
    except Exception as e:
        print(f"生成可视化时出错: {e}")
    
    # 创建学生代理
    try:
        agent = sa.StudentAgent('student_profiles.csv')
        
        # 如果指定了学生ID，显示该学生的详细分析
        if args.student:
            analyze_student_detailed(agent, args.student)
            return
        
        # 如果开启了详细模式，显示第一个学生的详细分析
        if args.detailed:
            first_student_id = 34400002
            analyze_student_detailed(agent, first_student_id)
            return
        
        # 默认模式：显示第一个学生的简要分析
        if not final_data.empty:
            first_student_id = 34400002
            
            print(f"\n分析学生ID: {first_student_id}")
            analysis = agent.analyze_student(first_student_id)
            
            if analysis:
                print(f"\n学生 {first_student_id} 分析结果:")
                for key, value in analysis.items():
                    if key != 'student_id':
                        print(f"  {key}: {value}")
                
                recommendations = agent.generate_recommendations(first_student_id)
                
                print("\n个性化建议摘要:")
                for category, recs in recommendations.items():
                    if category != "error" and recs:
                        print(f"\n{category}:")
                        for i, rec in enumerate(recs[:2], 1):  # 只显示前两个建议
                            if isinstance(rec, dict):
                                print(f"  {i}. {rec.get('描述', rec.get('策略名称', '建议'))}")
                            else:
                                print(f"  {i}. {rec}")
                
                print("\n要查看完整建议，请使用参数运行: python main.py --detailed")
                print("要分析特定学生，请使用: python main.py --student <学生ID>")
    
    except Exception as e:
        print(f"学生分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
