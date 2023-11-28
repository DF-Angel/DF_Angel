import sqlite3
import os

def connect_db():
    db_path = "./IDIS_FS_sqlite.db"
    return sqlite3.connect(db_path, isolation_level=None)


def del_db():
    db_path = "./IDIS_FS_sqlite.db"
    if os.path.exists(db_path):
        os.remove(db_path)


def create_table(table_name, columns):
    conn = connect_db()
    c = conn.cursor()

    # 테이블 생성
    c.execute(f'''
        CREATE TABLE {table_name} (
            idx INTEGER PRIMARY KEY AUTOINCREMENT,
            {columns}
        );
    ''')

    # 연결 종료
    conn.commit()
    conn.close()


def insert_data_root_scan(name, ch, start_time, end_time, start_offset, end_offset, size):
    conn = connect_db()
    c = conn.cursor()

    c.execute('''
        INSERT INTO ROOT_SCAN (NAME, CH, START_TIME, END_TIME, START_OFFSET, END_OFFSET, SIZE)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    ''', (name, ch, start_time, end_time, start_offset, end_offset, size))

    conn.commit()
    conn.close()


def insert_data_precise_scan(name, block, ch, start_time, end_time,duration, start_offset, end_offset,size, del_type, i_frame, p_frame, is_it_del):
    conn = connect_db()
    c = conn.cursor()

    c.execute('''
        INSERT INTO PRECISE_SCAN (NAME , BLOCK , CH , START_TIME , END_TIME , DURATION , START_OFFSET , END_OFFSET ,SIZE, DEL_TYPE, I_FRAME, P_FRAME, IS_IT_DEL)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    ''', (name, block, ch, start_time, end_time,duration, start_offset, end_offset,size, del_type, i_frame, p_frame, is_it_del))

    conn.commit()
    conn.close()


def insert_data_log(EVENT, DATETIME):
    conn = connect_db()
    c = conn.cursor()

    c.execute('''
        INSERT INTO LOG (EVENT, DATETIME)
        VALUES (?, ?);
    ''', (EVENT, DATETIME))

    conn.commit()
    conn.close()

# 데이터베이스 초기화
del_db()

# ROOTSCAN 테이블 생성
create_table("ROOT_SCAN",
             "NAME INTEGER, CH INTEGER, START_TIME TEXT, END_TIME TEXT, START_OFFSET INTEGER, END_OFFSET INTEGER, SIZE INTEGER")

# ALLOCATION 테이블 생성
create_table("PRECISE_SCAN",
             "NAME TEXT, BLOCK INTEGER, CH INTEGER, START_TIME TEXT, END_TIME TEXT, DURATION TEST, START_OFFSET INTEGER, END_OFFSET INTEGER, SIZE INTEGER, DEL_TYPE INTEGER, I_FRAME INTEGER, P_FRAME INTEGER, IS_IT_DEL INTEGER")


create_table("LOG",
             "EVENT TEXT, DATETIME TEXT")
