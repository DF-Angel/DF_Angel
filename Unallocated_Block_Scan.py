from CommonFunction import *
from sqlite_db import *
from datetime import timedelta

class Unallocated_Block_Scan:
    def __init__(self):
        self.all_del_condition = None

    def all_del(self, block_start_time, block_end_time, block_cnt, file, ADC):
        self.all_del_condition = ADC
        frame_set = []  # List to store frames in a set
        status = 0
        block_end = 0
        allocated_block_end = 1
        frame_meta = file.read(32)
        if int.from_bytes(frame_meta) == 0x00:
            return
        frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
        frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
        frame_channel = frame_meta[0x18]
        frame_type = frame_meta[0x1A]
        frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')

        start_frame_time = frame_time
        bef_frame_time = 0
        bef_frame_offset = 0
        # 할당 블록의 시작 프레임부터 비할당 프레임인 경우 -> 부분 삭제(앞)
        if block_start_time > frame_time:
            status = 1
            frame_set = [
                {
                    "frame_time": frame_time,
                    "frame_size": frame_size,
                    "frame_channel": frame_channel,
                    "frame_type": frame_type,
                    "frame_offset": frame_offset,
                }
            ]
            frame_meta = file.read(32)
            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            while frame_time != block_start_time:
                # Modify 203-12-02
                if len(frame_set) != 0 and frame_time >= frame_set[-1]["frame_time"] + timedelta(seconds=2):
                    process_frame_set(frame_set, status, block_cnt, 0)
                    frame_set = [
                        {
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    ]
                else:
                    frame_set.append(
                        {
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    )
                frame_meta = file.read(32)
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            #print("Block : " + str(block_cnt) + ", ", end='')
            process_frame_set(frame_set, status, block_cnt, 1)
            status = 0
            frame_set = []
            #file.seek(-32, 1)
            #status = 0
        file.seek(-32, 1)

        #할당 및 중간 부분 삭제
        while allocated_block_end:
            stauts = 2
            frame_meta = file.read(32)
            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')

            if frame_time == block_end_time:
                # End of frames in the current set
                while frame_time == block_end_time:
                    frame_set.append(
                        {
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    )
                    bef_frame_time = frame_time
                    bef_frame_offset = frame_offset
                    frame_meta = file.read(32)
                    if int.from_bytes(frame_meta[:32]) == 0x00:
                        block_end = 1
                        #print("Block : " + str(block_cnt) + ", ", end='')
                        process_frame_set(frame_set, status, block_cnt, 1)
                    #    block_end = 1
                        return
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                #print("Block : " + str(block_cnt) + ", ", end='')
                process_frame_set(frame_set, status, block_cnt, 1)

                if not(start_frame_time <= frame_time <= block_end_time):
                    frame_set = [
                            {
                                "frame_time": frame_time,
                                "frame_size": frame_size,
                                "frame_channel": frame_channel,
                                "frame_type": frame_type,
                                "frame_offset": frame_offset,
                            }
                        ]
                    bef_frame_time = frame_time
                    bef_frame_offset = frame_offset
                break


            if frame_size == 0:
                #print("Block : " + str(block_cnt) + ", ", end='')
                process_frame_set(frame_set, status, block_cnt, 1)
                status = 1
                frame_set = []
                while frame_size == 0:
                    # Modify 203-12-02
                    if len(frame_set) != 0 and frame_time >= frame_set[-1]["frame_time"] + timedelta(seconds=2):
                        process_frame_set(frame_set, status, block_cnt, 0)
                        frame_set = [
                            {
                                "frame_time": frame_time,
                                "frame_size": frame_size,
                                "frame_channel": frame_channel,
                                "frame_type": frame_type,
                                "frame_offset": frame_offset,
                            }
                        ]
                    else:
                        frame_set.append(
                            {
                                "frame_time": frame_time,
                                "frame_size": frame_size,
                                "frame_channel": frame_channel,
                                "frame_type": frame_type,
                                "frame_offset": frame_offset,
                            }
                        )
                    bef_frame_time = frame_time
                    bef_frame_offset = frame_offset
                    frame_meta = file.read(32)
                    if int.from_bytes(frame_meta) == 0x00:
                        #print("Block : " + str(block_cnt) + ", ", end='')
                        file_loc = file.tell()
                        file.seek(0x80100000 + block_cnt * 0x10000000 + 0x500000 + frame_set[-1]["frame_offset"], 0)
                        frame_set[-1]["frame_size"] = int.from_bytes(file.read(32)[0x10:0x14], byteorder="little")
                        file.seek(file_loc, 0)
                        process_frame_set(frame_set, status, block_cnt, 1)
                        return
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                    if frame_set[-1]["frame_time"] > frame_time:
                        file_loc = file.tell()
                        file.seek(0x80100000 + block_cnt * 0x10000000 + 0x500000 + frame_set[-1]["frame_offset"], 0)
                        frame_set[-1]["frame_size"] = int.from_bytes(file.read(32)[0x10:0x14], byteorder="little")
                        file.seek(file_loc, 0)
                        allocated_block_end = 0
                        break
                    frame_set[-1]["frame_size"] = frame_offset - frame_set[-1]["frame_offset"] - 0xC4
                #print("Block : " + str(block_cnt) + ", ", end='')
                process_frame_set(frame_set, status, block_cnt, 1)
                status = 0
                if not(start_frame_time <= frame_time <= block_end_time):
                    frame_set = [
                        {
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    ]
                    bef_frame_time = frame_time
                    bef_frame_offset = frame_offset
                status = 0
                continue
            # Modify 203-12-02
            if len(frame_set) != 0 and frame_time >= frame_set[-1]["frame_time"] + timedelta(seconds=2):
                process_frame_set(frame_set, status, block_cnt, 0)
                frame_set = [
                    {
                        "frame_time": frame_time,
                        "frame_size": frame_size,
                        "frame_channel": frame_channel,
                        "frame_type": frame_type,
                        "frame_offset": frame_offset,
                    }
                ]
            else:
                frame_set.append(
                    {
                        "frame_time": frame_time,
                        "frame_size": frame_size,
                        "frame_channel": frame_channel,
                        "frame_type": frame_type,
                        "frame_offset": frame_offset,
                    }
                )
            bef_frame_time = frame_time
            bef_frame_offset = frame_offset
        # 부분 삭제(끝)
        if frame_set[0]["frame_time"] > block_end_time:
            status = 1
            frame_meta = file.read(32)
            if int.from_bytes(frame_meta[:32]) == 0x00:
                #print("Block : " + str(block_cnt) + ", ", end='')
                process_frame_set(frame_set, status, block_cnt, 1)
                status = 0
                return
            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            while frame_set[-1]["frame_time"] <= frame_time:
                # Modify 203-12-02
                if len(frame_set) != 0 and frame_time >= frame_set[-1]["frame_time"] + timedelta(seconds=2):
                    process_frame_set(frame_set, status, block_cnt, 0)
                    frame_set = [
                        {
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    ]
                else:
                    frame_set.append(
                        {
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    )
                frame_meta = file.read(32)
                if int.from_bytes(frame_meta[:32]) == 0x00:
                    #print("Block : " + str(block_cnt) + ", ", end='')
                    process_frame_set(frame_set, status, block_cnt, 1)
                    status = 0
                    block_end = 1
                    return
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            #print("Block : " + str(block_cnt) + ", ", end='')
            process_frame_set(frame_set, status, block_cnt, 1)
            file.seek(-32, 1)
        self.slack(block_cnt, start_frame_time, frame_set[-1]["frame_time"], frame_set[-1]["frame_offset"], file)

            #if block_end == 0:
                #print('')

    def format(self, block_cnt, file):
        frame_meta = file.read(32)
        if int.from_bytes(frame_meta) == 0x00:
            return
        frame_set = []
        status = 3
        if int.from_bytes(frame_meta) == 0x00:
            return
        else:
            start_frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            bef_frame_time = start_frame_time
            bef_frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            file.seek(-32, 1)
            while True:
                frame_meta = file.read(32)
                if int.from_bytes(frame_meta) == 0x00:
                    process_frame_set(frame_set, status, block_cnt, 1)
                    break
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                if bef_frame_time > frame_time:
                        self.process_frame_set(frame_set, status, block_cnt, 1)
                        file.seek(-32)
                        self.slack(block_cnt, start_frame_time, bef_frame_time, bef_frame_offset, file)
                else:
                    bef_frame_time = frame_time
                    bef_frame_offset = frame_offset
                    frame_set.append(
                        {
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    )
#시간 반전 일어나기 전까지 다 읽기
#이전 블록의 시작과 끝 시간정보 들고 있기
#이전 블록의 시작 시간정보보다 더 과거의 시간정보를 지니고 있는 프레임이 등장할 때까지 버리기
    def slack(self, block_cnt, start_frame_time, end_frame_time, end_frame_offset, file):
        return
        frame_set = []
        bef_frame_time = 0
        bef_frame_offset = 0
        status = 4
        #썸네일 추정 중복 프레임 및 유효하지 않은 프레임 오프셋 제거
        while True:
            frame_meta = file.read(32)
            file_loc = file.tell()
            #print(frame_meta)
            if int.from_bytes(frame_meta) == 0x00:
                return

            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            if frame_time == 0:
                return
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            #Modify Point
            #if frame_offset == 0x00:
            #    return
            if start_frame_time <= frame_time <= end_frame_time or frame_offset <= end_frame_offset:
                continue
            else:
                start_frame_time = frame_time
                bef_frame_time = frame_time
                file.seek(-32, 1)
                break

        #슬랙에 존재하는 유효한 프레임 분석

        while True:
            frame_meta = file.read(32)
            if int.from_bytes(frame_meta) == 0x00:
                #print("Block : " + str(block_cnt) + ", ", end='')
                process_frame_set(frame_set, status, block_cnt, 1)
                return
            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            if bef_frame_time > frame_time:
                #print("Block : " + str(block_cnt) + ", ", end='')
                process_frame_set(frame_set, status, block_cnt, 1)
                file.seek(-32, 1)
                self.slack(block_cnt, start_frame_time, bef_frame_time, bef_frame_offset, file)
                break
            else:
                bef_frame_time = frame_time
                bef_frame_offset = frame_offset
                frame_set.append(
                    {
                        "frame_time": frame_time,
                        "frame_size": frame_size,
                        "frame_channel": frame_channel,
                        "frame_type": frame_type,
                        "frame_offset": frame_offset,
                    }
                )

    def new_slack(self, slack_start_offset, block_cnt, ch, file):
        i_frame_sig = b'\x00\x00\x00\x01\x65'
        p_frame_sig = b'\x00\x00\x00\x01\x21'

        known_frame_set = []
        unknown_frame_set = []

        slack_end_offset = (block_cnt + 1) * 0x10000000 + 0x80100000

        file.seek(slack_start_offset, 0)
        slack_data = file.read(slack_end_offset - slack_start_offset)

        frame_sig_offsets = []
        frame_type_mapping = {b'\x00\x00\x00\x01\x65': 0, b'\x00\x00\x00\x01\x21': 1}


        for frame_type, frame_type_value in frame_type_mapping.items():
            index = 0

            while True:
                index = slack_data.find(frame_type, index)

                if index == -1:
                    break

                frame_sig_offsets.append((slack_start_offset + index, frame_type_value))
                index += 1

        sorted_frame_sig_offset = sorted(frame_sig_offsets, key=lambda x: x[0])


        for i in range(len(sorted_frame_sig_offset)):
            if sorted_frame_sig_offset[i][1] == 0:
                frame_meta = slack_data[sorted_frame_sig_offset[i][0] - slack_start_offset - 0xDB: sorted_frame_sig_offset[i][0] - slack_start_offset + 0x20]
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                if (
                    frame_time != 0 and
                    frame_offset == sorted_frame_sig_offset[i][0] - 0x806000DB - (block_cnt * 0x10000000) and
                    #frame_time < last_frame_time and
                    frame_type == 0 and
                    0 <= frame_channel <= ch and
                    0 <= frame_size <= (slack_end_offset - sorted_frame_sig_offset[i][0])
                ):
                    known_frame_set.append(
                        {
                            "real_frame_offset": sorted_frame_sig_offset[i][0] - 0x17,
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    )
                else:
                    if i == len(sorted_frame_sig_offset) - 1:
                        unknown_frame_set.append((sorted_frame_sig_offset[i][0], slack_end_offset - 1))
                    else:
                        unknown_frame_set.append((sorted_frame_sig_offset[i][0], sorted_frame_sig_offset[i + 1][0] - sorted_frame_sig_offset[i][0]))
            elif sorted_frame_sig_offset[i][1] == 1:
                frame_meta = slack_data[sorted_frame_sig_offset[i][0] - slack_start_offset - 0xC4: sorted_frame_sig_offset[i][0] - slack_start_offset + 0x20]
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                if (
                        frame_time != 0 and
                        frame_offset == sorted_frame_sig_offset[i][0] - 0x806000C4 - (block_cnt * 0x10000000) and
                        # frame_time < last_frame_time and
                        frame_type == 1 and
                        0 <= frame_channel <= ch and
                        0 <= frame_size <= (slack_end_offset - sorted_frame_sig_offset[i][0])
                ):
                    known_frame_set.append(
                        {
                            "real_frame_offset": sorted_frame_sig_offset[i][0],
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    )
                else:
                    if i == len(sorted_frame_sig_offset) - 1:
                        unknown_frame_set.append((sorted_frame_sig_offset[i][0], slack_end_offset - 1))
                    else:
                        unknown_frame_set.append((sorted_frame_sig_offset[i][0],
                                                  sorted_frame_sig_offset[i + 1][0] - sorted_frame_sig_offset[i][0]))