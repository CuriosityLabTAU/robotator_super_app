import rosbag
from os import listdir
from os.path import isfile, join
import json
import csv
import numpy as np


def parse_person(person_):
    p_data_ = {}
    for p in person_:
        p_info = p.split(':')
        if len(p_info) == 2:
            p_data_[p_info[0]] = p_info[1]
    return p_data_


def parse_data(data_):
    info = str(data_).split(' ')
    id = [i for i, inf in enumerate(info) if 'PersonID' in inf] + [len(info)-1]
    data_ = {}
    for iid in range(0, len(id)-1):
        data_[info[id[iid]]] = parse_person(info[id[iid]:id[iid+1]])
    return data_


bag_files = [f for f in listdir('data/') if isfile(join('data/', f)) and '.bag' in f]
bag_files.sort()
bag_filename = join('data/', bag_files[-1])
print(bag_filename)
bag = rosbag.Bag(bag_filename)
data = {}
total_speak = 0
for topic, msg, t in bag.read_messages(topics=['/omer_data', '/omer_speaker_data']):
    # print(topic, msg)
    if topic == '/omer_data':
        new_data = parse_data(msg)
        for k, v in new_data.items():
            if k not in data:
                data[k] = {
                    'Engagement': [],
                    'Joy': [],
                    'LookAtPerson': [],
                    'Speak': []
                }
            for i in data[k].keys():
                if i != 'Speak':
                    data[k][i].append(v[i])
    if topic == '/omer_speaker_data':
        new_data = json.loads(msg.data)
        id = 'PersonID:%d' % new_data['PersonID']
        if id not in data:
            data[id] = {
                    'Engagement': [],
                    'Joy': [],
                    'LookAtPerson': [],
                    'Speak': 0
                }
        data[id]['Speak'].append(new_data['time'])
        total_speak += 1
bag.close()

report = []
for k, v in data.items():
    report.append({
        'ID': k,
        'Mean Joy': np.mean([float(j) for j in v['Joy']]),
        'Mean Engagement': np.mean([float(e) for e in v['Engagement']]),
        'Speak': float(len(v['Speak'])) * 100.0 / float(total_speak)
    })
print(report)
csv_file = "report.csv"
field_names = ['ID', 'Mean Joy', 'Mean Engagement', 'Speak']
try:
    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        for data in report:
            writer.writerow(data)
except IOError:
    print("I/O error")