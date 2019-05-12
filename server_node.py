import json
import rospy
from std_msgs.msg import String
import requests
import time
import copy


class ServerNode():

    number_of_tablets = 2
    tablets = {}    #in the form of {tablet_id_1:{"subject_id":subject_id, "tablet_ip";tablet_ip}
                                    #,tablet_id_2:{"subject_id":subject_id, "tablet_ip";tablet_ip}

    tablets_ips = {}
    tablets_ids = {}
    tablets_subjects_ids = {}

    tablet_audience_data = {}
    tablets_audience_agree = {}
    tablets_audience_done = {}  # by id
    count_audience_done = 0

    attention_tablet = {}
    listen_to_text = None
    text_audience_group = {}
    sleep_timer = None
    run_study_timer = None
    is_audience_done  = False

    waiting = False
    waiting_timer = False
    waiting_robot = False

    session = 'session1'
    robot_end_signal = {}
    tablets_done = {}
    tablets_agree = {}
    tablets_mark = {}
    tablets_continue = {}

    sensor_speak = {}

    def __init__(self):
        print("init server_node")

        rospy.init_node('server_node')
        rospy.Subscriber('to_tablet', String, self.callback)

        self.publisher = rospy.Publisher('tablet_to_manager', String, queue_size=10)

        self.devices = []

        # LECTURES
        self.lectures = requests.get('http://localhost/apilocaladmin/api/v1/admin/lectures').json()
        for lecture in self.lectures:
            res = requests.put('http://localhost/apilocaladmin/api/v1/admin/lectures/%s/active' % lecture['uuid'])
            print(lecture['name'], res)
        self.current_lecture = None

        rospy.spin()


server = ServerNode()



