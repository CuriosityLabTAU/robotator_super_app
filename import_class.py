import pandas as pd
from convert_text_to_speech_hebrew import *
from os.path import exists
from mp3_to_amplitude import *

class_file = 'student_names.csv'
school_path = 'school_files/'

data = pd.read_csv(school_path + class_file)

for i, row in data.iterrows():
    name_soundfile = school_path + 'user_%d.mp3' % row['username']
    if not exists(name_soundfile):
        print('processing ', name_soundfile)
        tts_heb(row[1], name_soundfile)
    else:
        print(name_soundfile, 'exists!')

path_to_lip_csv(school_path)
