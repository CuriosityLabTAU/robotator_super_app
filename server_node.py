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
            requests.put('http://localhost/apilocaladmin/api/v1/admin/lectures/%s/active' % lecture['uuid'])
        self.current_lecture = None

    def start(self):
        self.current_lecture = '' # TODO: get it somehow

        # DEVICES
        print('----- devices -----')
        self.devices = requests.get('http://localhost/apilocaladmin/api/v1/device/getAll').json()
        self.number_of_tablets = len(self.devices)

        # register all tablets
        for d in self.devices:
            d_info = d['user_name'].split(',')
            group_id = d_info[0]
            tablet_id = d_info[1]

            device_message = {'action': 'register_tablet',
                              'client_ip':d['id'],
                              'parameters': {
                                  'session': self.current_lecture,
                                  'tablet_id': tablet_id,
                                  'group_id': group_id
                              }
                              }
            self.publisher.publish(json.dumps(device_message))
            time.sleep(1)

    def callback(self, data):
        info = json.loads(data.data)
        the_section = info['screen_name']
        the_tablet = info['client_ip']

        self.current_section = '' # TODO
        current_section_order = 0
        # TODO: show section

        if info['response']:
            duration = info['duration']

            current_answers = requests.get('http://localhost/apilocaladmin/api/v1/lecture/%s/answers' %
                                           self.current_lecture['uuid']).json()[current_section_order]['answers']

            # if the section requires response, if someone answered, publish it, until all answered or time passes
            start_time = time.time()
            while (time.time() - start_time) < duration:
                new_answers = requests.get(
                    'http://localhost/apilocaladmin/api/v1/lecture/%s/answers' % self.current_lecture['uuid']).json()[
                    current_section_order]['answers']
                for i_answer, answer in enumerate(new_answers):
                    if current_answers[i_answer]['answered'] == 0 and new_answers[i_answer]['answered'] == 1:
                        # means that the tablet has answered
                        done_message = {'action': 'participant_done',
                                        'client_ip': answer['id'],
                                        'the_answer': answer['answer']
                                        }
                        self.publisher.publish(json.dumps(done_message))
                time.sleep(0.1)
                current_answers = copy.copy(new_answers)




