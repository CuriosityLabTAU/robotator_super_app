import threading
import rospy
from std_msgs.msg import String
import json


class CalibrationNode():
    def __init__(self):
        print("init server_node")

        rospy.init_node('tablet_node')
        rospy.Subscriber('conc_speaker', String, self.callback)

        self.current_speaker_info = []
        self.current_speaker_pos = None

        t1 = threading.Thread(target=self.mark)
        t1.start()

        self.tablets = {}

        rospy.spin()

    def callback(self, data):
        speakers = str(data.data)[1:-1].split(',')[1:]
        speaker_data = [speaker[2:-1].split('_') for speaker in speakers]
        speaker_info = []
        for d in speaker_data:
            if len(d) == 2:
                speaker_info.append({'pos': int(d[0]), 'count': int(d[1])})
        for i, s in enumerate(self.current_speaker_info):
            if s['count'] < speaker_info[i]['count']:
                # print('-----', s['pos'])
                self.current_speaker_pos = s['pos']
        self.current_speaker_info = speaker_info

    def mark(self):
        tablet_id = -1
        while True:
            tablet_id = raw_input('Press number of tablet_id (999 to exit) ...\n')
            if tablet_id == '999':
                break
            print(tablet_id, self.current_speaker_pos)
            self.tablets[tablet_id] = self.current_speaker_pos
        print('Saving to calibration file ...')
        json.dump(self.tablets, open('calibration.txt', 'w+'))


cn = CalibrationNode()