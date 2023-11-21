from CommonFunction import *
from datetime import timedelta
class Unallocated_Block_Scan:
    def all_del(self, block_start_time, block_end_time, block_cnt, file):
        frame_set = []  # List to store frames in a set
        block_index = file.read(64)
        frame_cnt = 1
        start_frame_cnt = frame_cnt
        #할당 : 0 / 부분 삭제 : 1 / 모든 데이터 삭제 : 2 / 포맷 : 3 / Unknown(Slack) : 4
        status = 0
        block_end = 0
        allocated_block_end = 1
        frame_meta = file.read(32)
        frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
        frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
        frame_channel = frame_meta[0x18]
        frame_type = frame_meta[0x1A]
        frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')

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
            print("Block : " + str(block_cnt - 1) + ", ", end='')
            self.process_frame_set(frame_set, status)
            status = 0
            frame_set = []
            #file.seek(-32, 1)
            status = 0
        file.seek(-32, 1)

        #할당 및 중간 부분 삭제
        while allocated_block_end:
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
                    frame_meta = file.read(32)
                    if int.from_bytes(frame_meta[:32]) == 0x00:
                    #    self.process_frame_set(frame_set)
                    #    block_end = 1
                        break
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                print("Block : " + str(block_cnt - 1) + ", ", end='')
                self.process_frame_set(frame_set, status)
                status = 0
                while int.from_bytes(frame_meta[:32]) != 0x00 and block_start_time <= frame_time <= block_end_time:
                    frame_meta = file.read(32)
                    if int.from_bytes(frame_meta[:32]) == 0x00:
                        #self.process_frame_set(frame_set)
                        block_end = 1
                        break
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                if int.from_bytes(frame_meta[:32]) == 0x00:
                    block_end = 1
                    break
                else:
                    frame_set = [
                        {
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    ]
                    break

            if frame_size == 0:
                print("Block : " + str(block_cnt - 1) + ", ", end='')
                self.process_frame_set(frame_set, status)
                status = 2
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
                    frame_meta = file.read(32)
                    if int.from_bytes(frame_meta) == 0x00:
                        block_end = 1
                        break
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                    if frame_set[-1]["frame_time"] > frame_time:
                        allocated_block_end = 0
                        break
                print("Block : " + str(block_cnt - 1) + ", ", end='')
                self.process_frame_set(frame_set, status)
                status = 0
                frame_set = [
                    {
                        "frame_time": frame_time,
                        "frame_size": frame_size,
                        "frame_channel": frame_channel,
                        "frame_type": frame_type,
                        "frame_offset": frame_offset,
                    }
                ]
                status = 0
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
        # 부분 삭제(끝)
        if frame_set[0]["frame_time"] > block_end_time and block_end == 0:
            status = 3
            frame_meta = file.read(32)
            if int.from_bytes(frame_meta[:32]) == 0x00:
                print("Block : " + str(block_cnt - 1) + ", ", end='')
                self.process_frame_set(frame_set, status)
                status = 0
                return
            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            while frame_time > block_end_time:
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
                    print("Block : " + str(block_cnt - 1) + ", ", end='')
                    self.process_frame_set(frame_set, status)
                    status = 0
                    block_end = 1
                    break
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            if block_end != 1:
                print("Block : " + str(block_cnt - 1) + ", ", end='')
                self.process_frame_set(frame_set, status)
                status = 0

            #if block_end == 0:
                #print('')



    def process_frame_set(self, frame_set, status):
        # Process and organize the complete set of frames
        start_time = frame_set[0]["frame_time"]
        last_time = frame_set[-1]["frame_time"]
        channel = frame_set[0]["frame_channel"]
        start_offset = hex(frame_set[0]["frame_offset"])
        last_offset = hex(frame_set[-1]["frame_offset"])
        del_type = ''
        if status == 0:
            del_type = "모든 데이터 삭제"
        elif status == 1:
            del_type = "부분 삭제(시작)"
        elif status == 2:
            del_type = "부분 삭제(중간)"
        elif status == 3:
            del_type = "부분 삭제(끝)"
        # Perform further actions as needed with the organized frame set
        print(f"Start Time: {start_time}, Last Time: {last_time}, Channel: {channel}, Start Offset: {start_offset}, Last Offset: {last_offset}, Del Type: {del_type}")
