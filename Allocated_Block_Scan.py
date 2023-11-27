from CommonFunction import *
from datetime import timedelta
from Unallocated_Block_Scan import Unallocated_Block_Scan
class Allocated_Block_Scan:
    def analyzer(self, block_start_time, block_end_time, block_cnt, file):
        #print("=============================================================")
        frame_set = []  # List to store frames in a set
        #block_index = file.read(64)
        frame_cnt = 1
        start_frame_cnt = frame_cnt
        #할당 : 0 / 부분 삭제 : 1 / 모든 데이터 삭제 : 2 / 포맷 : 3 / Unknown(Slack) : 4
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
            self.process_frame_set(frame_set, status)
            status = 0
            frame_set = []
            #file.seek(-32, 1)
            #status = 0
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
                        self.process_frame_set(frame_set, status)
                    #    block_end = 1
                        return
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                print("Block : " + str(block_cnt) + ", ", end='')
                self.process_frame_set(frame_set, status)
                #return
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
                    bef_frame_time = frame_time
                    bef_frame_offset = frame_offset
                    frame_meta = file.read(32)
                    if int.from_bytes(frame_meta) == 0x00:
                        print("Block : " + str(block_cnt) + ", ", end='')
                        self.process_frame_set(frame_set, status)
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
                self.process_frame_set(frame_set, status)
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
            status = 3
            frame_meta = file.read(32)
            if int.from_bytes(frame_meta[:32]) == 0x00:
                print("Block : " + str(block_cnt) + ", ", end='')
                self.process_frame_set(frame_set, status)
                status = 0
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
                    self.process_frame_set(frame_set, status)
                    status = 0
                    block_end = 1
                    return
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            print("Block : " + str(block_cnt) + ", ", end='')
            self.process_frame_set(frame_set, status)
            file.seek(-32, 1)
        UBS = Unallocated_Block_Scan()
        print(frame_set[-1])
        UBS.slack(block_cnt, start_frame_time, frame_set[-1]["frame_time"], frame_set[-1]["frame_offset"], file)
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
            del_type = "할당"
        elif status == 1:
            del_type = "부분 삭제(시작)"
        elif status == 2:
            del_type = "부분 삭제(중간)"
        elif status == 3:
            del_type = "부분 삭제(끝)"
        # Perform further actions as needed with the organized frame set
        #print(f"Start Time: {start_time}, Last Time: {last_time}, Channel: {channel}, Start Offset: {start_offset}, Last Offset: {last_offset}, Del Type: {del_type}")
        print(f"Start Time: {start_time}, Last Time: {last_time}, Channel: {channel}, Del Type: {del_type}")