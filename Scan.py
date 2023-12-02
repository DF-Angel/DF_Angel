from CommonFunction import *
from Allocated_Block_Scan import Allocated_Block_Scan
from Unallocated_Block_Scan import Unallocated_Block_Scan
from datetime import timedelta
class Scan:
    def __init__(self, imagefile):
        self.f = imagefile
        self.f = open(self.f, 'rb')

    def analyzer(self):
        with self.f as file:
            ABS = Allocated_Block_Scan()
            block_cnt = 1
            base = 0x80100000
            block_meta = []
            file.seek(base + 0x500080, 0)
            while True:
                block_index = file.read(64)
               # print(block_index[0])
                #print(int.from_bytes(block_index[0x06:0x0A], byteorder='little'))
                if int.from_bytes(block_index[:64], byteorder='little') == 0x00:
                    break
                if block_index[0] == 0x82 or block_index[0] == 0x20:
                    block_meta.append([])
                    continue
                if int.from_bytes(block_index[0x06:0x0A], byteorder='little') == 0x03419F7D:
                    block_start_time = int.from_bytes(block_index[0x06:0x0A], byteorder='little')
                    block_end_time = int.from_bytes(block_index[0x12:0x16], byteorder='little')
                else:
                    block_start_time = convert_to_datetime(
                        int.from_bytes(block_index[0x06:0x0A], byteorder='little')
                    )
                    block_end_time = convert_to_datetime(
                        int.from_bytes(block_index[0x12:0x16], byteorder='little')
                    )
                    if block_start_time == 0 or block_end_time == 0:
                        block_meta.append([])
                        continue
                block_channel = block_index[0x22]
                block_meta.append([block_index[0], block_start_time, block_end_time, block_channel])
            #print(block_meta[28])
            for i in range(len(block_meta)):
                print(block_cnt)
                if block_meta[i] == []:
                    block_cnt += 1
                    continue
                file.seek(base + 0x10000000 * block_cnt + 0x100000, 0)
                #print(block_meta[i][0])
                if block_meta[i][0] == 0x05 or block_meta[i][0] == 0x06:
                    ABS.analyzer(block_meta[i][1], block_meta[i][2], block_cnt, file)
                elif block_index[0] == 0x00:#비할당
                    all_del_condition = True
                    UBS = Unallocated_Block_Scan()
                    if block_meta[i][1] == 0x03419F7D:#포맷
                        UBS.format(block_cnt, file)
                    else:#모든 데이터 삭제 or 부분 삭제(블록 전체)
                        for j in range(len(block_meta)):
                            if block_meta[j] == []:
                                continue
                            if i == j or block_meta[j][1] == 0x03419F7D:
                                continue
                            if block_meta[i][1] >= block_meta[j][1] and block_meta[j][0] != 0x00:
                                all_del_condition = False
                                break
                        UBS.all_del(block_meta[i][1], block_meta[i][2], block_cnt, file, all_del_condition)
                block_cnt += 1