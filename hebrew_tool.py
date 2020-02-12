#!/usr/bin/python
# -*- coding: utf-8 -*-
from os import system, listdir
import json


def is_english(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def convert_hebrew_to_ascii(s):
    if is_english(s):
        return s
    else:
        ascii_string = s.decode('utf-8').encode('ascii', 'xmlcharrefreplace')
        ascii_string = ascii_string.replace('&#', '').replace(';', '').replace(' ', '')
        return ascii_string

def convert_mp3_csv_to_proper_names(lecture_path):
    print('Convert sound and lip to ascii...')

    conversion = {}

    mp3_files = [f for f in listdir(lecture_path) if '.mp3' in f]
    for mp3_file in mp3_files:
        before_name = '\"%s/%s\"' % (lecture_path, mp3_file)
        after_name = '%s/%s' % (lecture_path, convert_hebrew_to_ascii(mp3_file))
        conversion[before_name.decode('utf-8')] = after_name
        if before_name == after_name:
            print('same name, dont copy.')
        else:
            system('cp %s %s' % (before_name, after_name))

    csv_files = [f for f in listdir(lecture_path) if '.csv' in f]
    for csv_file in csv_files:
        before_name = '\"%s/%s\"' % (lecture_path, csv_file)
        after_name = '%s/%s' % (lecture_path, convert_hebrew_to_ascii(csv_file))
        conversion[before_name.decode('utf-8')] = after_name
        if before_name == after_name:
            print('same name, dont copy.')
        else:
            system('cp %s %s' % (before_name, after_name))
    json.dump(conversion, open('%s/conversion.json' % lecture_path, 'w+'))#, ensure_ascii=True)