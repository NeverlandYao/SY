import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from config import LABEL_MAP # Import config
import data_processing as data_processing

def plot_radar_chart(data, student_id=None):
    """为单个学生或总体绘制四维度雷达图"""
    dimensions = ['知识维度_综合得分', '认知维度_综合得分', '情感维度_综合得分', '行为维度_综合得分']
    dimensions = [dim for dim in dimensions if dim in data.columns]
    
    if len(dimensions) < 3:
        print("可用维度不足，无法绘制雷达图")
        return None
    
    # 准备数据
    if student_id is not None:
        # 单个学生
        if student_id not in data.index:
            print(f"找不到ID为 {student_id} 的学生")
            return None
        values = data.loc[student_id, dimensions].values.flatten().tolist()
        title = f"学生{student_id}的四维度特征"
    else:
        # 总体平均
        values = data[dimensions].mean().values.flatten().tolist()
        title = "全体学生的四维度特征平均值"
    
    # 添加首尾相连
    values += values[:1]
    
    # 使用导入的英文标签
    display_dims = [LABEL_MAP.get(dim, dim) for dim in dimensions]
    
    # 角度计算
    angles = np.linspace(0, 2*np.pi, len(dimensions), endpoint=False).tolist()
    angles += angles[:1]
    
    # 绘图
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), display_dims)
    ax.set_title(title)
    ax.grid(True)
    plt.close(fig)
    
    return display_dims, values

def calculate_average_scores(data):
    """计算各维度得分的平均值"""
    dim_scores = [col for col in data.columns if col.endswith('综合得分')]
    if not dim_scores:
        print("无维度得分数据，无法计算平均值")
        return None
    
    average_scores = data[dim_scores].mean().values.flatten().tolist()
    display_dims = [LABEL_MAP.get(dim, dim) for dim in dim_scores]
    
    return display_dims, average_scores

def plot_overall_distribution(data):
    """绘制各维度得分的总体分布"""
    dim_scores = [col for col in data.columns if col.endswith('综合得分')]
    
    if not dim_scores:
        print("无维度得分数据，无法绘制分布图")
        return
    
    plt.figure(figsize=(12, 8))
    sns.boxplot(data=data[dim_scores])
    
    # 使用英文标签
    eng_labels = ['Knowledge', 'Cognition', 'Affection', 'Behavior']
    plt.xticks(range(len(dim_scores)), eng_labels[:len(dim_scores)], rotation=45)
    
    plt.title("Distribution of Dimension Scores")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig('./dimension_png/dimension_scores_distribution.png')
    print("已保存维度得分分布图")

def plot_dimension_correlations(data):
    """绘制维度之间的相关性热图"""
    dim_scores = [col for col in data.columns if col.endswith('综合得分')]
    
    if len(dim_scores) < 2:
        print("维度得分数据不足，无法绘制相关性热图")
        return
    
    plt.figure(figsize=(10, 8))
    corr_matrix = data[dim_scores].corr()
    
    # 使用英文标签
    eng_labels = ['Knowledge', 'Cognition', 'Affection', 'Behavior']
    corr_matrix.index = eng_labels[:len(dim_scores)]
    corr_matrix.columns = eng_labels[:len(dim_scores)]
    
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
    plt.title("Correlation Between Dimensions")
    plt.tight_layout()
    plt.savefig('./dimension_png/dimension_correlations.png')
    print("已保存维度相关性热图")

def plot_student_types(data):
    """绘制学生类型分布饼图"""
    if '学生类型' not in data.columns:
        print("无学生类型数据，无法绘制饼图")
        return
    
    plt.figure(figsize=(10, 8))
    
    # 准备数据
    type_counts = data['学生类型'].value_counts()
    
    # 使用导入的英文标签
    type_counts.index = [LABEL_MAP.get(t, t) for t in type_counts.index]
    
    # 绘制饼图
    type_counts.plot.pie(autopct='%1.1f%%', shadow=True, startangle=90)
    plt.title("Student Type Distribution")
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig('./dimension_png/student_types_distribution.png')
    print("已保存学生类型分布图")

if __name__ == "__main__":
    file_path = 'Model_py.xlsx'  # 替换为你的数据文件路径
    df = data_processing.load_data(file_path)
    if df is not None:
        df_cleaned = data_processing.clean_data(df)
        if df_cleaned is not None:
            df_processed = data_processing.calculate_dimensions(df_cleaned)
            if df_processed is not None:
                df_identified = data_processing.identify_student_types(df_processed)
                if df_identified is not None:
                    print("正在生成可视化图形...")
                    plot_student_types(df_identified)
                    plot_overall_distribution(df_identified)
                    plot_dimension_correlations(df_identified)

                    # 获取学生ID
                    student_id = df_identified.index[0] if not df_identified.empty else None

                    # 获取学生个人数据
                    if student_id:
                        student_dims, student_values = plot_radar_chart(df_identified, student_id=student_id)
                    else:
                        student_dims, student_values = None, None

                    # 获取平均数据
                    average_dims, average_values = calculate_average_scores(df_identified)

                    # 准备JSON数据
                    if student_dims and student_values and average_dims and average_values:
                        radar_data = {
                            "student": {
                                "dimensions": student_dims,
                                "values": student_values
                            },
                            "average": {
                                "dimensions": average_dims,
                                "values": average_values
                            }
                        }
                        import json
                        print(json.dumps(radar_data))

                    print("可视化图形生成完成。")
                else:
                    print("学生类型识别失败")
            else:
                print("维度计算失败")
        else:
            print("数据清洗失败")
    else:
        print("数据加载失败")
