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
        cursor.execute("SELECT START_OFFSET, END_OFFSET, DEL_TYPE, SIZE, I_FRAME, P_FRAME FROM PRECISE_SCAN WHERE idx=?", (index,))
        row = cursor.fetchone()

        if not row:
            logging.warning(f"No data found for index {index}.")
            continue

        start_offset, end_offset, del_type, size, i_frame_count, p_frames = row
        frame_data_file = os.path.join(output_folder, f"{index}.bin")
        
        if size == 0:
            logging.info(f"Index {index} has zero size, skipping extraction.")
            continue

        i_frame_found = False
        if i_frame_count != 0:
            i_frame_found = True

        if del_type == 4:
            with open(frame_data_file, 'wb') as fd_file, open('./'+str(index)+'.bin', 'rb') as origin_file:
                fd_file.write(origin_file.read())
        else:
            with open(frame_data_file, 'wb') as fd_file, open(image_filepath, 'rb') as file:
                file.seek(start_offset, 0)
                while file.tell() < end_offset:
                    metadata = file.read(0xFF)
                    frame_type = metadata[0x1A]
                    frame_size = int.from_bytes(metadata[0x10:0x14], byteorder='little')
                    data = b''
                    sps_offset = 0
                    p_frame_offset = 0

                    if frame_type == 0:
                        sps_offset = metadata.find(b'\x00\x00\x00\x01\x67', 0)
                        file.seek(sps_offset - 0xFF, 1)
                        data = file.read(frame_size + 0xA1 - sps_offset)
                    elif frame_type == 1:
                        p_frame_offset = metadata.find(b'\x00\x00\x00\x01\x21', 0)
                        file.seek(p_frame_offset - 0xFF, 1)
                        data = file.read(frame_size + 0xA1 - p_frame_offset)
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
    db_filepath = '../IDIS_FS_sqlite.db'
    selected_indexes = [1, 2]  # 추출할 데이터의 인덱스 목록
    output_folder = 'output'  # 출력 폴더 경로
    main(db_filepath, selected_indexes, output_folder)
