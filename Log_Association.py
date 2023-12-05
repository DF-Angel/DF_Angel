import sqlite3
from sqlite_db import *

db_file_path = "./IDIS_FS_sqlite.db"

connection = sqlite3.connect(db_file_path)
cursor = connection.cursor()

combined_results = []

try:
    query_precise_scan = "SELECT * FROM PRECISE_SCAN WHERE IS_IT_DEL = 1"
    cursor.execute(query_precise_scan)

    rows_precise_scan = cursor.fetchall()

    for row in rows_precise_scan:
        combined_results.append(row[1:] + (1,))
       
        

    query_log = "SELECT EVENT, NULL, NULL, NULL, DATETIME, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0 FROM LOG WHERE EVENT LIKE '%삭제%' OR EVENT LIKE '%포맷%' OR EVENT LIKE '%클립%' OR EVENT LIKE '%시스템%' OR EVENT LIKE '%설정 변경%'"
    cursor.execute(query_log)

    rows_log = cursor.fetchall()

    combined_results.extend(rows_log)

    combined_results = sorted(combined_results, key=lambda x: x[4])

    for row in combined_results:
        print(row)
        insert_data_association(row)
            


except sqlite3.Error as e:
    print("SQLite 오류:", e)

finally:
    connection.close()
