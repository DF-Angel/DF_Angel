from CommonFunction import *
from sqlite_db import *
from datetime import timedelta

class Unallocated_Block_Scan:
    def all_del(self, block_start_time, block_end_time, block_cnt, file, version):
        #self.all_del_condition = ADC
        frame_set = []  # List to store frames in a set
        status = 2
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
                    process_frame_set(frame_set, status, block_cnt, 1, version)
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
            process_frame_set(frame_set, status, block_cnt, 1, version)
            status = 2
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
                        process_frame_set(frame_set, status, block_cnt, 1, version)
                    #    block_end = 1
                        return
                    frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                    frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                    frame_channel = frame_meta[0x18]
                    frame_type = frame_meta[0x1A]
                    frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                #print("Block : " + str(block_cnt) + ", ", end='')
                process_frame_set(frame_set, status, block_cnt, 1, version)

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
                process_frame_set(frame_set, status, block_cnt, 1, version)
                status = 1
                frame_set = []
                while frame_size == 0:
                    # Modify 203-12-02
                    if len(frame_set) != 0 and frame_time >= frame_set[-1]["frame_time"] + timedelta(seconds=2):
                        process_frame_set(frame_set, status, block_cnt, 1, version)
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
                        process_frame_set(frame_set, status, block_cnt, 1, version)
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
                process_frame_set(frame_set, status, block_cnt, 1, version)
                status = 2
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
                status = 2
                continue
            # Modify 203-12-02
            if len(frame_set) != 0 and frame_time >= frame_set[-1]["frame_time"] + timedelta(seconds=2):
                process_frame_set(frame_set, status, block_cnt, 1, version)
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
                process_frame_set(frame_set, status, block_cnt, 1, version)
                status = 2
                return
            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            while frame_set[-1]["frame_time"] <= frame_time:
                # Modify 203-12-02
                if len(frame_set) != 0 and frame_time >= frame_set[-1]["frame_time"] + timedelta(seconds=2):
                    process_frame_set(frame_set, status, block_cnt, 1, version)
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
                    process_frame_set(frame_set, status, block_cnt, 1, version)
                    status = 2
                    block_end = 1
                    return
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            #print("Block : " + str(block_cnt) + ", ", end='')
            process_frame_set(frame_set, status, block_cnt, 1, version)
            file.seek(-32, 1)
        base = 0x80100000 + 0x10000000 * block_cnt + 0x500000
        self.new_slack(base + frame_set[-1]["frame_offset"] + frame_set[-1]["frame_size"], block_cnt, file, version)
        #self.slack(block_cnt, start_frame_time, frame_set[-1]["frame_time"], frame_set[-1]["frame_offset"], file)

            #if block_end == 0:
                #print('')

    def format(self, block_cnt, file, version):
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
                    process_frame_set(frame_set, status, block_cnt, 1, version)
                    break
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')

                if frame_size == 0:
                    status = 1
                    process_frame_set(frame_set, status, block_cnt, 1, version)

                    while frame_size == 0:
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
                        if bef_frame_time > frame_time:
                            process_frame_set(frame_set, status, block_cnt, 1, version)
                            file.seek(-32)
                            base = 0x80100000 + 0x10000000 * block_cnt + 0x500000
                            self.new_slack(base + frame_set[-1]["frame_offset"] + frame_set[-1]["frame_size"],
                                           block_cnt, file, version)
                            #self.slack(block_cnt, start_frame_time, bef_frame_time, bef_frame_offset, file)

                        frame_meta = file.read(32)
                        if int.from_bytes(frame_meta) == 0x00:
                            process_frame_set(frame_set, status, block_cnt, 1, version)
                            break
                        frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                        frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                        frame_channel = frame_meta[0x18]
                        frame_type = frame_meta[0x1A]
                        frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')

                    process_frame_set(frame_set, status, block_cnt, 1, version)
                    status = 3

                if bef_frame_time > frame_time:
                        process_frame_set(frame_set, status, block_cnt, 1, version)
                        file.seek(-32)
                        base = 0x80100000 + 0x10000000 * block_cnt + 0x500000
                        self.new_slack(base + frame_set[-1]["frame_offset"] + frame_set[-1]["frame_size"], block_cnt,
                                       file, version)
                        #self.slack(block_cnt, start_frame_time, bef_frame_time, bef_frame_offset, file)
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
                process_frame_set(frame_set, status, block_cnt, 1, version)
                return
            frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
            frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
            frame_channel = frame_meta[0x18]
            frame_type = frame_meta[0x1A]
            frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
            if bef_frame_time > frame_time:
                #print("Block : " + str(block_cnt) + ", ", end='')
                process_frame_set(frame_set, status, block_cnt, 1, version)
                file.seek(-32, 1)
                base = 0x80100000 + 0x10000000 * block_cnt + 0x500000
                self.new_slack(base + frame_set[-1]["frame_offset"] + frame_set[-1]["frame_size"], block_cnt, file,
                               version)
                #self.slack(block_cnt, start_frame_time, bef_frame_time, bef_frame_offset, file)
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

    def new_slack(self, slack_start_offset, block_cnt, file, version):

        i_frame_sig = b'\x00\x00\x00\x01\x65'
        p_frame_sig = b'\x00\x00\x00\x01\x21'

        known_frame_set = []
        unknown_frame_set = []

        status = 4
        interval_i = 0
        interval_p = 0
        if version == 0:
            interval_i = 0xDB
            interval_p = 0xC4
        elif version == 1:
            interval_i = 0xC6
            interval_p = 0xAC

        slack_end_offset = (block_cnt + 1) * 0x10000000 + 0x80100000

        file.seek(slack_start_offset, 0)
        slack_data = file.read(slack_end_offset - slack_start_offset)

        frame_sig_offsets = []
        slack_data_len = len(slack_data)

        index = 0
        i_frame_offset = 0
        p_frame_offset = 0
        bef_frame_offset = 0

        i_frame_offset = slack_data.find(i_frame_sig, index)
        p_frame_offset = slack_data.find(p_frame_sig, index)

        if i_frame_offset == -1 and p_frame_offset == -1:
            return

        while i_frame_offset != -1 or p_frame_offset != -1:
            sel_type = 0
            if i_frame_offset != -1 and p_frame_offset != -1:
                if i_frame_offset > p_frame_offset:
                    sel_type = 1
                else:
                    sel_type = 0
            else:
                if i_frame_offset == -1:
                    sel_type = 1
                else:
                    sel_type = 0
            #print('unknown : ' + str(len(unknown_frame_set)) + ' / known : ' + str(len(known_frame_set)) + ' / block : ' + str(block_cnt))
            if sel_type == 1:#P-Frame Check
                #if len(unknown_frame_set) != 0 and unknown_frame_set[-1][1] == 0:
                #    unknown_frame_set[-1][1] = p_frame_offset - bef_frame_offset  # 직전에 처리한 프레임의 오프셋
                if p_frame_offset <= 0x20 + interval_p:
                    #unknown_frame_set.append([slack_start_offset + p_frame_offset, 0])  # start offset, size
                    index += 1
                    #bef_frame_offset = p_frame_offset
                    p_frame_offset = slack_data.find(p_frame_sig, index)
                    continue
                frame_meta = slack_data[p_frame_offset - interval_p: p_frame_offset - interval_p + 0x20]
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                if (
                        frame_time != 0 and
                        frame_offset == slack_start_offset + p_frame_offset - 0x80600000 - interval_p - (
                        block_cnt * 0x10000000) and
                        # frame_time < last_frame_time and
                        frame_type == 1 and
                        0 <= frame_channel < 255 and
                        0 <= frame_size <= (slack_end_offset - slack_start_offset - p_frame_offset)
                ):
                    known_frame_set.append(
                        {
                            "real_frame_offset": slack_start_offset + p_frame_offset,
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    )
                    index += frame_size - 0x23
                else:
                    #unknown_frame_set.append([slack_start_offset + p_frame_offset, 0,
                    #                         1])  # start offset, size, frame type
                    index += 1
                bef_frame_offset = p_frame_offset
                p_frame_offset = slack_data.find(p_frame_sig, index)

            elif sel_type == 0:#I-Frame Check
                #if len(unknown_frame_set) != 0 and unknown_frame_set[-1][1] == 0:
                #    unknown_frame_set[-1][1] = i_frame_offset - bef_frame_offset  # 직전에 처리한 프레임의 오프셋
                if i_frame_offset <= 0x20 + interval_i:
                    unknown_frame_set.append(slack_start_offset + i_frame_offset, 0)  # start offset, size
                    index += 1
                    bef_frame_offset = i_frame_offset
                    i_frame_offset = slack_data.find(i_frame_sig, index)
                    continue
                frame_meta = slack_data[i_frame_offset - interval_i: i_frame_offset - interval_i + 0x20]
                frame_time = convert_to_datetime(int.from_bytes(frame_meta[0x04:0x08], byteorder='little'))
                frame_size = int.from_bytes(frame_meta[0x10:0x14], byteorder='little')
                frame_channel = frame_meta[0x18]
                frame_type = frame_meta[0x1A]
                frame_offset = int.from_bytes(frame_meta[0x1C:0x20], byteorder='little')
                if (
                        frame_time != 0 and
                        frame_offset == slack_start_offset + i_frame_offset - 0x80600000 - interval_i - (
                        block_cnt * 0x10000000) and
                        # frame_time < last_frame_time and
                        frame_type == 1 and
                        0 <= frame_channel < 255 and
                        0 <= frame_size <= (slack_end_offset - slack_start_offset - i_frame_offset)
                ):
                    known_frame_set.append(
                        {
                            "real_frame_offset": slack_start_offset + i_frame_offset,
                            "frame_time": frame_time,
                            "frame_size": frame_size,
                            "frame_channel": frame_channel,
                            "frame_type": frame_type,
                            "frame_offset": frame_offset,
                        }
                    )
                    index += frame_size - 0x23
                else:
                    #unknown_frame_set.append([slack_start_offset + i_frame_offset, 0,
                    #                         0])  # start offset, size, frame type
                    index += 1
                bef_frame_offset = i_frame_offset
                i_frame_offset = slack_data.find(i_frame_sig, index)
        #print('unknown : ' + str(len(unknown_frame_set)) + ' / known : ' + str(
        #    len(known_frame_set)) + ' / block : ' + str(block_cnt))

        #if len(unknown_frame_set) != 0 and unknown_frame_set[-1][1] == 0:
        #    unknown_frame_set[-1][1] = slack_end_offset - unknown_frame_set[-1][0]
        #print(len(known_frame_set))
        # frame_channel을 기준으로 그룹화
        channel_groups = {}
        for frame in known_frame_set:
            channel = frame["frame_channel"]
            if channel not in channel_groups:
                channel_groups[channel] = []
            channel_groups[channel].append(frame)

        # 각 그룹 내에서 frame_time을 기준으로 정렬
        for channel, frames in channel_groups.items():
            channel_groups[channel] = sorted(frames, key=lambda x: x["frame_time"])

        for channel, frames in channel_groups.items():
            bef_frame_time = channel_groups[channel][0]["frame_time"]
            idx = 0
            for frame_cnt in range(len(channel_groups[channel])):
                if channel_groups[channel][frame_cnt]["frame_time"] >= bef_frame_time + timedelta(seconds=2):
                    process_frame_set(channel_groups[channel][idx:frame_cnt], status, block_cnt, 1, version)
                    idx = frame_cnt
                bef_frame_time = channel_groups[channel][frame_cnt]["frame_time"]
            process_frame_set(channel_groups[channel][idx:len(channel_groups[channel])], status, block_cnt, 1, version)
        return
        for i in range(len(unknown_frame_set)):
            i_frame_cnt = 0
            p_frame_cnt = 0
            if unknown_frame_set[i][2] == 0:
                i_frame_cnt = 1
            else:
                p_frame_cnt = 1
            insert_data_precise_scan('Unknown Frame ' + str(i),
                                     block_cnt,
                                     -1, 'Unknwon',
                                     'Unknwon', '00:00:01',unknown_frame_set[i][0],
                                     unknown_frame_set[i][0] + unknown_frame_set[i][1], unknown_frame_set[i][1],
                                     status, i_frame_cnt,
                                     p_frame_cnt, 1)
