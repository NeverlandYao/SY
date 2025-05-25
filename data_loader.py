import pandas as pd
import os # 引入 os 库用于构建文件路径

def load_student_data_from_excel_transposed(file_path: str) -> list[dict]:
    """
    从一个转置的文件加载学生数据，进行转置处理，并返回一个字典列表。
    假定 Excel 文件的第一列是属性名称，后续列是每个学生的数据。

    Args:
        file_path: Excel 文件的完整路径。

    Returns:
        一个字典列表，每个字典代表一个学生的完整数据。
        如果文件不存在、为空或读取出错，返回空列表。
    """
    print(f"尝试从路径加载 Excel 文件: {file_path}") # 添加调试输出
    if not os.path.exists(file_path):
        print(f"错误: 文件未找到 at {file_path}")
        return []

    try:
        # 读取 Excel 文件。
        # header=None 表示文件没有专门的标题行。
        # index_col=0 表示将第一列（索引为 0 的列）作为 DataFrame 的索引。
        # 转置后，原来的索引列将变成新的列名。
        # sheet_name=0 读取第一个工作表。
        df = pd.read_excel(file_path, header=None, index_col=0, sheet_name=0)
        print("Excel 文件读取成功（原始数据）")

        # 转置 DataFrame
        # .T 是转置操作的属性
        df_transposed = df.T
        print("DataFrame 转置成功")

        # 将转置后的 DataFrame 转换为字典列表
        # orient='records' 参数会将 DataFrame 的每一行转换为一个字典，
        # 然后把这些字典收集到一个列表中。
        data = df_transposed.to_dict(orient='records')
        print(f"成功从转置文件中加载 {len(data)} 条学生记录")

        # !!! 调试关键步骤：检查加载数据的键 !!!
        if data:
             print("第一条学生记录的键（从转置文件加载后）:", data[0].keys())
             # 可选：打印第一条记录的部分数据看看值对不对
             # print("第一条学生记录的部分数据样本:", list(data[0].items())[:10])
        else:
             print("加载数据列表为空，请检查 Excel 内容和读取逻辑。")


        return data

    except FileNotFoundError:
        # 这个异常已经被前面的 os.path.exists 检查捕获，但保留以防万一
        print(f"错误: Excel 文件未找到 at {file_path}")
        return []
    except pd.errors.EmptyDataError:
        print(f"错误: Excel 文件为空 at {file_path}")
        return []
    except Exception as e:
        print(f"读取和处理转置 Excel 文件时发生错误: {e}")
        # 打印更详细的错误信息，比如 traceback
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    # 定义Excel文件路径
    excel_file_path = 'Model_py.xlsx' 

    # 从Excel文件加载学生数据
    student_list_raw = load_student_data_from_excel_transposed(excel_file_path)

    # 此处预留，用于将来的操作
    pass
