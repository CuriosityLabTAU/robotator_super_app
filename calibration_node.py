import threading
import os
import rospy
from std_msgs.msg import String
import json


class CalibrationNode():
    def __init__(self):
        print("init server_node")

        rospy.init_node('tablet_node')
        rospy.Subscriber('/conc_speaker', String, self.callback)

        self.current_speaker_info = {}
        self.current_speaker_pos = None

        t1 = threading.Thread(target=self.mark)
        t1.start()

        self.tablets = {}

        rospy.spin()

    def callback(self, data):
        speaker_info = json.loads(data.data)#str(data.data)[1:-1].split(',')[1:]
        for k, v in self.current_speaker_info.items():
            if v['count'] < speaker_info[k]['count']:
                # print('-----', s['pos'])
                self.current_speaker_pos = v['pos']
        self.current_speaker_info = speaker_info
        print(self.current_speaker_info)

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


def worker_sensors():
    print('starting sensors...')
    os.system('./run_sensors.sh > /dev/null 2>&1')
    return


def run_thread(worker):
    threading.Thread(target=worker).start()
    threading._sleep(2.0)

run_thread(worker_sensors)

cn = CalibrationNode()