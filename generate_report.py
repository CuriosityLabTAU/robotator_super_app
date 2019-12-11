import rosbag
from os import listdir
from os.path import isfile, join


def parse_person(person_):
    p_data_ = {}
    for p in person_:
        p_info = p.split(':')
        if len(p_info) == 2:
            p_data_[p_info[0]] = p_info[1]
    return p_data_


def parse_data(data_):
    info = str(data_).split(' ')
    for i in info:
        print(i)
    id = [i for i, inf in enumerate(info) if 'PersonID' in inf] + [len(info)-1]
    data_ = {}
    for iid in range(0, len(id)-1):
        data_[info[id[iid]]] = parse_person(info[id[iid]:id[iid+1]])
    return data_


bag_files = [f for f in listdir('data/') if isfile(join('data/', f)) and '.bag' in f]
print(bag_files)
bag_filename = join('data/', bag_files[-1])
print(bag_filename)
bag = rosbag.Bag(bag_filename)
data = {}
for topic, msg, t in bag.read_messages(topics=['/omer_data', '/omer_speaker_data']):
    print(topic, msg)
    # if topic == '/omer_data':
    #     new_data = parse_data(msg)
    #     for k, v in new_data.items():
    #         if k not in data:
    #             data[k] = {
    #                 'Engagement': [],
    #                 'Joy': [],
    #                 'LookAtPerson': []
    #             }
    #         for i in data[k].keys():
    #             data[k][i].append(v[i])
    # if topic == '/ReSpeaker':
    #     print(msg)
    # print(data)
bag.close()