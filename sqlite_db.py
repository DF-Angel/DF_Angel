import sqlite3
import os

print(sqlite3.version)
print(sqlite3.sqlite_version)

conn = sqlite3.connect("./IDIS_FS_sqlite.db", isolation_level=None)
c = conn.cursor()

def ALLOCATION_create_table():
    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='ALLOCATION';''')
    table_exists = c.fetchone()

    if table_exists:
        # 테이블이 이미 존재하면 삭제
        c.execute('DROP TABLE ALLOCATION;')
    # 테이블 생성
    c.execute('''
            CREATE TABLE ALLOCATION (
                idx INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME TEXT,
                CH INTEGER,
                START_TIME TEXT,
                END_TIME TEXT,
                TOTAL_TIME TEXT,
                START_OFFSET INTEGER,
                END_OFFSET INTEGER,
                SIZE INTEGER
            );
        ''')
    # 연결 종료
    conn.commit()
    conn.close()

def insert_data(name, ch, start_time, end_time, total_time, start_offset, end_offset, size):
    # timedelta를 문자열로 변환
    total_time_str = str(total_time)

    conn = sqlite3.connect("./IDIS_FS_sqlite.db", isolation_level=None)
    c = conn.cursor()

    c.execute('''
        INSERT INTO ALLOCATION (NAME, CH, START_TIME, END_TIME, TOTAL_TIME, START_OFFSET, END_OFFSET, SIZE)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    ''', (name, ch, start_time, end_time, total_time_str, start_offset, end_offset, size))

    conn.commit()
    conn.close()

ALLOCATION_create_table()
