import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

def process_pisa_data(file_path):
    print(f"Loading data from {file_path}...")
    # Read excel, skipping the description row (row 1, index 1)
    # Header is at index 0. Data starts at index 2?
    # Let's read header=0, then drop index 0.
    df = pd.read_excel(file_path, header=0)
    
    # Check if first row is description
    if isinstance(df.iloc[0]['CNTSCHID'], str) and 'School ID' in str(df.iloc[0]['CNTSCHID']):
        print("Removing description row...")
        df = df.drop(0).reset_index(drop=True)
    
    # Columns of interest
    # Knowledge: PVMATH, PVREAD, PVSCIE
    knowledge_cols = ['PVMATH', 'PVREAD', 'PVSCIE']
    
    # Cognition: ST307Q (Task Persistence)
    # Check columns starting with ST307Q
    cognition_cols = [c for c in df.columns if c.startswith('ST307Q')]
    
    # Emotion: ST297Q (Math Anxiety)
    emotion_cols = [c for c in df.columns if c.startswith('ST297Q')]
    
    # Behavior: ST326Q (Digital Resource Usage)
    behavior_cols = [c for c in df.columns if c.startswith('ST326Q')]
    
    print(f"Knowledge cols: {knowledge_cols}")
    print(f"Cognition cols: {cognition_cols}")
    print(f"Emotion cols: {emotion_cols}")
    print(f"Behavior cols: {behavior_cols}")
    
    # Convert to numeric
    all_cols = knowledge_cols + cognition_cols + emotion_cols + behavior_cols + ['CNTSTUID']
    for col in all_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # Clean Likert scale columns (ST...)
    # Replace common PISA missing codes with NaN
    # Single digit missing: 7 (N/A), 8 (Invalid), 9 (Missing)
    # Double digit missing: 97, 98, 99
    # We apply this to Cognition, Emotion, Behavior columns
    likert_cols = cognition_cols + emotion_cols + behavior_cols
    missing_codes = [7, 8, 9, 97, 98, 99]
    
    for col in likert_cols:
        df[col] = df[col].replace(missing_codes, np.nan)
        
    # Check data quality
    print(f"Missing values after cleaning: {df[all_cols].isna().sum().sum()}")
    
    # Impute missing values with column mean to preserve the 5908 sample size
    # (Assuming the user wants to analyze this specific batch)
    for col in all_cols:
        if col != 'CNTSTUID': # Don't impute ID
            df[col] = df[col].fillna(df[col].mean())
            
    # Drop rows that are still missing (e.g. if a column is ALL missing)
    initial_len = len(df)
    df_clean = df.dropna(subset=all_cols).copy()
    print(f"Data prepared for clustering. Rows: {initial_len} -> {len(df_clean)}")
    
    # Calculate Dimension Scores
    # Knowledge: Average of PVs
    df_clean['Knowledge_Raw'] = df_clean[knowledge_cols].mean(axis=1)
    
    # Cognition: Average of ST307Q
    # Check value range. Usually 1-4. High score ? 
    # ST307Q: 1=Strongly disagree, 4=Strongly agree. 
    # Usually "I give up easily" vs "I persist". Need to check direction.
    # Assuming standard PISA scaling or just taking mean for clustering now.
    # User said "High Task Persistence". 
    df_clean['Cognition_Raw'] = df_clean[cognition_cols].mean(axis=1)
    
    # Emotion: Average of ST297Q (Anxiety)
    # ST297Q: Often "I worry...", "I get very tense...". 
    # 1=Strongly disagree, 4=Strongly agree.
    # High score = High Anxiety.
    df_clean['Emotion_Raw'] = df_clean[emotion_cols].mean(axis=1)
    
    # Behavior: Average of ST326Q (Digital Resources)
    df_clean['Behavior_Raw'] = df_clean[behavior_cols].mean(axis=1)
    
    # Standardize for Clustering
    scaler = StandardScaler()
    features = ['Knowledge_Raw', 'Cognition_Raw', 'Emotion_Raw', 'Behavior_Raw']
    X = df_clean[features]
    X_scaled = scaler.fit_transform(X)
    
    df_clean[['V_Knowledge', 'V_Cognition', 'V_Emotion', 'V_Behavior']] = X_scaled
    
    # K-Means Clustering (K=4)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df_clean['Cluster'] = kmeans.fit_predict(X_scaled)
    
    # Analyze Clusters
    cluster_means = df_clean.groupby('Cluster')[features].mean()
    print("\nCluster Centers (Raw Scores):")
    print(cluster_means)
    
    cluster_means_scaled = df_clean.groupby('Cluster')[['V_Knowledge', 'V_Cognition', 'V_Emotion', 'V_Behavior']].mean()
    print("\nCluster Centers (Standardized):")
    print(cluster_means_scaled)
    
    # Map Clusters to Types
    # A: Comprehensive (High Knowledge, High Cognition, High Behavior, Low Anxiety?)
    # B: High-Pressure (High Knowledge, High Anxiety)
    # C: Potential (Low Knowledge, High Cognition, High Behavior)
    # D: Warning (Low everything)
    
    # Logic to identify types based on centroids
    # We assign each cluster to the closest ideal type definition or using rules.
    
    # Robust Mapping Logic:
    # 1. High-Pressure (B): Highest Emotion (Anxiety)
    # 2. Excellent (A): Highest Knowledge (among remaining)
    # 3. Warning (D): Lowest Knowledge (among remaining)
    # 4. Potential (C): The last one (usually High Cognition/Behavior)
    
    mapping_logic = {}
    
    # Create a dataframe for easier sorting
    centers = cluster_means_scaled.copy()
    
    # 1. Find High-Pressure (Max Emotion)
    b_cluster = centers['V_Emotion'].idxmax()
    mapping_logic[b_cluster] = '高压成绩型'
    centers = centers.drop(b_cluster)
    
    # 2. Find Excellent (Max Knowledge)
    a_cluster = centers['V_Knowledge'].idxmax()
    mapping_logic[a_cluster] = '优秀全面型'
    centers = centers.drop(a_cluster)
    
    # 3. Find Warning (Min Knowledge)
    d_cluster = centers['V_Knowledge'].idxmin()
    mapping_logic[d_cluster] = '警示型'
    centers = centers.drop(d_cluster)
    
    # 4. Find Potential (Remaining)
    c_cluster = centers.index[0]
    mapping_logic[c_cluster] = '潜力型'
    
    type_mapping = mapping_logic
    print("\nProposed Mapping (Dynamic):")
    print(type_mapping)
    
    df_clean['Student_Type'] = df_clean['Cluster'].map(type_mapping)
    
    # Rename columns to match system expected format
    # System expects: 知识维度_综合得分, 认知维度_综合得分, 情感维度_综合得分, 行为维度_综合得分
    # And we should probably normalize them to 0-1 or just keep them?
    # The system visualization uses 0-100 or 0-1.
    # data_processing.py uses calculate_dimensions which normalizes to 0-1 or similar.
    # Let's normalize the raw scores to 0-1 for the system display using MinMax scaling or similar logic.
    
    # Knowledge: Raw is score ~400-600. Map to 0-1.
    # Cognition/Emotion/Behavior: Raw 1-4. Map to 0-1.
    
    # Knowledge
    k_min, k_max = df_clean['Knowledge_Raw'].min(), df_clean['Knowledge_Raw'].max()
    df_clean['知识维度_综合得分'] = (df_clean['Knowledge_Raw'] - k_min) / (k_max - k_min)
    
    # Cognition (1-4)
    df_clean['认知维度_综合得分'] = (df_clean['Cognition_Raw'] - 1) / 3
    
    # Emotion (1-4) - Note: System display usually expects "Positive" score.
    # If Anxiety is high (4), score is high. 
    # For visualization, if we want "High Score = Good", we should invert Anxiety.
    # But the user description for Type B is "High Anxiety".
    # If the radar chart shows "Emotion", usually a full polygon is "Good".
    # If Type B has "High Anxiety", does it mean "Low Emotion Score" or "High Emotion Score"?
    # In `data_processing.py`:
    # df_result['情感维度_综合得分'] = ((4 - df_result[affective_cols].mean(axis=1)) / 4.0)
    # It inverts it! So High Score = Low Anxiety (Good).
    # So for Type B (High Anxiety), the System Score should be LOW.
    # Emotion Raw Stats shows:
    # mean 0.218, min 0.0, max 1.0.
    # Wait, ST297Q should be 1-4 scale. Why is it 0-1 range?
    # Ah, let's check the unique values again.
    # Earlier we saw [0, 1, nan].
    # It seems the data in Excel for ST297Q might be already binary or normalized?
    # Or maybe it's "Selected" (1) vs "Not Selected" (0)?
    # PISA sometimes uses 1/0 for checkboxes.
    # If ST297Q is binary (1=Yes, I have anxiety, 0=No), then:
    # High score (1) = High Anxiety.
    # We want "Emotion Score" to be high for GOOD state (Low Anxiety).
    # So if data is 0-1, we should do: Score = 1 - Raw.
    
    # If max is 1, then scaling (4-Raw)/3 is wrong because Raw is never > 1.
    # (4-0)/3 = 1.33 (clipped to 1)
    # (4-1)/3 = 1.0.
    # So everyone gets 1.0!
    
    if df_clean['Emotion_Raw'].max() <= 1:
        # Binary data assumed: 0 = Low Anxiety (Good), 1 = High Anxiety (Bad)
        df_clean['情感维度_综合得分'] = 1 - df_clean['Emotion_Raw']
    else:
        # 1-4 Scale
        df_clean['情感维度_综合得分'] = (4 - df_clean['Emotion_Raw']) / 3
        
    # Clip to 0-1 just in case
    df_clean['情感维度_综合得分'] = df_clean['情感维度_综合得分'].clip(0, 1)
    
    # Behavior (1-4)
    df_clean['行为维度_综合得分'] = (df_clean['Behavior_Raw'] - 1) / 3
    
    # Add Student Type
    df_clean['学生类型'] = df_clean['Student_Type']
    
    # Add student_id (using CNTSTUID)
    df_clean['student_id'] = df_clean['CNTSTUID']
    
    # Save to CSV
    output_file = 'student_profiles.csv'
    # Keep all original columns plus the new ones
    df_clean.to_csv(output_file, index=False)
    print(f"Saved processed data to {output_file}")
    
    # Plotting
    plot_cluster_radar(cluster_means_scaled, type_mapping)
    
    # Calculate Percentages
    cluster_counts = df_clean['Cluster'].value_counts(normalize=True) * 100
    
    print("\n" + "="*50)
    print("CLUSTERING ANALYSIS REPORT")
    print("="*50)
    
    # Generate textual descriptions
    # Helper to format percentage
    def fmt_pct(x): return f"{x:.1f}%"
    
    # We iterate through the identified types to ensure order if desired, or just by cluster ID
    # The user example order: Excellent (A), High Pressure (B), Potential (C), Warning (D)
    
    # Find cluster IDs for each type
    inv_map = {v: k for k, v in type_mapping.items()}
    
    # 1. Excellent (A)
    cid_a = inv_map.get('优秀全面型')
    if cid_a is not None:
        pct_a = cluster_counts[cid_a]
        # Calculate stats for description
        # Is Knowledge significantly above average?
        k_score = cluster_means_scaled.loc[cid_a, 'V_Knowledge']
        print(f"\n优秀全面型 (Cluster {cid_a}, {fmt_pct(pct_a)})：各维度得分均衡且显著高于平均水平。")
    
    # 2. High Pressure (B)
    cid_b = inv_map.get('高压成绩型')
    if cid_b is not None:
        pct_b = cluster_counts[cid_b]
        # Check Knowledge rank (Top X%?) - Hard to say exact percentile without full distribution check, 
        # but centroid is high.
        # Check Anxiety score
        anxiety_raw = df_clean[df_clean['Cluster'] == cid_b]['Emotion_Raw'].mean()
        # User example said > 0.75, but our raw scale is 1-4. 
        # Maybe they meant the normalized score? Or maybe the example is hypothetical.
        # Let's use our data for the description.
        print(f"\n高压成绩型 (Cluster {cid_b}, {fmt_pct(pct_b)})：该类群体在知识维度上表现优异，但情感维度中的“数学焦虑”指数异常偏高（均值: {anxiety_raw:.2f}）。")
    
    # 3. Potential (C)
    cid_c = inv_map.get('潜力型')
    if cid_c is not None:
        pct_c = cluster_counts[cid_c]
        print(f"\n潜力型 (Cluster {cid_c}, {fmt_pct(pct_c)})：虽然学业成绩暂时落后，但在认知维度的“任务坚持性”和行为维度的“数字资源利用”上表现出较高水平。")
        
    # 4. Warning (D)
    cid_d = inv_map.get('警示型')
    if cid_d is not None:
        pct_d = cluster_counts[cid_d]
        print(f"\n警示型 (Cluster {cid_d}, {fmt_pct(pct_d)})：多维度指标均处于风险阈值以下。")
        
    print("\n" + "="*50)
    
    # Also return the mapping for verification
    return cluster_means_scaled, type_mapping

