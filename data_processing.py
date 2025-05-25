import pandas as pd
import numpy as np
import math
from sklearn.preprocessing import MinMaxScaler

def load_data(file_path):
    """
    加载学生数据
    
    Args:
        file_path: 数据文件路径
    
    Returns:
        pandas DataFrame: 包含学生数据的数据框
    """
    # 加载所有列，以便保留原始ID (CNTSTUID)
    try:
        # 读取数据
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=0)
        else:
            df = pd.read_excel(file_path, header=0)
        print(f"成功加载数据: {df.shape[0]} 行, {df.shape[1]} 列")
        return df
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None

def clean_data(df):
    """
    清洗数据，处理缺失值和异常值
    
    Args:
        df: 原始数据
    
    Returns:
        pandas DataFrame: 清洗后的数据
    """
    if df is None:
        return None
    
    # 复制数据，避免修改原始数据
    df_clean = df.copy()
    
    # 处理特殊值（如97, 98, 99等）
    special_values = [97, 98, 99, 997, 998, 999]
    for col in df_clean.columns:
        if df_clean[col].dtype in [np.int64, np.float64]:
            df_clean[col] = df_clean[col].replace(special_values, np.nan)
    
    # 强制转换为数值类型，无法转换的变为NaN
    for col in ['PVMATH', 'PVREAD', 'PVSCIE']:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # 处理缺失值
    key_columns = ['PVMATH', 'PVREAD', 'PVSCIE']
    existing_key_columns = [col for col in key_columns if col in df_clean.columns]
    
    if existing_key_columns:
        df_clean = df_clean.dropna(subset=existing_key_columns)
        print(f"移除缺失关键数据的行后，剩余 {df_clean.shape[0]} 行")
    
    return df_clean

def calculate_dimensions(df):
    """
    计算四个维度的得分
    
    Args:
        df: 清洗后的数据
    
    Returns:
        pandas DataFrame: 增加了维度得分的数据
    """
    if df is None:
        return None
    
    df_result = df.copy()
    
    # 初始化维度列
    df_result['知识维度_综合得分'] = np.nan
    df_result['认知维度_综合得分'] = np.nan
    df_result['情感维度_综合得分'] = np.nan
    df_result['行为维度_综合得分'] = np.nan
    
    # 根据实际数据计算维度得分
    # 知识维度
    knowledge_cols = [col for col in ['PVMATH', 'PVREAD', 'PVSCIE'] if col in df_result.columns]
    if knowledge_cols:
        # 标准化
        scaler = MinMaxScaler()
        df_result[knowledge_cols] = scaler.fit_transform(df_result[knowledge_cols])
        df_result['知识维度_综合得分'] = df_result[knowledge_cols].mean(axis=1).round(2)
    
    # 认知维度
    cognitive_cols = [col for col in [f'ST307Q{i:02d}JA' for i in range(7, 11)] if col in df_result.columns]
    if cognitive_cols:
        # 确保在计算均值前排除 97
        df_cognitive = df_result[cognitive_cols].replace(97, np.nan)
        df_result['认知维度_综合得分'] = (df_cognitive.mean(axis=1) / 4.0).round(2)  # 假设满分为4
        # 如果计算结果为 NaN (例如，所有值都是 97)，则替换为 0
        df_result['认知维度_综合得分'] = df_result['认知维度_综合得分'].fillna(0)

    # 情感维度
    affective_cols = [col for col in [f'ST297Q{i:02d}JA' for i in range(1, 11)] if col in df_result.columns]
    if affective_cols:
        df_result['情感维度_综合得分'] = ((4 - df_result[affective_cols].mean(axis=1)) / 4.0).round(2)  # 反向计分，假设满分为4
    
    # 行为维度
    behavioral_cols = [col for col in [f'ST326Q{i:02d}JA' for i in range(1, 7)] if col in df_result.columns]
    if behavioral_cols:
        df_result['行为维度_综合得分'] = (df_result[behavioral_cols].mean(axis=1) / 5.0).round(2)  # 假设满分为5
    
    return df_result

