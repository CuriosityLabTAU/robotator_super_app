import pandas as pd
from convert_text_to_speech_hebrew import *
from os.path import exists
from mp3_to_amplitude import *

speech_file = 'generic_speech.csv'
the_path = 'robot_files/robotod/blocks/'

data = pd.read_csv(the_path + speech_file)

for i, row in data.iterrows():
    name_soundfile = the_path + 'speech_%s.mp3' % row['name']
    if not exists(name_soundfile):
        print('processing ', name_soundfile)
        tts_heb(row[1], name_soundfile)
    else:
        print(name_soundfile, 'exists!')

path_to_lip_csv(the_path)