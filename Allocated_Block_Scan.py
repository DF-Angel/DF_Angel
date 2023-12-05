from CommonFunction import *
from datetime import timedelta
from Unallocated_Block_Scan import Unallocated_Block_Scan
from sqlite_db import *

class Allocated_Block_Scan:
    def analyzer(self, block_start_time, block_end_time, block_cnt, file):
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
                #Modify 203-12-02
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
                #print(frame_time)
            #print("Block : " + str(block_cnt) + ", ", end='')
            process_frame_set(frame_set, status, block_cnt, 0)
            status = 0
            frame_set = []
        file.seek(-32, 1)

        #할당 및 중간 부분 삭제
        while allocated_block_end:
            #print(hex(file.tell()))
            frame_meta = file.read(32)
            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            #print(frame_time)
            #print(block_end_time)
            #print('')
            if frame_time == block_end_time:
                # End of frames in the current set
                while frame_time == block_end_time:
                    #print(frame_time)
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
                        process_frame_set(frame_set, status, block_cnt, 0)
                    #    block_end = 1
                        return
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                #print("Block : " + str(block_cnt) + ", ", end='')
                process_frame_set(frame_set, status, block_cnt, 0)

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
                process_frame_set(frame_set, status, block_cnt, 0)
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
                        process_frame_set(frame_set, status, block_cnt, 0)
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
                process_frame_set(frame_set, status, block_cnt, 0)
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
                process_frame_set(frame_set, status, block_cnt, 0)
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
                bef_frame_time = frame_time
                bef_frame_offset = frame_offset
                frame_meta = file.read(32)
                if int.from_bytes(frame_meta[:32]) == 0x00:
                    #print("Block : " + str(block_cnt) + ", ", end='')
                    process_frame_set(frame_set, status, block_cnt, 0)
                    return
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            #print("Block : " + str(block_cnt) + ", ", end='')
            process_frame_set(frame_set, status, block_cnt, 0)
            status = 0
            file.seek(-32, 1)
        UBS = Unallocated_Block_Scan()
        #print(frame_set[-1])
        UBS.slack(block_cnt, start_frame_time, frame_set[-1]["frame_time"], frame_set[-1]["frame_offset"], file)
            #if block_end == 0:
                #print('')



