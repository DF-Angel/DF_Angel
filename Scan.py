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
            block_cnt = 1
            base = 0x80100000
            while True:
                file.seek(base + 0x500080 + (block_cnt - 1) * 64, 0)
                frame_set = []  # List to store frames in a set
                block_index = file.read(64)
                file.seek(base + 0x10000000 * block_cnt + 0x100000, 0)
                block_cnt += 1
                if int.from_bytes(block_index[:64], byteorder='little') == 0x00:
                    break
                if block_index[0] == 0x05 or block_index[0] == 0x06:
                    block_start_time = convert_to_datetime(
                        int.from_bytes(block_index[0x06:0x0A], byteorder='little')
                    )
                    block_end_time = convert_to_datetime(
                        int.from_bytes(block_index[0x12:0x16], byteorder='little')
                    )
                    block_channel = block_index[0x22]
                    ABS = Allocated_Block_Scan()
                    ABS.analyzer(block_start_time, block_end_time, block_cnt, file)
                elif block_index[0] == 0x00:#비할당
                    UBS = Unallocated_Block_Scan()
                    if int.from_bytes(block_index[0x06:0x0A]) == 0x7D9F4103:#포맷
                        continue
                    else:#모든 데이터 삭제 or 부분 삭제(블록 전체)
                        block_start_time = convert_to_datetime(
                            int.from_bytes(block_index[0x06:0x0A], byteorder='little')
                        )
                        block_end_time = convert_to_datetime(
                            int.from_bytes(block_index[0x12:0x16], byteorder='little')
                        )
                        UBS.all_del(block_start_time, block_end_time, block_cnt, file)