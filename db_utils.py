import mysql.connector
import pandas as pd
from config import db_config

def create_database():
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        mycursor = mydb.cursor()
        mycursor.execute("CREATE DATABASE IF NOT EXISTS mydatabase")
        print("Database created successfully")
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")

def create_students_table():
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database='mydatabase'
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
        print("Students table created successfully")
    except mysql.connector.Error as err:
        print(f"Error creating students table: {err}")

def create_recommendations_table():
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database='mydatabase'
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
        print("Recommendations table created successfully")
    except mysql.connector.Error as err:
        print(f"Error creating recommendations table: {err}")

def insert_student_data(student_data):
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database='mydatabase'
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
        print(f"Student data inserted successfully for student ID: {student_data['student_id']}")
    except mysql.connector.Error as err:
        print(f"Error inserting student data: {err}")

def insert_recommendation_data(student_id, dimension, recommendation):
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database='mydatabase'
        )
        mycursor = mydb.cursor()

        insert_statement = """
        INSERT INTO recommendations (student_id, dimension, recommendation)
        VALUES (%s, %s, %s)
        """

        values = (student_id, dimension, recommendation)

        mycursor.execute(insert_statement, values)
        mydb.commit()
        print(f"Recommendation inserted successfully for student ID: {student_id}, dimension: {dimension}")
    except mysql.connector.Error as err:
        print(f"Error inserting recommendation data: {err}")

def import_excel_data(file_path, table_name):
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database='mydatabase'
        )
        mycursor = mydb.cursor()

        df = pd.read_excel(file_path)

        # Determine column types from DataFrame
        column_types = {}
        for col in df.columns:
            if pd.api.types.is_integer_dtype(df[col]):
                column_types[col] = "INT"
            elif pd.api.types.is_float_dtype(df[col]):
                column_types[col] = "FLOAT"
            else:
                column_types[col] = "TEXT"

        # Create table
        create_table(table_name, column_types)

        # Prepare the INSERT statement
        columns = ', '.join(df.columns)
        placeholders = ', '.join(['%s'] * len(df.columns))
        insert_statement = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # Execute the INSERT statement for each row
        for _, row in df.iterrows():
            try:
                mycursor.execute(insert_statement, tuple(row))
            except mysql.connector.Error as err:
                print(f"Error inserting row: {err}")

        mydb.commit()
        print("Excel data imported successfully")
    except mysql.connector.Error as err:
        print(f"Error importing Excel data: {err}")
    except FileNotFoundError:
        print(f"Error: File not found at path: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def store_text_data(table_name, text_data):
    try:
        mydb = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database='mydatabase'
        )
        mycursor = mydb.cursor()

        # Insert into the first column of the table
        # Assuming the first column is a suitable place to store the text data
        df = pd.read_excel('Model_py.xlsx')
        first_column = df.columns[0]
        insert_statement = f"INSERT INTO {table_name} ({first_column}) VALUES (%s)"
        mycursor.execute(insert_statement, (text_data,))

        mydb.commit()
        print("Text data stored successfully")
    except mysql.connector.Error as err:
        print(f"Error storing text data: {err}")

if __name__ == '__main__':
    create_database()
    create_students_table()
    create_recommendations_table()
    # import_excel_data('Model_py.xlsx', 'model_data')
    # store_text_data('model_data', 'This is a sample text data.')
