import sqlite3
import os
import logging
import ffmpeg

# 로깅 설정
logging.basicConfig(filename='precise_extract_video.log', level=logging.DEBUG, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# SQLite 데이터베이스로부터 데이터를 추출하는 함수
def extract_data_from_db(db_filepath, image_filepath, output_folder, selected_indexes):
    
    extracted_folder = os.path.join(output_folder, 'Extracted')
    if not os.path.isdir(extracted_folder):
        logging.info(f"Creating extracted folder at {extracted_folder}")
        os.makedirs(extracted_folder, exist_ok=True)
    
    connection = sqlite3.connect(db_filepath)
    logging.info(f"Database connected: {db_filepath}")
    cursor = connection.cursor()

    for index in selected_indexes:
        logging.info(f"Processing index: {index}")
        cursor.execute("SELECT START_OFFSET, SIZE FROM PRECISE_SCAN WHERE idx=?", (index,))
        row = cursor.fetchone()

        if not row:
            logging.warning(f"No data found for index {index}.")
            continue

        start_offset, size = row
        frame_data_file = os.path.join(output_folder, f"{index}.bin")
        
        if size == 0:
            logging.info(f"Index {index} has zero size, skipping extraction.")
            continue

        p_frames = 0
        i_frame_found = False
        i_frame_count = 0

        with open(frame_data_file, 'wb') as fd_file, open(image_filepath, 'rb') as file:
            
            metadata = file.read(0xA0200000)
            frame_type = metadata[26]
            if frame_type == 0x00:  # I-frame
                if not i_frame_found:
                    i_frame_found = True
                else:
                    i_frame_count += 1
            elif frame_type == 0x01 and i_frame_found:  # P-frame
                p_frames += 1            

            file.seek(start_offset + 0xC4)
            data = file.read(size)
            fd_file.write(data)

    frame_cycle = p_frames + 1 if i_frame_count == 0 else p_frames / i_frame_count
    speed_factor = 25.0 / frame_cycle
    logging.info(f"Speed factor for index {index}: {speed_factor}")

    # 모든 프레임 데이터가 추출된 후 MP4로 변환
    output_mp4_file = os.path.join(output_folder, 'Extracted', f'precise_{index}.mp4')
    convert_to_mp4(frame_data_file, output_mp4_file, speed_factor)

    cursor.close()
    connection.close()

# .bin 파일을 .mp4로 변환하는 함수
def convert_to_mp4(input_file, output_file, speed_factor=5.0):
    try:
        (
            ffmpeg
            .input(input_file, format='h264')
            .filter('setpts', f'{speed_factor}*PTS')
            .output(output_file, vcodec='libx264', preset='ultrafast', threads='auto')
            .run(overwrite_output=True)
        )
        logging.info(f"변환 완료: {output_file}")
    except ffmpeg.Error as e:
        logging.error(f"변환 중 오류 발생: {e}")


# 메인 함수
def main(db_filepath, image_filepath, selected_indexes, output_folder='output'):
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    extract_data_from_db(db_filepath, image_filepath, output_folder, selected_indexes)

if __name__ == "__main__":
    db_filepath = 'IDIS_FS_sqlite.db'
    selected_indexes = [1, 2]  # 추출할 데이터의 인덱스 목록
    output_folder = 'output'  # 출력 폴더 경로
    main(db_filepath, selected_indexes, output_folder)
