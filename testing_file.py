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

import requests
generic_lecture_uuid = u'd9603110-5f25-11ea-9cca-75737e6ac11c'
result = requests.put('http://localhost:8003/apilocaladmin/api/v1/admin/lectures/%s/active' % generic_lecture_uuid).json()
print(result)
print('done!')