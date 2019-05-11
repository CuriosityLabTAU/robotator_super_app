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
        print("init run_manager")

        # connection to robot
        # msg:
        #   'play_audio_file', '*.wav' --> animated speech
        self.robot_publisher = rospy.Publisher('to_nao', String, queue_size=10)

        # connection to tablet
        # msg structure: action, 'client_ip'
        self.tablet_publisher = rospy.Publisher('to_tablet', String, queue_size=10)

        rospy.init_node('manager_node') #init a listener:
        rospy.Subscriber('nao_state', String, self.callback_nao_state)
        rospy.Subscriber('tablet_to_manager', String, self.callback_to_manager) # TODO: this is the main function to change
        rospy.Subscriber('sensor_data', String, self.callback_sensor)
        rospy.Subscriber('log', String, self.callback_log)
        self.waiting = False
        self.waiting_timer = False
        self.waiting_robot = False
        i=1
        while i <= self.number_of_tablets:
            self.tablets_audience_agree[i]= None
            i += 1

        print(self.tablets_audience_agree)

        self.robot_end_signal = {}
        self.tablets_done = {}
        self.number_of_tablets_done = self.number_of_tablets
        self.tablets_agree = {}
        self.tablets_mark = {}
        self.tablets_continue = {}

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
        data_file = open(the_lecture_flow_json_file)
        study_sequence = json.load(data_file)
        # self.poses_conditions = logics_json['conditions']

        self.actions = {}

        for seq in study_sequence:
            self.actions[seq['tag']] = seq

        self.run_study_action(self.actions['start'])

    def run_study_action(self, action):
        print(action)
        if action['target'] == 'tablet':
            if "tablets" in action:
                for tablet_id in action['tablets']:
                    try:
                        client_ip = self.tablets_ips[str(tablet_id)]
                        message = action
                        message['client_ip'] = client_ip
                        self.tablet_publisher.publish(json.dumps(message))
                    except:
                        print('not enough tablets')
            next_action = self.actions[action['next']]
            self.run_study_action(next_action)

        elif action['target'] == 'robot':
            if action["action"] in ["play_audio_file"]:
                self.robot_play_audio_file(action)
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

    def robot_wakeup(self, action):
        local_action = {"action": "wake_up"}
        self.run_robot_behavior(local_action)
        local_action = {'action': 'set_autonomous_state', 'parameters': ['solitary']}
        self.run_robot_behavior(local_action)
        next_action = self.actions[action['next']]
        self.run_study_action(next_action)

    def robot_play_audio_file(self, action):
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
        print("start_timer")
        # either go on timeout
        self.sleep_timer = Timer(float(action["seconds"]), self.run_study_action,
                                 [self.actions[action["end"]["timeout"]]])
        self.sleep_timer.start()

        # or go on something else
        self.robot_end_signal = {}
        for k, v in action["end"].items():
            self.robot_end_signal[k] = v
        # TODO: look at person speaks + person least engaged

    def robot_resolution(self, action):
        # first, aggregate data fron sensor and tablets
        # do group-dynamics logic
        # goal: find out whom to address

        # rule: find disagreeing tablets
        pairs = self.find_disagree()

        # rule: find most unspoken people
        unspeaking_rank, most_unspoken = self.find_rank()

        if len(pairs) > 0:
            # rule: find pair who spoke least
            best_pair = pairs[0]
            best_unspoken = 10 # more than twice the number of pariticipants
            for p in pairs:
                unspoken = unspeaking_rank[p[0]] + unspeaking_rank[p[1]]
                if unspoken < best_unspoken:
                    best_unspoken = unspoken
                    best_pair = copy.copy(p)
            # run the appropriate behavior
            parameters = 'discuss_%d_%d' % (best_pair[0], best_pair[1])
        else:
            # address person who spoke least
            parameters = 'explain_%d' % most_unspoken

        nao_message = {"action": 'run_behavior',
                       "parameters": parameters}
        self.robot_end_signal = {action['parameters'][0]: False}
        self.robot_publisher.publish(json.dumps(nao_message))
        while not self.robot_end_signal[action['parameters'][0]]:
            pass

        # sleep
        self.robot_sleep(action)


    def run_robot_behavior(self, nao_message):
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

        print("register_tablet", type(parameters['tablet_id']),client_ip)
        print(self.tablets)
        self.tablets[parameters['tablet_id']] = {'subject_id': parameters['group_id'], 'tablet_ip':client_ip}
        self.tablets_subjects_ids[parameters['tablet_id']] = parameters['group_id']
        self.tablets_ips[parameters['tablet_id']] = client_ip
        self.tablets_ids[client_ip] = parameters['tablet_id']
        self.tablets_audience_done[parameters['tablet_id']] = False
        self.session = parameters['session']

        nao_message = {'action': 'say_text_to_speech', 'client_ip':client_ip,
                       'parameters': ['register tablet', 'tablet_id',str(parameters['tablet_id']),
                                      'group id',str(parameters['group_id'])]}
        self.robot_publisher.publish(json.dumps(nao_message))
        if (len(self.tablets) >= self.number_of_tablets):
            print("two tablets are registered")
            for key,value in self.tablets_ips.viewitems():
                print ("key, value", key, value)
                client_ip = value
                message = {'action':'registration_complete','client_ip':client_ip}
                self.tablet_publisher.publish(json.dumps(message))
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
            {'action': 'play_audio_file', 'parameters': ['/home/nao/naoqi/sounds/dyslexia/s_w15_m7.wav']}
        elif (action == 'audience_done'):
            print("audience_done")
            #self.audience_done(data_json['parameters']['tablet_id'], data_json['parameters']['subject_id'],
            #                   data_json['client_ip'])
        elif ("agree" in action):
            pass
        else:
            print('else', data.data)
            self.robot_publisher.publish(data.data)
        print ("finish manager callback_to_manager")

    def callback_sensor(self, data):
        print("start manager callback_sensor", data.data)

    def callback_log(self, data):
        # print('----- log -----')
        # print('----- log -----', data)
        log = json.loads(data.data)
        # print(log)

        if 'btn_done' in log['obj'] and log['action'] == 'press':
            client_ip = log['client_ip']
            tablet_id = self.tablets_ids[client_ip]
            subject_id = self.tablets_subjects_ids[tablet_id]
            self.count_done = 0
            self.tablets_done[tablet_id] = True
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

        if 'agree' in log['obj'] and log['action'] == 'press':
            client_ip = log['client_ip']
            tablet_id = self.tablets_ids[client_ip]
            subject_id = self.tablets_subjects_ids[tablet_id]
            self.tablets_agree[tablet_id] = not 'disagree' in log['obj']
            self.count_responded = len(self.tablets_agree.keys())
            if (self.count_responded == self.number_of_tablets):
                try:
                    self.sleep_timer.cancel()
                    print("self.sleep_timer.cancel()")
                except:
                    print("failed self.sleep_timer_cancel")
                self.count_responded = 0

                count_agree = 0
                for v in self.tablets_agree.values():
                    if v:
                        count_agree += 1
                if count_agree == self.number_of_tablets:
                    self.run_study_action(self.actions[self.robot_end_signal['all_agree']])
                else:
                    self.run_study_action(self.actions[self.robot_end_signal['not_all_agree']])

        if 'btn_continue' in log['obj'] and log['action'] == 'press' and len(log['comment']) > 1:
            client_ip = log['client_ip']
            tablet_id = self.tablets_ids[client_ip]
            subject_id = self.tablets_subjects_ids[tablet_id]

            if tablet_id not in self.tablets_mark:
                self.tablets_mark[tablet_id] = []
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ log[comment]",log['comment'])
            self.tablets_mark[tablet_id] = json.loads(log['comment']) # TODO: parse the comment

            self.count_continue = 0
            self.tablets_continue[tablet_id] = True
            for value in self.tablets_continue.values():
                if value == True:
                    self.count_continue += 1
            if (self.count_continue == self.number_of_tablets):
                try:
                    self.sleep_timer.cancel()
                    print("self.sleep_timer.cancel()")
                except:
                    print("failed self.sleep_timer_cancel")
                self.count_continue = 0

                # check if same, find two that are not
                tablet_pairs = []
                for t_id_1 in self.tablets_mark.keys():
                    for t_id_2 in self.tablets_mark.keys():
                        if t_id_1 != t_id_2:
                            if len(set(self.tablets_mark[t_id_1]).symmetric_difference(
                                    set(self.tablets_mark[t_id_2])
                            )) > 0: # there is some difference
                                tablet_pairs.append([t_id_1, t_id_2])
                if len(tablet_pairs) == 0: # they are all the same
                    self.run_study_action(self.actions[self.robot_end_signal['all_same']])
                else:
                    the_pair = random.choice(tablet_pairs)
                    self.actions[self.robot_end_signal['not_all_same']]["lookat"] = the_pair
                    self.run_study_action(self.actions[self.robot_end_signal['not_all_same']])


        # if 'audience_done' in log['obj'] and log['action'] == 'press':
        #     client_ip = log['client_ip']
        #     tablet_id = self.tablets_ids[client_ip]
        #     subject_id = self.tablets_subjects_ids[tablet_id]
        #     self.audience_done(tablet_id,subject_id,client_ip)
        #
        # if 'audience_group_done' in log['obj'] and log['action'] == 'press':
        #     client_ip = log['client_ip']
        #     tablet_id = self.tablets_ids[client_ip]
        #     subject_id = self.tablets_subjects_ids[tablet_id]
        #     self.audience_group_done(tablet_id,subject_id,client_ip)
        #
        # if 'audience_list' in log['obj']:
        #     if 'text' in log['action']:
        #         if self.tablets_ids[log['client_ip']] not in self.tablet_audience_data:
        #             self.tablet_audience_data[self.tablets_ids[log['client_ip']]] = 0
        #         self.tablet_audience_data[self.tablets_ids[log['client_ip']]] += 1
        #         print("self.tablet_audience_data", self.tablet_audience_data)
        #
        # if 'agree' in log['obj']:
        #     print("agree in")
        #     # if self.tablets_ids[log['client_ip']] not in self.tablets_audience_agree.values():
        #     #     self.tablets_audience_agree[int(self.tablets_ids[log['client_ip']])] = False
        #     if log['obj'] == 'agree_list' and log['action'] == 'down':
        #         print("agree_list True")
        #         self.tablets_audience_agree[int(self.tablets_ids[log['client_ip']])] = True
        #     elif (log['action'] == 'down'):  #dont_agree_list
        #         print("agree_list False")
        #         self.tablets_audience_agree[int(self.tablets_ids[log['client_ip']])] = False
        #
        #     allVoted = True
        #     i=1
        #     print("self.tablets_audience_agree=", self.tablets_audience_agree)
        #     while i <= self.number_of_tablets:
        #         if (self.tablets_audience_agree[i] == None):
        #             allVoted = False
        #         i += 1
        #     if (allVoted == True):
        #         self.waiting_timer = False
        #         self.sleep_timer.cancel()
        #         print("self.sleep_timer.cancel() ALL VOTED")
        #         self.waiting = False
        #         self.waiting_timer = False

        if self.listen_to_text:
            self.text_audience_group[log['obj']] = log['comment']

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
        most_unspoken_ = sorted_sensor_speak[0]
        rank_sensor_speak_ = {}
        for i, s in enumerate(sorted_sensor_speak):
            rank_sensor_speak_[s] = i
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
