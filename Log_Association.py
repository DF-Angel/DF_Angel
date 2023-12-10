import sqlite3
from sqlite_db import insert_data_association

class Association:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        connection = sqlite3.connect(self.file_path)
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
            WHERE (EVENT LIKE '%삭제%' OR EVENT LIKE '%포맷%')
            AND EVENT NOT LIKE '%부분 삭제 시작%'
            AND EVENT NOT LIKE '%부분 삭제 종료%'
            OR EVENT LIKE '%부분 삭제 시작 :%'
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
                formatted_row = (
                "부분 삭제 카메라 : CAM " + ', '.join(camera_numbers), None, None, None, datetime_value, None, None, None,
                None, None, None, None, None, 0)
                combined_results.append(formatted_row)

            combined_results.sort(key=lambda x: x[4])

            for i, row in enumerate(combined_results):
                if "부분 삭제 시작" in row[0]:
                    start_row = row
                    camera_row = None
                    user_row = None

                    for j in range(i + 1, len(combined_results)):
                        if "부분 삭제 카메라" in combined_results[j][0]:
                            camera_row = combined_results[j]
                        elif "부분 삭제 사용자" in combined_results[j][0]:
                            user_row = combined_results[j]
                        elif "부분 삭제 마침" in combined_results[j][0]:
                            break

                    if camera_row and user_row:
                        datetime_value = row[4]
                        datetime1 = start_row[0].split(': ')[-1].split(' /')[0].strip()
                        combined_results[i] = (
                            f"{start_row[0]} / {camera_row[0]} / {user_row[0]} / 부분 삭제 행위 : {datetime_value}",
                            *((start_row[j] if start_row[j] is not None else None) for j in range(1, 4)),
                            datetime1, None,
                            *((start_row[j] if start_row[j] is not None else None) for j in range(6, len(start_row)))
                        )

                        combined_results.pop(i + 1)
                        combined_results.pop(i + 1)

                elif "부분 삭제 마침" in row[0]:
                    datetime_value = row[4]
                    datetime2 = row[0].split(': ')[-1].split(' /')[0].strip()
                    combined_results[i] = (
                        f"{row[0]} / 부분 삭제 행위 : {datetime_value}",
                        *((row[j] if row[j] is not None else None) for j in range(1, 4)),
                        datetime2, None,
                        *((row[j] if row[j] is not None else None) for j in range(6, len(row)))
                    )
            combined_results.sort(key=lambda x: x[4])

            for row in combined_results:
                print(row)
                try:
                    insert_data_association(row)
                except Exception as e:
                    print("Error during insertion:", e)

        except sqlite3.Error as e:
            print("SQLite 오류:", e)

        finally:
            connection.close()


association_instance = Association("./IDIS_FS_sqlite.db")
association_instance.parse()
