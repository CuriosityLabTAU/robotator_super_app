from os import listdir, rename, system
import os
import json
import threading
from read_lecture import *


# get all zip files in Downloads
# for each one
# unzip
# read json
# set list of no. names
# get number to import from console


def worker_tablet_coordinator_backend():
    print('starting the tablet coordinator backend...')
    os.system('./tablet_coordinator_backend.sh > /dev/null 2>&1')
    return


def worker_tablet_coordinator_frontend():
    print('starting the tablet coordinator frontend...')
    os.system('./tablet_coordinator_frontend.sh > /dev/null 2>&1')
    return


def run_thread(worker):
    threading.Thread(target=worker).start()
    threading._sleep(2.0)


run_thread(worker_tablet_coordinator_backend)
run_thread(worker_tablet_coordinator_frontend)


# move from downloads to lecture_files
zip_files = [f for f in listdir('../../Downloads') if '.zip' in f and len(f.split('-')) == 5]
for z in zip_files:
    print("Moved from downloads: ", z)
    rename('../../Downloads/%s' % z, 'lecture_files/%s' % z)

# for all files in lecture files
zip_files = [f for f in listdir('lecture_files') if '.zip' in f and len(f.split('-')) == 5]
lecture_names = []
for z in zip_files:
    print("unzipping: ", z)
    if os.path.isdir('lecture_files/%s' % z[:-4]):
        print('aleady unzipped')
    else:
        system('unzip lecture_files/%s -d lecture_files/%s' % (z, z[:-4]))
    j = json.load(open('lecture_files/%s/%s.json' % (z[:-4], z[:-4])))
    lecture_names.append([j['name'], z[:-4]])

for i, ln in enumerate(lecture_names):
    print(i, ln)


print('Import the lecture into the database.')
x = raw_input('Select lecture to convert ...')
x = int(x)
the_name = lecture_names[x][0]
print(lecture_names[x])

lectures = requests.get('http://localhost:8003/apilocaladmin/api/v1/admin/lectures').json()
for lecture in lectures:
    if the_name in lecture['name']:
        convert_lecture_to_flow_robotod(lecture)
        print('cp lecture_files/%s/* lecture_files/%s/.' % (lecture_names[x][1], lecture_names[x][0]))
        system('cp lecture_files/%s/* lecture_files/%s/.' % (lecture_names[x][1], lecture_names[x][0]))

print("DONE!")