def identify_student_types(df):
    """
    识别学生类型
    
    Args:
        df: 包含维度得分的数据
    
    Returns:
        pandas DataFrame: 增加了学生类型的数据
    """
    if df is None:
        return None
    
    df_result = df.copy()
    
    # 初始化学生类型列
    df_result['学生类型'] = '待分类'
    
    # 获取维度列
    dimension_cols = [col for col in ['知识维度_综合得分', '认知维度_综合得分', '情感维度_综合得分', '行为维度_综合得分'] 
                     if col in df_result.columns]
    
    if len(dimension_cols) >= 2:
        # 计算阈值（使用中位数）
        thresholds = {col: df_result[col].median() for col in dimension_cols}
        
        # 知识高+认知高：优秀全面型
        if '知识维度_综合得分' in dimension_cols and '认知维度_综合得分' in dimension_cols:
            mask = (df_result['知识维度_综合得分'] > thresholds['知识维度_综合得分']) & \
                   (df_result['认知维度_综合得分'] > thresholds['认知维度_综合得分'])
            df_result.loc[mask, '学生类型'] = '优秀全面型'
        
        # 知识高+情感低：高压成绩型
        if '知识维度_综合得分' in dimension_cols and '情感维度_综合得分' in dimension_cols:
            mask = (df_result['知识维度_综合得分'] > thresholds['知识维度_综合得分']) & \
                   (df_result['情感维度_综合得分'] < thresholds['情感维度_综合得分']) & \
                   (df_result['学生类型'] == '待分类')
            df_result.loc[mask, '学生类型'] = '高压成绩型'
        
        # 知识低+情感高+行为高：潜力型
        if '知识维度_综合得分' in dimension_cols and '情感维度_综合得分' in dimension_cols and '行为维度_综合得分' in dimension_cols:
            mask = (df_result['知识维度_综合得分'] < thresholds['知识维度_综合得分']) & \
                   (df_result['情感维度_综合得分'] > thresholds['情感维度_综合得分']) & \
                   (df_result['行为维度_综合得分'] > thresholds['行为维度_综合得分']) & \
                   (df_result['学生类型'] == '待分类')
            df_result.loc[mask, '学生类型'] = '潜力型'
        
        # 知识低+认知低+行为低：警示型
        if '知识维度_综合得分' in dimension_cols and '认知维度_综合得分' in dimension_cols and '行为维度_综合得分' in dimension_cols:
            mask = (df_result['知识维度_综合得分'] < thresholds['知识维度_综合得分']) & \
                   (df_result['认知维度_综合得分'] < thresholds['认知维度_综合得分']) & \
                   (df_result['行为维度_综合得分'] < thresholds['行为维度_综合得分']) & \
                   (df_result['学生类型'] == '待分类')
            df_result.loc[mask, '学生类型'] = '警示型'
    
    return df_result

from db_utils import insert_student_data, insert_recommendation_data
from student_agent import StudentAgent

if __name__ == "__main__":
    file_path = 'student_profiles.csv'  # 替换为你的数据文件路径
    df = load_data(file_path)
    if df is not None:
        df_cleaned = clean_data(df)
        if df_cleaned is not None:
            df_processed = calculate_dimensions(df_cleaned)
            if df_processed is not None:
                df_identified = identify_student_types(df_processed)
                if df_identified is not None:
                    print("\nProcessed Data:")
                    print(df_identified.head())

                    # 初始化 StudentAgent
                    student_agent = StudentAgent(file_path)

                    # 存储数据到数据库
                    for index, row in df_identified.iterrows():
                        student_id = int(row['CNTSTUID'])
                        student_data = {
                            'student_id': student_id,  # 使用 CNTSTUID 作为 student_id
                            'student_type': row['学生类型'],
                            'knowledge_score': row['知识维度_综合得分'] if '知识维度_综合得分' in row else None,
                            'cognitive_score': row['认知维度_综合得分'] if '认知维度_综合得分' in row else None,
                            'affective_score': row['情感维度_综合得分'] if '情感维度_综合得分' in row else None,
                            'behavioral_score': row['行为维度_综合得分'] if '行为维度_综合得分' in row else None,
                            'expert_diagnosis': None,  # 假设没有专家诊断
                            'risk_level': None,  # 假设没有风险等级
                            'risk_factors': None,  # 假设没有风险因素
                            'CNTSTUID': row['CNTSTUID'] if 'CNTSTUID' in row else None,
                            'ST004D01T': row['ST004D01T'] if 'ST004D01T' in row else None,
                            'ST001D01T': row['ST001D01T'] if 'ST001D01T' in row else None,
                            'PV1MATH': row['PVMATH'] if 'PVMATH' in row else None,
                            'PV1READ': row['PVREAD'] if 'PVREAD' in row else None,
                            'PV1SCIE': row['PVSCIE'] if 'PV1SCIE' in row else None,
                            'ST099Q01TA': row['ST099Q01TA'] if 'ST099Q01TA' in row else None,
                            'ST099Q02TA': row['ST099Q02TA'] if 'ST099Q02TA' in row else None,
                            'ST099Q03TA': row['ST099Q03TA'] if 'ST099Q03TA' in row else None,
                            'ST099Q04TA': row['ST099Q04TA'] if 'ST099Q04TA' in row else None
                        }
                        insert_student_data(student_data)

                        # 生成并存储推荐
                        recommendations = student_agent.generate_recommendations(student_id)

                        if recommendations:
                            insert_recommendation_data(student_id, '知识维度', recommendations.get('知识维度', ''))
                            insert_recommendation_data(student_id, '认知维度', recommendations.get('认知维度', ''))
                            insert_recommendation_data(student_id, '情感维度', recommendations.get('情感维度', ''))
                            insert_recommendation_data(student_id, '行为维度', recommendations.get('行为维度', ''))
                else:
                    print("学生类型识别失败")
            else:
                print("维度计算失败")
        else:
            print("数据清洗失败")
    else:
        print("数据加载失败")
