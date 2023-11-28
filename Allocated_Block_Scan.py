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
            print("Block : " + str(block_cnt) + ", ", end='')
            self.process_frame_set(frame_set, status, block_cnt)
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
                        print("Block : " + str(block_cnt) + ", ", end='')
                        self.process_frame_set(frame_set, status, block_cnt)
                    #    block_end = 1
                        return
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                print("Block : " + str(block_cnt) + ", ", end='')
                self.process_frame_set(frame_set, status, block_cnt)

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
                #while int.from_bytes(frame_meta[:32]) != 0x00 and block_start_time <= frame_time <= block_end_time:
                #    frame_meta = file.read(32)
                #    if int.from_bytes(frame_meta[:32]) == 0x00:
                #        #self.process_frame_set(frame_set)
                #        block_end = 1
                #        break
                    #print(frame_meta)
                #    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                #    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                #    frame_channel = frame_meta[0x18]
                #    frame_type = frame_meta[0x1A]
                #    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                #if int.from_bytes(frame_meta[:32]) == 0x00:
                #    block_end = 1
                #    break
                #else:
                #    frame_set = [
                #        {
                #            "frame_time": frame_time,
                #            "frame_size": frame_size,
                #            "frame_channel": frame_channel,
                #            "frame_type": frame_type,
                #            "frame_offset": frame_offset,
                #        }
                #    ]
                #    break

            if frame_size == 0:
                print("Block : " + str(block_cnt) + ", ", end='')
                self.process_frame_set(frame_set, status, block_cnt)
                status = 1
                frame_set = []
                while frame_size == 0:
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
                        print("Block : " + str(block_cnt) + ", ", end='')
                        self.process_frame_set(frame_set, status, block_cnt)
                        return
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                    if frame_set[-1]["frame_time"] > frame_time:
                        allocated_block_end = 0
                        break
                print("Block : " + str(block_cnt) + ", ", end='')
                self.process_frame_set(frame_set, status, block_cnt)
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
                print("Block : " + str(block_cnt) + ", ", end='')
                self.process_frame_set(frame_set, status, block_cnt)
                return
            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            while frame_set[-1]["frame_time"] <= frame_time:
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
                    print("Block : " + str(block_cnt) + ", ", end='')
                    self.process_frame_set(frame_set, status, block_cnt)
                    return
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            print("Block : " + str(block_cnt) + ", ", end='')
            self.process_frame_set(frame_set, status, block_cnt)
            status = 0
            file.seek(-32, 1)
        UBS = Unallocated_Block_Scan()
        #print(frame_set[-1])
        UBS.slack(block_cnt, start_frame_time, frame_set[-1]["frame_time"], frame_set[-1]["frame_offset"], file)
            #if block_end == 0:
                #print('')



    def process_frame_set(self, frame_set, status, block_cnt):
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
            del_type = "부분 삭제(시작)"
        # Perform further actions as needed with the organized frame set
        #print(f"Start Time: {start_time}, Last Time: {last_time}, Channel: {channel}, Start Offset: {start_offset}, Last Offset: {last_offset}, Del Type: {del_type}")
        print(f"Start Time: {start_time}, Last Time: {last_time}, Channel: {channel}, Del Type: {del_type}")
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
                                 p_frame_cnt, 0)