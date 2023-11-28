import pandas as pd
from sqlite_db import insert_data_log
import re

class LogParse:
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
            else:
                EVENT = None

            # 날짜/시간 추출
            if len(values) >= 5:
                DATETIME = values[4]
                DATETIME = self.convert_datetime(DATETIME)
            else:
                DATETIME_start = line.find("|", no_end + 1)
                DATETIME_end = line.find("|", DATETIME_start + 1)
                DATETIME = line[DATETIME_start + 1:DATETIME_end].strip() if DATETIME_start != -1 and DATETIME_end != -1 else None
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

                # Remove the dynamic pattern from the merged_event
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
        # Remove the dynamic pattern from the event string
        pattern_to_remove = r'-.*?-'
        cleaned_event = re.sub(pattern_to_remove, '-', event_str)

        return cleaned_event

    def convert_datetime(self, datetime_str):
        # 날짜 및 시간 형식 변환
        if datetime_str and ('오후' in datetime_str or '오전' in datetime_str):
            datetime_str = datetime_str.replace('오후', '').replace('오전', '')

            # 시간 부분 추출
            time_parts = datetime_str.split()
            time_part = time_parts[1] if len(time_parts) > 1 else ''

            # 24시간 형식으로 시간 변환
            if '오후' in datetime_str and '12' not in time_part:
                hours, minutes, seconds = map(int, time_part.split(':'))
                hours += 12
                datetime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            elif '오전' in datetime_str and '12' in time_part:
                hours, minutes, seconds = map(int, time_part.split(':'))
                hours -= 12
                datetime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            datetime_str = datetime_str.replace(' ', '')
            datetime_str = datetime_str[:10] + ' ' + datetime_str[10:]

        return datetime_str