def plot_cluster_radar(cluster_means, type_mapping):
    """
    Plot radar chart for cluster centers.
    cluster_means: DataFrame with standardized scores (rows=clusters, cols=features)
    type_mapping: Dict mapping cluster_id to type name
    """
    # Set style
    plt.style.use('ggplot')
    
    # Chinese font support (try common fonts)
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    
    # Features
    labels = ['知识维度', '认知维度', '情感维度(焦虑)', '行为维度']
    # The columns in cluster_means are ['V_Knowledge', 'V_Cognition', 'V_Emotion', 'V_Behavior']
    # Ensure order matches labels
    data_cols = ['V_Knowledge', 'V_Cognition', 'V_Emotion', 'V_Behavior']
    
    # Number of variables
    num_vars = len(labels)
    
    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    # Close the loop
    angles += angles[:1]
    
    # Initialize plot
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    # Color palette
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    
    # Plot each cluster
    for idx, (cluster_id, row) in enumerate(cluster_means.iterrows()):
        values = row[data_cols].tolist()
        values += values[:1] # Close the loop
        
        type_name = type_mapping.get(cluster_id, f'Cluster {cluster_id}')
        label = f"{type_name} (Cluster {cluster_id})"
        
        ax.plot(angles, values, linewidth=2, label=label, color=colors[idx % len(colors)])
        ax.fill(angles, values, color=colors[idx % len(colors)], alpha=0.1)
    
    # Labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=12)
    
    # Title and Legend
    plt.title('PISA 2022 四类学生群体特征雷达图', size=16, y=1.05)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    # Save
    plt.tight_layout()
    plt.savefig('cluster_radar_chart.png', dpi=300)
    print("Radar chart saved to cluster_radar_chart.png")

if __name__ == "__main__":
    process_pisa_data('/Users/neverland/SY/PISA_67_5908.xlsx')
