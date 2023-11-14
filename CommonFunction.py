from datetime import datetime

def convert_to_datetime(time_info):
    time_info_bin = bin(time_info)[2:]

    sec = int(time_info_bin[-6:], 2)
    min = int(time_info_bin[-12:-6], 2)
    hour = int(time_info_bin[-17:-12], 2)
    day = int(time_info_bin[-22:-17], 2)
    month = int(time_info_bin[-26:-22], 2)
    year = int(time_info_bin[:-26], 2) + 1970
    return datetime(year, month, day, hour, min, sec)


