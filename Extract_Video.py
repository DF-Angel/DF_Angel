import sqlite3
import os
import logging
import datetime
import ffmpeg

# 로깅 설정
logging.basicConfig(filename='debug.log', level=logging.DEBUG, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

def hex_to_datetime_le(hex_value):
    le_hex = ''.join(reversed([hex_value[i:i+2] for i in range(0, len(hex_value), 2)]))
    int_value = int(le_hex, 16)
    
    second = int_value & 0x3F
    int_value >>= 6
    minute = int_value & 0x3F
    int_value >>= 6
    hour = int_value & 0x1F
    int_value >>= 5
    day = int_value & 0x1F
    int_value >>= 5
    month = int_value & 0xF
    int_value >>= 4
    year_offset = int_value & 0x3F

    year = 1970 + year_offset

    # 월(month) 값의 유효성 검증
    if 1 <= month <= 12:
        return datetime.datetime(year, month, day, hour, minute, second)
    else:
        # 유효하지 않은 월(month) 값에 대한 예외 처리
        logging.error(f"Invalid month value extracted: {month}")
        return None  # 또는 적절한 기본 날짜 반환
    
def convert_h264_to_mp4(input_file, output_file):
    try:
        (
            ffmpeg
            .input(input_file, format='h264')
            .output(output_file, vcodec='copy')
            .run(overwrite_output=True)
        )
        logging.info(f"변환 완료: {output_file}")
    except ffmpeg.Error as e:
        logging.error(f"변환 중 오류 발생: {e}")

def little_endian_to_int(bytes_data):
    try:
        return int.from_bytes(bytes_data, byteorder='little')
    except Exception as e:
        logging.error(f"Error converting little endian to int: {e}")
        raise

def extract_frames(db_filepath, image_filepath, selected_rows, output_folder):
    # 'Extracted' 폴더를 생성합니다.
    extracted_folder = os.path.join(output_folder, 'Extracted')
    if not os.path.isdir(extracted_folder):
        logging.info(f"Creating extracted folder at {extracted_folder}")
        os.makedirs(extracted_folder, exist_ok=True)

    connection = sqlite3.connect(db_filepath)
    logging.info(f"Database connected: {db_filepath}")
    cursor = connection.cursor()

    for index in selected_rows:
        logging.info(f"Processing index: {index}")
        cursor.execute("SELECT START_OFFSET FROM ROOT_SCAN WHERE idx=?", (index,))
        start_offset_result = cursor.fetchone()

        if not start_offset_result:
            logging.warning(f"Index {index} has no START_OFFSET.")
            continue

        start_offset = start_offset_result[0]
        metadata_offset = start_offset + 0x100000

        frame_data_file = os.path.join(extracted_folder, f'block_{index}.bin')  # 'Extracted' 폴더에 프레임 데이터 파일 저장
        index_file = os.path.join(extracted_folder, f'index_{index}.txt')  # 'Extracted' 폴더에 인덱스 파일 저장

        with open(frame_data_file, 'wb') as fd_file, open(index_file, 'w') as idx_file, open(image_filepath, 'rb') as file:
            while True:
                file.seek(metadata_offset, 0)
                metadata = file.read(32)

                if metadata == b'\x00' * 32:
                    logging.info(f"All metadata bytes are zero at index {index}. Ending read.")
                    break

                frame_start_point = little_endian_to_int(metadata[28:32])
                frame_data_size = little_endian_to_int(metadata[16:20]) - 0x23

                actual_frame_start = start_offset + 0x500000 + frame_start_point + 0xC4

                file.seek(actual_frame_start, 0)
                frame_data = file.read(frame_data_size)

                current_position = fd_file.tell()
                fd_file.write(frame_data)
                idx_file.write(f"{current_position},{len(frame_data)}\n")

                metadata_offset += 32

        # 모든 프레임 데이터가 추출된 후 MP4로 변환
        output_mp4_file = os.path.join(output_folder, 'Extracted', f'frames_{index}.mp4')
        convert_h264_to_mp4(frame_data_file, output_mp4_file)

    connection.close()
    logging.info("Database connection closed.")

def main(db_filepath, image_filepath, selected_indexes, output_folder='output'):
    logging.info("Extraction started.")
    extract_frames(db_filepath, image_filepath, selected_indexes, output_folder)
    logging.info("Extraction finished.")

if __name__ == "__main__":
    db_filepath = './IDIS_FS_sqlite.db'
    image_filepath = './example_image.img'
    selected_rows = [1, 2]
    output_folder = 'output'
    main(db_filepath, image_filepath, selected_rows, output_folder)