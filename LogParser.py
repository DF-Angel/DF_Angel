import pandas as pd
from sqlite_db import insert_data_log
import re


class LogParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        # 빈 리스트 생성
        parsed_data = []

        # 파일에서 데이터 읽기 ('utf-8' 또는 'euc-kr'로 시도)
        with open(self.file_path, 'rb') as file:
            try:
                lines = [line.decode('utf-8') for line in file.readlines()]
            except UnicodeDecodeError:
                file.seek(0)
                lines = [line.decode('euc-kr') for line in file.readlines()]

        # 데이터 파싱
        for line in lines[3:]:
            # 숫자 여부 확인하여 No. 추출
            no_start = line.find("|")
            no_end = line.find("|", no_start + 1)
            no_str = line[no_start + 1:no_end].strip()
            no = int(no_str) if no_str.isdigit() else None

            # 종류와 날짜/시간 추출
            values = [value.strip() for value in line.strip().split('|')]

            # 종류 추출
            if len(values) >= 3:
                EVENT = values[2]
                EVENT = self.convert_EVENT_TIME(EVENT)
            else:
                EVENT = None

            # 날짜/시간 추출
            if len(values) >= 5:
                DATETIME = values[4]
                DATETIME = self.convert_datetime(DATETIME)
            else:
                DATETIME_start = line.find("|", no_end + 1)
                DATETIME_end = line.find("|", DATETIME_start + 1)
                DATETIME = line[
                           DATETIME_start + 1:DATETIME_end].strip() if DATETIME_start != -1 and DATETIME_end != -1 else None
                DATETIME = self.convert_datetime(DATETIME)

            # 추출한 값들을 딕셔너리로 저장
            parsed_data.append({'NUMBER': no, 'EVENT': EVENT, 'DATETIME': DATETIME})

        merged_data = []
        for i in range(len(parsed_data)):
            current_row = parsed_data[i]
            if current_row['EVENT'] and '설정 변경' in current_row['EVENT']:
                merged_event = current_row['EVENT']

                for j in range(i + 1, len(parsed_data)):
                    next_row = parsed_data[j]
                    if next_row['NUMBER'] is None and next_row['EVENT']:
                        merged_event += next_row['EVENT']
                        next_row['EVENT'] = None
                    else:
                        break

                merged_event = self.clean_event(merged_event)

                current_row['EVENT'] = merged_event
                merged_data.append(current_row)
            elif current_row['NUMBER'] is not None:
                merged_data.append(current_row)

        data = pd.DataFrame(merged_data)

        for row in merged_data:
            if row['DATETIME'] is not None:
                insert_data_log(row['EVENT'], row['DATETIME'])

        print(data)

    def clean_event(self, event_str):
        pattern_to_remove = r'-.*?-'
        cleaned_event = re.sub(pattern_to_remove, '-', event_str)

        return cleaned_event

    def convert_datetime(self, datetime_str):
        # 날짜 및 시간 형식 변환
        if datetime_str and ('오후' in datetime_str or '오전' in datetime_str):

            if '오후' in datetime_str:
                hours_match = re.search(r'오후 (\d+):', datetime_str)
                hours_str = hours_match.group(1) if hours_match else None
                hours = int(hours_str) if hours_str else 0
                hours += 12  # 오후인 경우 12를 더해줌

                if hours == 24:
                    hours = 12

                datetime_str = re.sub(r'오후 \d+:', f'{hours:02d}:', datetime_str)
                datetime_str = datetime_str.replace('  ', ' ')

            elif '오전' in datetime_str:
                hours_match = re.search(r'오전 (\d+):', datetime_str)
                hours_str = hours_match.group(1) if hours_match else None
                hours = int(hours_str) if hours_str else 0
                hours += 0  # 오후인 경우 12를 더해줌

                if hours == 12:
                    hours = 0

                datetime_str = re.sub(r'오전 \d+:', f'{hours:02d}:', datetime_str)
                datetime_str = datetime_str.replace('  ', ' ')

        return datetime_str

    def convert_EVENT_TIME(self, EVENT):

        if EVENT and ('오후' in EVENT or '오전' in EVENT):

            if '오후' in EVENT:
                hours_match = re.search(r'오후 (\d+):', EVENT)
                hours_str = hours_match.group(1) if hours_match else None
                hours = int(hours_str) if hours_str else 0
                hours += 12  # 오후인 경우 12를 더해줌

                if hours == 24:
                    hours = 12

                EVENT = re.sub(r'오후 \d+:', f'{hours:02d}:', EVENT)
                EVENT = EVENT.replace('  ', ' ')

            elif '오전' in EVENT:
                hours_match = re.search(r'오전 (\d+):', EVENT)
                hours_str = hours_match.group(1) if hours_match else None
                hours = int(hours_str) if hours_str else 0
                hours += 0

                if hours == 12:
                    hours = 0

                EVENT = re.sub(r'오전 \d+:', f'{hours:02d}:', EVENT)
                EVENT = EVENT.replace('  ', ' ')

        return EVENT