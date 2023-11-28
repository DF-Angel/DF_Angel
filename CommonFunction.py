from datetime import datetime, timedelta
from sqlite_db import *

def convert_to_datetime(time_info):
    time_info_bin = bin(time_info)[2:]

    sec = int(time_info_bin[-6:], 2)
    min = int(time_info_bin[-12:-6], 2)
    hour = int(time_info_bin[-17:-12], 2)
    day = int(time_info_bin[-22:-17], 2)
    month = int(time_info_bin[-26:-22], 2)
    year = int(time_info_bin[:-26], 2) + 1970

    try:
        return datetime(year, month, day, hour, min, sec)
    except ValueError:
        return 0  # 파일을 찾을 수 없을 때 0을 반환

def process_frame_set(frame_set, status, block_cnt, AU):
    # Process and organize the complete set of frames
    start_time = frame_set[0]["frame_time"]
    last_time = frame_set[-1]["frame_time"]
    channel = frame_set[0]["frame_channel"]
    start_offset = hex(frame_set[0]["frame_offset"])
    last_offset = hex(frame_set[-1]["frame_offset"])
    del_type = ''
    if status == 0:
        del_type = "할당"
    elif status == 1:
        del_type = "부분 삭제"
    elif status == 2:
        del_type = "모든 데이터 삭제 / 부분 삭제"
    elif status == 3:
        del_type = "포맷"
    elif status == 4:
        del_type = "Slack(Unknown)"

    # Perform further actions as needed with the organized frame set
    #print(f"Start Time: {start_time}, Last Time: {last_time}, Channel: {channel}, Start Offset: {start_offset}, Last Offset: {last_offset}, Del Type: {del_type}")
    #print(f"Block : {block_cnt}, Start Time: {start_time}, Last Time: {last_time}, Channel: {channel}, Del Type: {del_type}")
    unique_frame_time_count = len(set(frame["frame_time"] for frame in frame_set))
    duration = str(timedelta(seconds=unique_frame_time_count))

    i_frame_cnt = 0
    p_frame_cnt = 0
    size = 0
    for frame in frame_set:
        if frame["frame_type"] == 0:
            i_frame_cnt += 1
        elif frame["frame_type"] == 1:
            p_frame_cnt += 1
        size += frame["frame_size"] - 0x23

    insert_data_precise_scan(str(frame_set[0]["frame_time"]) + " ~ " + str(frame_set[-1]["frame_time"]), block_cnt,
                             frame_set[0]["frame_channel"], str(frame_set[0]["frame_time"]),
                             str(frame_set[-1]["frame_time"]), duration, frame_set[0]["frame_offset"],
                             frame_set[-1]["frame_offset"] + frame_set[-1]["frame_size"] + 0xA0, size, status, i_frame_cnt,
                             p_frame_cnt, AU)
