from datetime import datetime, timedelta
from sqlite_db import *

idx = 1

def convert_to_datetime(time_info):
    try:
        time_info_bin = bin(time_info)[2:]

        sec = int(time_info_bin[-6:], 2)
        min = int(time_info_bin[-12:-6], 2)
        hour = int(time_info_bin[-17:-12], 2)
        day = int(time_info_bin[-22:-17], 2)
        month = int(time_info_bin[-26:-22], 2)
        year = int(time_info_bin[:-26], 2) + 1970
        return datetime(year, month, day, hour, min, sec)
    except ValueError:
        return 0  # 파일을 찾을 수 없을 때 0을 반환

def process_frame_set(frame_set, status, block_cnt, AU, file):#AU는 할당/비할당
    #print(hex(frame_set[-1]["frame_offset"]))
    global idx
    # Process and organize the complete set of frames
    base = 0x80100000 + 0x10000000 * block_cnt + 0x500000
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
        del_type = "모든 데이터 삭제 / 부분 삭제 / 자동 삭제"
    elif status == 3:
        del_type = "포맷"
    elif status == 4:
        del_type = "Slack(Unknown)"

    duration = str(frame_set[-1]["frame_time"] - frame_set[0]["frame_time"] + timedelta(seconds=1))

    i_frame_cnt = 0
    p_frame_cnt = 0
    size = 0



    if status == 4:
        data = b''
        for frame in frame_set:
            file.seek(frame["h264_frame_offset"], 0)
            data += file.read(frame["h264_frame_size"])
            if frame["frame_type"] == 0:
                i_frame_cnt += 1
                size += frame["frame_size"] + 0xA1
            elif frame["frame_type"] == 1:
                p_frame_cnt += 1
                size += frame["frame_size"] + 0xA1
        output_file = open('./'+str(idx)+'.bin', 'rb')
        output_file.write(data)
        insert_data_precise_scan(str(frame_set[0]["frame_time"]) + " ~ " + str(frame_set[-1]["frame_time"]), block_cnt,
                                 frame_set[0]["frame_channel"], str(frame_set[0]["frame_time"]),
                                 str(frame_set[-1]["frame_time"]), duration, frame_set[0]["real_frame_offset"],
                                 frame_set[-1]["real_frame_offset"] + frame_set[-1]["frame_size"] + 0xA1, size,
                                 status, i_frame_cnt,
                                 p_frame_cnt, AU)
    else:
        for frame in frame_set:
            if frame["frame_type"] == 0:
                i_frame_cnt += 1
                size += frame["frame_size"] + 0xA1
            elif frame["frame_type"] == 1:
                p_frame_cnt += 1
                size += frame["frame_size"] + 0xA1

        insert_data_precise_scan(str(frame_set[0]["frame_time"]) + " ~ " + str(frame_set[-1]["frame_time"]), block_cnt,
                             frame_set[0]["frame_channel"], str(frame_set[0]["frame_time"]),
                             str(frame_set[-1]["frame_time"]), duration, base + frame_set[0]["frame_offset"],
                             base + frame_set[-1]["frame_offset"] + frame_set[-1]["frame_size"] + 0xA1, size, status, i_frame_cnt,
                             p_frame_cnt, AU)
    idx += 1
