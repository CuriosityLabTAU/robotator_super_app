import json
import rospy
from std_msgs.msg import String
import time
from threading import Timer
import threading
import random
import operator
import copy

robot_path = '/home/nao/naoqi/sounds/HCI/'
the_lecture_flow_json_file = 'flow_files/"robotator_study.json"'


class ManagerNode():

    number_of_tablets = 1
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



    def __init__(self):
        print("init run_manager")

        # connection to robot
        # msg:
        #   'play_audio_file', '*.wav' --> animated speech
        self.robot_publisher = rospy.Publisher('to_nao', String, queue_size=10)

        # connection to tablet
        # msg structure: action, 'client_ip'
        self.tablet_publisher = rospy.Publisher('to_tablet', String, queue_size=10)

        self.sensor_publisher = rospy.Publisher("/send_msg", String, queue_size=1)

        self.log_publisher = rospy.Publisher('log', String, queue_size=10)

        rospy.init_node('manager_node') #init a listener:
        rospy.Subscriber('nao_state', String, self.callback_nao_state)
        rospy.Subscriber('tablet_to_manager', String, self.callback_to_manager) # TODO: this is the main function to change
        rospy.Subscriber('conc_speaker', String, self.callback_sensor)
        rospy.Subscriber('send_data', String, self.callback_engage)
        rospy.Subscriber('send_speaker_data', String, self.callback_speak)
        # rospy.Subscriber('log', String, self.callback_log)
        self.waiting = False
        self.waiting_timer = False
        self.waiting_robot = False

        self.session = 'lecture_1'

        i=1
        while i <= self.number_of_tablets:
            self.tablets_audience_agree[i]= None
            i += 1

        print(self.tablets_audience_agree)

        self.tablets = {}

        self.robot_end_signal = {}
        self.tablets_done = {}
        self.number_of_tablets_done = self.number_of_tablets
        self.tablets_agree = {}
        self.tablets_mark = {}
        self.tablets_continue = {}

        self.tablet_calibration = json.load(open('calibration.txt'))

        # sensor variables
        self.sensor_speak = {}
        self.engagement = {}
        self.current_speaker = 3

        # robot behavior management variables
        self.is_sleeping = False

        # the flow variables
        self.actions = None

        rospy.spin() #spin() simply keeps python from exiting until this node is stopped

    # TODO: check if needed
    # def run_study(self):
    #     #start running the study
    #     action = {"action": "wake_up"}
    #     self.run_robot_behavior(action)
    #     action = {"action": "show_screen", "screen_name": "ScreenDyslexia", "tablets": [1, 2, 3, 4, 5]}
    #     for tablet_id in action['tablets']:
    #         try:
    #             client_ip = self.tablets_ips[str(tablet_id)]
    #             message = {'action': 'show_screen', 'client_ip': client_ip, 'screen_name': action['screen_name']}
    #             self.tablet_publisher.publish(json.dumps(message))
    #         except:
    #             print('not enough tablets')
    #     # action3 = {"action":"say_text_to_speech", "parameters": ["hello all, how are you today?"]}
    #     action3 = {"action": "wake_up"}
    #     self.run_robot_behavior(action3)
    #     action4 = {'action': 'set_autonomous_state', 'parameters': ['solitary']}
    #     self.run_robot_behavior(action4)
    #     #threading._sleep(4.0)
    #     action5 = {'action': 'play_audio_file', 'parameters': ['/home/nao/naoqi/sounds/dyslexia/introduction.wav']}
    #     self.run_robot_behavior(action5)
    #     #action6 = {"action": "rest"}
    #     #self.run_robot_behavior(action6)

    def run_generic_script(self):
        print("run_study")
        data_file = open('flow_files/%s.json' % self.session)
        study_sequence = json.load(data_file)
        # self.poses_conditions = logics_json['conditions']

        self.actions = {}

        for seq in study_sequence:
            self.actions[seq['tag']] = seq

        self.run_study_action(self.actions['start'])

    def run_study_action(self, action):
        print(action['tag'], action)
        if action['target'] == 'tablet':
            if "tablets" in action:
                for tablet_id in action['tablets']:
                    try:
                        client_ip = self.tablets_ips[str(tablet_id)] #TODO: check
                        message = action
                        message['client_ip'] = client_ip
                        self.tablet_publisher.publish(json.dumps(message))

                        # clear the previous answers
                        # important for collecting the answers that are given
                        self.tablets_mark = {}
                    except:
                        print('not enough tablets')
            next_action = self.actions[action['next']]
            self.run_study_action(next_action)

        elif action['target'] == 'robot':
            if action["action"] in ["play_audio_file", "animated_text_to_speech"]:
                if 'play' in action['action']:
                    self.robot_play_audio_file(action)
                elif 'animated' in action['action']:
                    self.robot_animated_text_to_speech(action)
                if action['next'] != 'end':
                    next_action = self.actions[action['next']]
                    self.run_study_action(next_action)
                else:
                    self.the_end()
            elif action["action"] in ["sleep"]:
                self.robot_sleep(action)
            # TODO: check that required
            # elif action['action'] == 'run_behavior_with_lookat':
            #     the_pair = action['lookat'] # pair of tablet ids
            #     the_pair = sorted([int(i) for i in the_pair])
            #     # Rinat: convert tablet ids to positions (1,2,3,4)
            #
            #     the_action = 'facilitator-6ea3b8/' + 'address_pair_%d_%d' % (int(the_pair[0]), int(the_pair[1]))
            #     nao_message = {"action": 'run_behavior',
            #                    "parameters": [the_action]}
            #     self.robot_publisher.publish(json.dumps(nao_message))
            #
            #     the_action = robot_path + 'general_not_same.wav'
            #     nao_message = {"action": 'play_audio_file',
            #                    "parameters": [the_action]}
            #     self.robot_publisher.publish(json.dumps(nao_message))
            #
            #     self.robot_end_signal = {}
            #     self.robot_end_signal[the_action] = False
            #     while not self.robot_end_signal[the_action]:
            #         pass
            #     if action['next'] != 'end':
            #         next_action = self.actions[action['next']]
            #         self.run_study_action(next_action)
            #     else:
            #         self.the_end()
            elif action["action"] in ["resolution"]:
                self.robot_resolution(action)
            elif "wake_up" in action["action"]:
                self.robot_wakeup(action)

    def robot_animated_text_to_speech(self, action):
        self.is_sleeping = False
        nao_message = {"action": action['action'],
                       "parameters": action['parameters']}
        self.robot_end_signal = {action['parameters'][0]: False}
        self.robot_publisher.publish(json.dumps(nao_message))
        while not self.robot_end_signal[action['parameters'][0]]:
            pass

    def robot_wakeup(self, action):
        local_action = {"action": "wake_up"}
        self.run_robot_behavior(local_action)
        local_action = {'action': 'set_autonomous_state', 'parameters': ['solitary']}
        self.run_robot_behavior(local_action)
        next_action = self.actions[action['next']]
        self.run_study_action(next_action)

    def robot_play_audio_file(self, action):
        self.is_sleeping = False
        # go over parameters and add robot_path
        for i, p in enumerate(action['parameters']):
            if 'wait' not in p:
                action['parameters'][i] = robot_path + p
                if "audio" in action["action"]:
                    action['parameters'][i] += ".wav"

        # send message to robot and wait for reply (from another thread)
        nao_message = {"action": action['action'],
                       "parameters": action['parameters']}
        self.robot_end_signal = {action['parameters'][0]: False}
        self.robot_publisher.publish(json.dumps(nao_message))
        while not self.robot_end_signal[action['parameters'][0]]:
            pass

    def robot_sleep(self, action):
        self.is_sleeping = True
        print("start_timer")
        # either go on timeout
        self.sleep_timer = Timer(float(action["seconds"]), self.run_study_action,
                                 [self.actions[action["end"]["timeout"]]])
        self.sleep_timer.start()

        # or go on something else
        self.robot_end_signal = {}
        for k, v in action["end"].items():
            self.robot_end_signal[k] = v

        print('==== Participants Status =====')
        print(self.engagement)
        print(self.current_speaker)

        # TODO: look at person speaks + person least engaged
        least_engaged = sorted(self.engagement.items(), key=lambda kv: kv[1])
        print('robot_sleep', least_engaged)
        if len(least_engaged) > 0:
            least_engaged = least_engaged[0]
            if least_engaged[1] < 30.0: # not engaged
                self.robot_publisher.publish(json.dumps({
                    "action": 'run_behavior',
                    "parameters": ['Engage_%d' % least_engaged[0]]
                }))
                time.sleep(5)

        while self.is_sleeping:
            self.robot_publisher.publish(json.dumps({
                "action": 'run_behavior',
                "parameters": ['Engage_%d' % self.current_speaker]
            }))
            time.sleep(1)

    def robot_resolution(self, action):
        self.is_sleeping = False
        # first, aggregate data fron sensor and tablets
        # do group-dynamics logic
        # goal: find out whom to address

        # rule: find disagreeing tablets
        pairs = self.find_disagree()
        self.log_publisher.publish(json.dumps({
            'log': 'disagree_pairs',
            'data': pairs
        }))

        # rule: find most unspoken people
        unspeaking_rank, most_unspoken = self.find_rank()
        self.log_publisher.publish(json.dumps({
            'log': 'unspeaking',
            'data': unspeaking_rank
        }))

        if len(pairs) > 0:
            # rule: find pair who spoke least
            best_pair = pairs[0]
            best_unspoken = 10 # more than twice the number of participants
            for p in pairs:
                unspoken = unspeaking_rank[p[0]] + unspeaking_rank[p[1]]
                if unspoken < best_unspoken:
                    best_unspoken = unspoken
                    best_pair = copy.copy(p)
            # run the appropriate behavior
            parameters = 'address_pair_%d_%d' % (best_pair[0], best_pair[1])
        else:
            # address person who spoke least
            parameters = 'explain_%d' % most_unspoken

        nao_message = {"action": 'run_behavior',
                       "parameters": parameters}
        self.robot_end_signal = {action['parameters'][0]: False}
        self.robot_publisher.publish(json.dumps(nao_message))
        while not self.robot_end_signal[action['parameters'][0]]:
            pass

        # reset the counters
        self.sensor_publisher.publish("C")
        time.sleep(0.1)
        self.sensor_publisher.publish("R")

        # sleep
        self.robot_sleep(action)

    def run_robot_behavior(self, nao_message):
        self.is_sleeping = False
        self.robot_publisher.publish(json.dumps(nao_message))
        self.waiting = True
        self.waiting_robot = True
        while self.waiting_robot:
            pass
        print('done waiting_robot', nao_message["action"])


    # ==== handling tablets =====

    def audience_done (self, tablet_id, subject_id, client_ip):
        print("audience_done!!! tablet_id=", tablet_id)
        self.count_audience_done = 0
        print ("values before", self.tablets_audience_done.values())
        self.tablets_audience_done[tablet_id] =  True
        print ("values after",self.tablets_audience_done.values())
        for value in self.tablets_audience_done.values():
            if value ==True:
                self.count_audience_done += 1
                print("self.count_audience_done",self.count_audience_done)

        if (self.count_audience_done == self.number_of_tablets):
            print("self.count_audience_done == self.number_of_tablets",self.count_audience_done,self.number_of_tablets)
            try:
                self.sleep_timer.cancel()
                print("self.sleep_timer.cancel()")
            except:
                print("failed self.sleep_timer_cancel")
            self.waiting_timer = False
            self.is_audience_done = True
            #restart the values for future screens
            self.count_audience_done = 0
            #for key in self.tablets_audience_done.keys():
            #    self.tablets_audience_done[key]=False

    def register_tablet(self, parameters, client_ip):
        if 'robot' not in parameters['condition']:
            print('WRONG CONDITION')
            return

        self.tablets[parameters['tablet_id']] = {'subject_id': parameters['group_id'], 'tablet_ip':client_ip}
        self.tablets_subjects_ids[parameters['tablet_id']] = parameters['group_id']
        self.tablets_ips[parameters['tablet_id']] = client_ip
        self.tablets_ids[client_ip] = parameters['tablet_id']
        self.tablets_audience_done[parameters['tablet_id']] = False
        if parameters['session']:
            self.session = parameters['session']

        nao_message = {'action': 'say_text_to_speech', 'client_ip':client_ip,
                       'parameters': ['register tablet', 'tablet_id',str(parameters['tablet_id']),
                                      'group id',str(parameters['group_id'])]}
        self.robot_publisher.publish(json.dumps(nao_message))
        if (len(self.tablets) >= self.number_of_tablets):
            # TODO: Check, but do not need in current scenario
            # print("two tablets are registered")
            # for key,value in self.tablets_ips.viewitems():
            #     print ("key, value", key, value)
            #     client_ip = value
            #     message = {'action':'registration_complete','client_ip':client_ip}
            #     self.tablet_publisher.publish(json.dumps(message))
            #time.sleep(2)
            self.run_study_timer = Timer(5.0, self.run_generic_script())
        print("finish register_tablet")


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CALLBACK FUNCTIONS
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def callback_nao_state(self, data):
        # get messages back from the robot
        # the only thing here is the end of a behavior/audio
        print("manager callback_nao_state", data.data, self.waiting_robot)
        if 'register tablet' not in data.data and 'sound_tracker' not in data.data:
            self.waiting = False
            self.waiting_robot = False

            try:
                signal = json.loads(data.data)['parameters'][0]
                self.robot_end_signal[signal] = True
            except:
                pass
            # message = data.data
            # rospy.loginfo(message)
            # self.tablet_publisher.publish(message)
            # self.nao.parse_message(message)



    # TODO: main function to change
    def callback_to_manager(self, data):
        print("start manager callback_to_manager", data.data)
        data_json = json.loads(data.data)
        action = data_json['action']
        if (action == 'register_tablet'):
            self.register_tablet(data_json['parameters'],
                                 data_json['client_ip'])
            # {'action': 'play_audio_file', 'parameters': ['/home/nao/naoqi/sounds/dyslexia/s_w15_m7.wav']}
        elif action == 'participant_done':
            client_ip = data_json['client_ip']
            tablet_id = self.tablets_ids[client_ip]
            self.count_done = 0
            self.tablets_done[tablet_id] = True
            self.tablets_mark[tablet_id] = data_json['answer']
            for value in self.tablets_done.values():
                if value == True:
                    self.count_done += 1
            if (self.count_done == self.number_of_tablets_done):
                try:
                    self.sleep_timer.cancel()
                    print("self.sleep_timer.cancel()")
                except:
                    print("failed self.sleep_timer_cancel")
                self.count_done = 0
                self.run_study_action(self.actions[self.robot_end_signal['done']])
            print("audience_done")
            #self.audience_done(data_json['parameters']['tablet_id'], data_json['parameters']['subject_id'],
            #                   data_json['client_ip'])
        elif ("agree" in action):
            pass
        else:
            print('else', data.data)
            self.robot_publisher.publish(data.data)
        print ("finish manager callback_to_manager")

    def pos_to_tablet(self, speaker_info):
        # convert the position from the directional microphone, to tablet id, via the calibration file
        tablet_info = {}
        for info in speaker_info:
            dist = 1000000
            best_fit = None
            for tab_id, tab_pos in self.tablet_calibration.items():
                if abs(tab_pos - info['pos']) < dist:
                    dist = abs(tab_pos - info['pos'])
                    best_fit = int(tab_id)
            tablet_info[best_fit] = info['count']
        return tablet_info

    def callback_sensor(self, data):
        # print("start manager callback_sensor", data.data)
        # parsing the message
        speakers = str(data.data)[1:-1].split(',')[1:]
        speaker_data = [speaker[2:-1].split('_') for speaker in speakers]
        speaker_info = []
        for d in speaker_data:
            if len(d) == 2:
                speaker_info.append({'pos': int(d[0]), 'count': int(d[1])})
        self.sensor_speak = self.pos_to_tablet(speaker_info)

    def callback_engage(self, data):
        subject_data = str(data.data).split(' ')
        engage_data = float([d.split(':')[1] for d in subject_data if 'Engagement' in d][0])
        if engage_data != 0.0:
            pos_data = float([d.split(':')[1] for d in subject_data if 'Location' in d][0])
            tablet_engage = self.pos_to_tablet([{'pos': pos_data, 'count': engage_data}])
            self.engagement[tablet_engage.keys()[0]] = tablet_engage.values()[0]

    def callback_speak(self, data):
        subject_data = json.loads(str(data.data))
        self.current_speaker = self.pos_to_tablet([{'pos': subject_data['x'], 'count': 0}]).keys()[0]
        print('Got speaker data: current speaker', self.current_speaker)

    # TODO: probably don't need at all
    # def callback_log(self, data):
    #     # print('----- log -----')
    #     # print('----- log -----', data)
    #     log = json.loads(data.data)
    #     # print(log)
    #
    #     if 'btn_done' in log['obj'] and log['action'] == 'press':
    #         client_ip = log['client_ip']
    #         tablet_id = self.tablets_ids[client_ip]
    #         subject_id = self.tablets_subjects_ids[tablet_id]
    #         self.count_done = 0
    #         self.tablets_done[tablet_id] = True
    #         for value in self.tablets_done.values():
    #             if value == True:
    #                 self.count_done += 1
    #         if (self.count_done == self.number_of_tablets_done):
    #             try:
    #                 self.sleep_timer.cancel()
    #                 print("self.sleep_timer.cancel()")
    #             except:
    #                 print("failed self.sleep_timer_cancel")
    #             self.count_done = 0
    #             self.run_study_action(self.actions[self.robot_end_signal['done']])
    #
    #     if 'agree' in log['obj'] and log['action'] == 'press':
    #         client_ip = log['client_ip']
    #         tablet_id = self.tablets_ids[client_ip]
    #         subject_id = self.tablets_subjects_ids[tablet_id]
    #         self.tablets_agree[tablet_id] = not 'disagree' in log['obj']
    #         self.count_responded = len(self.tablets_agree.keys())
    #         if (self.count_responded == self.number_of_tablets):
    #             try:
    #                 self.sleep_timer.cancel()
    #                 print("self.sleep_timer.cancel()")
    #             except:
    #                 print("failed self.sleep_timer_cancel")
    #             self.count_responded = 0
    #
    #             count_agree = 0
    #             for v in self.tablets_agree.values():
    #                 if v:
    #                     count_agree += 1
    #             if count_agree == self.number_of_tablets:
    #                 self.run_study_action(self.actions[self.robot_end_signal['all_agree']])
    #             else:
    #                 self.run_study_action(self.actions[self.robot_end_signal['not_all_agree']])
    #
    #     if 'btn_continue' in log['obj'] and log['action'] == 'press' and len(log['comment']) > 1:
    #         client_ip = log['client_ip']
    #         tablet_id = self.tablets_ids[client_ip]
    #         subject_id = self.tablets_subjects_ids[tablet_id]
    #
    #         if tablet_id not in self.tablets_mark:
    #             self.tablets_mark[tablet_id] = []
    #         print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ log[comment]",log['comment'])
    #         self.tablets_mark[tablet_id] = json.loads(log['comment']) # TODO: parse the comment
    #
    #         self.count_continue = 0
    #         self.tablets_continue[tablet_id] = True
    #         for value in self.tablets_continue.values():
    #             if value == True:
    #                 self.count_continue += 1
    #         if (self.count_continue == self.number_of_tablets):
    #             try:
    #                 self.sleep_timer.cancel()
    #                 print("self.sleep_timer.cancel()")
    #             except:
    #                 print("failed self.sleep_timer_cancel")
    #             self.count_continue = 0
    #
    #             # check if same, find two that are not
    #             tablet_pairs = []
    #             for t_id_1 in self.tablets_mark.keys():
    #                 for t_id_2 in self.tablets_mark.keys():
    #                     if t_id_1 != t_id_2:
    #                         if len(set(self.tablets_mark[t_id_1]).symmetric_difference(
    #                                 set(self.tablets_mark[t_id_2])
    #                         )) > 0: # there is some difference
    #                             tablet_pairs.append([t_id_1, t_id_2])
    #             if len(tablet_pairs) == 0: # they are all the same
    #                 self.run_study_action(self.actions[self.robot_end_signal['all_same']])
    #             else:
    #                 the_pair = random.choice(tablet_pairs)
    #                 self.actions[self.robot_end_signal['not_all_same']]["lookat"] = the_pair
    #                 self.run_study_action(self.actions[self.robot_end_signal['not_all_same']])
    #
    #
    #     # if 'audience_done' in log['obj'] and log['action'] == 'press':
    #     #     client_ip = log['client_ip']
    #     #     tablet_id = self.tablets_ids[client_ip]
    #     #     subject_id = self.tablets_subjects_ids[tablet_id]
    #     #     self.audience_done(tablet_id,subject_id,client_ip)
    #     #
    #     # if 'audience_group_done' in log['obj'] and log['action'] == 'press':
    #     #     client_ip = log['client_ip']
    #     #     tablet_id = self.tablets_ids[client_ip]
    #     #     subject_id = self.tablets_subjects_ids[tablet_id]
    #     #     self.audience_group_done(tablet_id,subject_id,client_ip)
    #     #
    #     # if 'audience_list' in log['obj']:
    #     #     if 'text' in log['action']:
    #     #         if self.tablets_ids[log['client_ip']] not in self.tablet_audience_data:
    #     #             self.tablet_audience_data[self.tablets_ids[log['client_ip']]] = 0
    #     #         self.tablet_audience_data[self.tablets_ids[log['client_ip']]] += 1
    #     #         print("self.tablet_audience_data", self.tablet_audience_data)
    #     #
    #     # if 'agree' in log['obj']:
    #     #     print("agree in")
    #     #     # if self.tablets_ids[log['client_ip']] not in self.tablets_audience_agree.values():
    #     #     #     self.tablets_audience_agree[int(self.tablets_ids[log['client_ip']])] = False
    #     #     if log['obj'] == 'agree_list' and log['action'] == 'down':
    #     #         print("agree_list True")
    #     #         self.tablets_audience_agree[int(self.tablets_ids[log['client_ip']])] = True
    #     #     elif (log['action'] == 'down'):  #dont_agree_list
    #     #         print("agree_list False")
    #     #         self.tablets_audience_agree[int(self.tablets_ids[log['client_ip']])] = False
    #     #
    #     #     allVoted = True
    #     #     i=1
    #     #     print("self.tablets_audience_agree=", self.tablets_audience_agree)
    #     #     while i <= self.number_of_tablets:
    #     #         if (self.tablets_audience_agree[i] == None):
    #     #             allVoted = False
    #     #         i += 1
    #     #     if (allVoted == True):
    #     #         self.waiting_timer = False
    #     #         self.sleep_timer.cancel()
    #     #         print("self.sleep_timer.cancel() ALL VOTED")
    #     #         self.waiting = False
    #     #         self.waiting_timer = False
    #
    #     if self.listen_to_text:
    #         self.text_audience_group[log['obj']] = log['comment']

# ===== Group dynamics functions ====

    # based on tablet_marks, find a pair that disagrees

    def find_disagree(self):
        # check if same, find two that are not
        tablet_pairs = []
        for t_id_1 in self.tablets_mark.keys():
            for t_id_2 in self.tablets_mark.keys():
                if t_id_1 != t_id_2:
                    if len(set(self.tablets_mark[t_id_1]).symmetric_difference(
                            set(self.tablets_mark[t_id_2])
                    )) > 0:  # there is some difference
                        tablet_pairs.append([t_id_1, t_id_2])
        return tablet_pairs

    def find_rank(self):    # TODO: check
        sorted_sensor_speak = sorted(self.sensor_speak.items(), key=lambda kv: kv[1])
        most_unspoken_ = sorted_sensor_speak[0][0]
        rank_sensor_speak_ = {}
        for i, s in enumerate(sorted_sensor_speak):
            rank_sensor_speak_[s[0]] = i
        return rank_sensor_speak_, most_unspoken_

    def the_end(self):
        action = {"action": "rest"}
        self.run_robot_behavior(action)
        print('THE END')

if __name__ == '__main__':
    try:
        manager = ManagerNode()
        # manager.run_study()
    except rospy.ROSInterruptException:
        pass
