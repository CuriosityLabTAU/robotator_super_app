import json
import rospy
from std_msgs.msg import String
import requests
import time
import copy
from run_condition import *


class TabletNode():

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

    def __init__(self, lecture_number=1):
        print("init server_node")

        rospy.init_node('tablet_node')
        rospy.Subscriber('to_tablet', String, self.callback, queue_size=1)

        self.publisher = rospy.Publisher('tablet_to_manager', String, queue_size=1)

        self.devices = []

        self.current_lecture = None
        if database:
            # LECTURES
            self.lectures = requests.get('http://localhost/apilocaladmin/api/v1/admin/lectures').json()
            for lecture in self.lectures:
                res = requests.put('http://localhost/apilocaladmin/api/v1/admin/lectures/%s/active' % lecture['uuid'])
                print(lecture['name'], res)
                if lecture['name'] == 'HCI_1':
                    self.current_lecture = lecture
                    self.first_section = json.loads(self.current_lecture['sectionsOrdering'])[0]
        rospy.spin()

    def start(self, lecture_number='1'):
        for lecture in self.lectures:
            if lecture['name'] == 'HCI_%s' % lecture_number:
                self.current_lecture = lecture
        self.first_section = json.loads(self.current_lecture['sectionsOrdering'])[0]

        if database:
            # DEVICES
            print('----- devices -----')
            self.devices = requests.get('http://localhost/apilocaladmin/api/v1/device/getAll').json()
        else:
            self.devices = [{
                'id': 1,
                'user_name': '1,1'
            }
            ]
        # set the first section to be the first section
        r = requests.post('http://localhost/apilocaladmin/api/v1/admin/lectureSwitchSection', data={
            'lectureUUID': self.current_lecture['uuid'],
            'sectionUUID': self.first_section
        })
        print('tablet_node', 'switch to first section', r, r.text)

        # DEVICES
        print('----- devices -----')
        self.devices = requests.get('http://localhost/apilocaladmin/api/v1/device/getAll').json()
        self.number_of_tablets = len(self.devices)


        # register all tablets
        for d in self.devices:
            try:
                d_info = d['user_name'].split(',')
                group_id = d_info[0]
                tablet_id = d_info[1]

                device_message = {'action': 'register_tablet',
                                  'client_ip': d['id'],
                                  'parameters': {
                                      'session': self.current_lecture,
                                      'tablet_id': tablet_id,
                                      'group_id': group_id,
                                      'condition': 'robot'
                                  }
                                  }
                self.publisher.publish(json.dumps(device_message))
                print('tablet_node: published tablet ', d['user_name'])
                time.sleep(1)
            except:
                print('ERROR: please enter a correct username: group_id, tablet_id. ', d['user_name'])

    def get_current_answers(self):
        all_answers = requests.get('http://localhost/apilocaladmin/api/v1/lecture/%s/answers' %
                                   self.current_lecture['uuid']).json()
        current_answers = [a['answers'] for a in all_answers if a['uuid'] == self.current_section][0]
        tablet_answers = {}
        for ca in current_answers:
            tablet_answers[ca['device_id']] = ca
        return tablet_answers

    def callback(self, data):
        print('tablet_node, callback', data.data)
        if 'start' in data.data:
            self.start(data.data[-1])
            return

        for d in self.devices:
            r = requests.get('http://localhost/apilocaladmin/api/v1/device/%s/freezeStatus' % d['id'])
            print('freeze status', d['id'], r, r.text)
        r = requests.post('http://localhost/apilocaladmin/api/v1/admin/defreezeDeviceAll')
        for d in self.devices:
            r = requests.post('http://localhost/apilocaladmin/api/v1/device/%s/toggleFrozen' % d['id'])
        for d in self.devices:
            r = requests.get('http://localhost/apilocaladmin/api/v1/device/%s/freezeStatus' % d['id'])
        #     print('freeze status', d['id'], r, r.text)

        print('====', 'tablet_node', data.data)
        info = json.loads(data.data)
        self.current_section = info['screen_name']

        r = requests.post('http://localhost/apilocaladmin/api/v1/admin/lectureSwitchSection', data={
            'lectureUUID': self.current_lecture['uuid'],
            'sectionUUID': self.current_section
        })

        if info['response']:
            duration = info['duration']

            current_answers = self.get_current_answers()

            # if the section requires response, if someone answered, publish it, until all answered or time passes
            start_time = time.time()
            while (time.time() - start_time) < duration:
                new_answers = self.get_current_answers()

                for i_answer, answer in new_answers.items():
                    if current_answers[i_answer]['answered'] == 0 and new_answers[i_answer]['answered'] == 1:
                        # means that the tablet has answered
                        done_message = {'action': 'participant_done',
                                        'client_ip': answer['device_id'],
                                        'answer': answer['answer']
                                        }
                        self.publisher.publish(json.dumps(done_message))
                        print('published:', done_message)
                time.sleep(0.1)
                current_answers = copy.copy(new_answers)

tablet = TabletNode()



