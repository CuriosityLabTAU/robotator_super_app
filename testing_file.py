import os
import threading
import rospy
from std_msgs.msg import String
import json


# nao_ip = '192.168.0.101'
#
# def worker1():
#     os.system('python ~/PycharmProjects/twisted_server_ros_2_0/scripts/nao_ros_listener.py ' + nao_ip)
#     # os.system('python ~/pycharm/curious_game/nao_ros.py ' + nao_ip)
#     return
#
#
# t1 = threading.Thread(target=worker1)
# t1.start()
# threading._sleep(2.5)
#
#
# class TestNode():
#
#     def __init__(self):
#         rospy.init_node('TestNode')
#         self.robot_publisher = rospy.Publisher('to_nao', String, queue_size=10)
#
#         t = threading.Thread(target=self.run)
#         t.start()
#
#         rospy.spin()
#
#     def run(self):
#         while True:
#             raw_input('Press any key to run ...')
#             # self.robot_publisher.publish(json.dumps({
#             #         "action": 'run_behavior',
#             #         "parameters": ['address_pair_1_2']
#             #     }))
#             self.robot_publisher.publish(json.dumps({
#                     "action": 'print_installed_behaviors'
#                 }))
#             # self.robot_publisher.publish(json.dumps({
#             #         "action": 'play_audio_file',
#             #         "parameters": ['general_not_same.wav']
#             #     }))
#
#
# tn = TestNode()

server_url = '3.14.152.95:8003'

import requests
# generic_lecture_uuid = u'd9603110-5f25-11ea-9cca-75737e6ac11c'
# result = requests.put('http://localhost:8003/apilocaladmin/api/v1/admin/lectures/%s/active' % generic_lecture_uuid).json()
# print(result)
# print('done!')
# read_devices = requests.get('http://18.224.140.36:8003/apilocaladmin/api/v1/device/getAll').json()
# read_devices = requests.get('http://ip-172-31-27-23:8003/apilocaladmin/api/v1/device/getAll').json()
read_devices = requests.get('http://%s/apilocaladmin/api/v1/device/getAll' % server_url).json()
# read_devices = requests.get('http://3.14.152.95:8001/apilocaladmin').json()
x = requests.get('http://%s/apilocaladmin/api/v1/admin/lectures' % server_url).json()
print(x)


def select_activity():
    lectures = requests.get('http://%s/apilocaladmin/api/v1/admin/lectures' % server_url).json()
    print('These are the lectures in the database:')
    for i, lecture in enumerate(lectures):
        print(i, lecture['name'], lecture['uuid'])
        result = requests.put(
            'http://%s/apilocaladmin/api/v1/admin/lectures/%s/active' % (server_url, lecture['uuid'])).json()
        if result['active']:
            requests.put(
                'http://%s/apilocaladmin/api/v1/admin/lectures/%s/active' % (server_url, lecture['uuid'])).json()

    x = raw_input('Select lecture to run ...')
    x = int(x)
    requests.put(
        'http://%s/apilocaladmin/api/v1/admin/lectures/%s/active' % (server_url, lectures[x]['uuid'])).json()
    raw_input('press any key to start ...')

# select_activity()

from run_condition import *
read_devices = requests.get('http://%s/apilocaladmin/api/v1/device/getAll' % ip_coordinator).json()
print(read_devices)