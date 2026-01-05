import mysql.connector
import pandas as pd
from config import db_config

def create_database():
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            port=db_config.get('port', 3306),
            user=db_config['user'],
            password=db_config['password']
        )
        mycursor = mydb.cursor()
        mycursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        print(f"数据库 {db_config['database']} 创建成功")
    except mysql.connector.Error as err:
        print(f"创建数据库出错: {err}")

def create_students_table():
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            port=db_config.get('port', 3306),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        mycursor = mydb.cursor()

        create_table_statement = """
        CREATE TABLE IF NOT EXISTS students (
            student_id INT PRIMARY KEY,
            student_type VARCHAR(255),
            knowledge_score FLOAT,
            cognitive_score FLOAT,
            affective_score FLOAT,
            behavioral_score FLOAT,
            expert_diagnosis TEXT,
            risk_level VARCHAR(255),
            risk_factors TEXT,
            CNTSTUID INT,
            ST004D01T INT,
            ST001D01T INT,
            PV1MATH FLOAT,
            PV1READ FLOAT,
            PV1SCIE FLOAT,
            ST099Q01TA INT,
            ST099Q02TA INT,
            ST099Q03TA INT,
            ST099Q04TA INT
        )
        """

        mycursor.execute(create_table_statement)
        mydb.commit()
        print("学生表创建成功")
    except mysql.connector.Error as err:
        print(f"创建学生表出错: {err}")

def create_recommendations_table():
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            port=db_config.get('port', 3306),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        mycursor = mydb.cursor()

        create_table_statement = """
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT,
            dimension VARCHAR(255),
            recommendation TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
        """

        mycursor.execute(create_table_statement)
        mydb.commit()
        print("推荐表创建成功")
    except mysql.connector.Error as err:
        print(f"创建推荐表出错: {err}")

def insert_student_data(student_data):
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            port=db_config.get('port', 3306),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        mycursor = mydb.cursor()

        insert_statement = """
        INSERT INTO students (
            student_id, student_type, knowledge_score, cognitive_score,
            affective_score, behavioral_score, expert_diagnosis, risk_level,
            risk_factors, CNTSTUID, ST004D01T, ST001D01T, PV1MATH, PV1READ,
            PV1SCIE, ST099Q01TA, ST099Q02TA, ST099Q03TA, ST099Q04TA
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            student_data['student_id'], student_data['student_type'],
            student_data['knowledge_score'], student_data['cognitive_score'],
            student_data['affective_score'], student_data['behavioral_score'],
            student_data['expert_diagnosis'], student_data['risk_level'],
            student_data['risk_factors'], student_data['CNTSTUID'],
            student_data['ST004D01T'], student_data['ST001D01T'],
            student_data['PV1MATH'], student_data['PV1READ'],
            student_data['PV1SCIE'], student_data['ST099Q01TA'],
            student_data['ST099Q02TA'], student_data['ST099Q03TA'],
            student_data['ST099Q04TA']
        )

        mycursor.execute(insert_statement, values)
        mydb.commit()
        print(f"学生数据插入成功，学生ID: {student_data['student_id']}")
    except mysql.connector.Error as err:
        print(f"插入学生数据出错: {err}")

def insert_recommendation_data(student_id, dimension, recommendation):
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            port=db_config.get('port', 3306),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        mycursor = mydb.cursor()

        insert_statement = """
        INSERT INTO recommendations (student_id, dimension, recommendation)
        VALUES (%s, %s, %s)
        """

        values = (student_id, dimension, recommendation)

        mycursor.execute(insert_statement, values)
        mydb.commit()
        print(f"推荐数据插入成功，学生ID: {student_id}, 维度: {dimension}")
    except mysql.connector.Error as err:
        print(f"插入推荐数据出错: {err}")

def import_excel_data(file_path, table_name):
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            port=db_config.get('port', 3306),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        mycursor = mydb.cursor()

        df = pd.read_excel(file_path)

        # 从 DataFrame 确定列类型
        column_types = {}
        for col in df.columns:
            if pd.api.types.is_integer_dtype(df[col]):
                column_types[col] = "INT"
            elif pd.api.types.is_float_dtype(df[col]):
                column_types[col] = "FLOAT"
            else:
                column_types[col] = "TEXT"

        # 创建表
        create_table(table_name, column_types)

        # 准备 INSERT 语句
        columns = ', '.join(df.columns)
        placeholders = ', '.join(['%s'] * len(df.columns))
        insert_statement = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # 为每一行执行 INSERT 语句
        for _, row in df.iterrows():
            try:
                mycursor.execute(insert_statement, tuple(row))
            except mysql.connector.Error as err:
                print(f"Error inserting row: {err}")

        mydb.commit()
        print("Excel数据导入成功")
    except mysql.connector.Error as err:
        print(f"导入Excel数据出错: {err}")
    except FileNotFoundError:
        print(f"错误: 文件未找到，路径: {file_path}")
    except Exception as e:
        print(f"发生意外错误: {e}")

def store_text_data(table_name, text_data):
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            port=db_config.get('port', 3306),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        mycursor = mydb.cursor()

        # 插入到表的第一列
        df = pd.read_excel('Model_py.xlsx')
        first_column = df.columns[0]
        insert_statement = f"INSERT INTO {table_name} ({first_column}) VALUES (%s)"
        mycursor.execute(insert_statement, (text_data,))

        mydb.commit()
        print("文本数据存储成功")
    except mysql.connector.Error as err:
        print(f"存储文本数据出错: {err}")

if __name__ == '__main__':
    create_database()
    create_students_table()
    create_recommendations_table()