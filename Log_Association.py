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

    query_log = """
    SELECT EVENT, NULL, NULL, NULL, DATETIME, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0
    FROM LOG
    WHERE (EVENT LIKE '%삭제%' OR EVENT LIKE '%포맷%' OR EVENT LIKE '%클립%' OR EVENT LIKE '%시스템%' OR EVENT LIKE '%설정 변경%')
      AND EVENT NOT LIKE '%부분 삭제 종료%'
    """

    cursor.execute(query_log)

    rows_log = cursor.fetchall()

    combined_dict = {}

    for row in rows_log:
        event_text = row[0]
        datetime_value = row[4]

        if "부분 삭제 카메라" in event_text:
            camera_numbers = set(filter(str.isdigit, event_text))
            camera_numbers_str = ', '.join(sorted(camera_numbers, key=int))

            if datetime_value in combined_dict:
                combined_dict[datetime_value].append(camera_numbers_str)
            else:
                combined_dict[datetime_value] = [camera_numbers_str]
        else:
            combined_results.append(row)

    for datetime_value, camera_numbers in combined_dict.items():
        formatted_row = ("부분 삭제 카메라 : CAM " + ', '.join(camera_numbers), None, None, None, datetime_value, None, None, None, None, None, None, None, None, 0)
        combined_results.append(formatted_row)

    combined_results = sorted(combined_results, key=lambda x: x[4])

    for row in combined_results:
        print(row)
        # insert_data_association(row)

except sqlite3.Error as e:
    print("SQLite 오류:", e)

finally:
    connection.close()
