from CommonFunction import *
from sqlite_db import *

class Allocated:
    def __init__(self, imagefile):
        self.f = imagefile
    def check_G2FDb(self):
        try:
            self.f = open(self.f, 'rb')
            return 1  # 파일이 정상적으로 열렸을 때 1을 반환
        except FileNotFoundError:
            return 0  # 파일을 찾을 수 없을 때 0을 반환
    def analyzer(self):
        with self.f as file:
            base = 0x80100000
            file.seek(base + 0x500000, 0)
            magic_signature = file.read(64)
            if magic_signature[:0x1B] != b"This is G2FDb Storage Magic":
                return 0 #비정상적인 G2FDb 이미지 파일
            file.read(64)

            block_cnt = 1
            while True:
                block_index = file.read(64)
                if int.from_bytes(block_index[:64]) == 0x00:
                    break
                if block_index[0] != 0x05 and block_index[0] != 0x06:
                    continue
                start_time = convert_to_datetime(int.from_bytes(block_index[0x06:0x0A], byteorder='little'))
                end_time = convert_to_datetime(int.from_bytes(block_index[0x12:0x16], byteorder='little'))
                total_time = end_time - start_time
                ch = block_index[0x22]
                insert_data('Block ' + str(block_cnt), ch, start_time, end_time, total_time, 0x10000000 * block_cnt, 0x10000000 * (block_cnt + 1) - 1, 0x10000000)
                block_cnt += 1