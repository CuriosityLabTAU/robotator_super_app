#!/usr/bin/python
# -*- coding: utf-8 -*-
import pickle
import pygame
import time
import rospy
from dynamixel_hr_ros.msg import *
from std_msgs.msg import String
import numpy as np
from scipy.signal import *
import matplotlib.pyplot as plt
from copy import deepcopy
import csv
from scipy.interpolate import interp1d
from scipy.signal import butter, lfilter, filtfilt  #omer
import matplotlib.pyplot as plt
from datetime import datetime
from copy import copy
import json
import threading
import subprocess
import os
from hebrew_tool import *


class RobotodListenerNode():


    def __init__(self):

        self.base_path = '.'

        self.rfids = [None for i in range(5)]
        self.rfid_prev = [None for i in range(5)]
        self.rfid_change = [None for i in range(5)]
        self.is_rfid_change = False

        # self.publisher = rospy.Publisher('/dxl/command_position', CommandPosition, queue_size=10)
        self.publisher = rospy.Publisher('/patricc_motion_control', CommandPosition, queue_size=10)
        self.rifd_sub = rospy.Subscriber('/rfid', String, self.callback)
        rospy.Subscriber('/to_robotod', String, self.callback_to_robotod)
        self.state_publisher = rospy.Publisher('/robotod_state', String, queue_size=1)


        pygame.init()
        pygame.mixer.init()

        self.sound_filename = None
        self.sound_offset = 0.0
        self.lip_filename = None
        self.lip_offset = 0.0

        self.filename = None
        self.duration = 0.0

        self.lip_angle = []
        self.motor_list  = {'skeleton': [0, 1, 4, 5, 6, 7], 'head_pose': [2], 'lip': [3], 'full': [0, 1, 2, 3, 4, 5, 6, 7], 'full_idx': [1, 2, 3, 4, 5, 6, 7, 8]}
        self.robot_angle_range = [[0.0, 5.0], #[1.1, 3.9],
                                  [2.8, 1.6],
                                  [2, 3.3], [1.8, 2.5], #[2.2, 2.5]#[1.8, 2.5], #[2.5, 3.5], #
                                  [4.1, 0.9], [1.3, 3],
                                  [1, 4.1], [2.5, 3.75]]
        self.sensor_angle_range = [[-np.pi, np.pi], [0, np.pi/2],
                                   [-0.2, 0.2], [0, 254],
                                   [-np.pi/2, np.pi/2], [np.pi/2, 0],
                                   [-np.pi/2, np.pi/2], [0, np.pi/2]]
        self.robot_kinect_angles = [0, 1, 0, 0, 2, 3, 4, 5]

        self.robot_motors_no_mouth = [0, 1, 2, 4, 5, 6, 7]
        self.robot_motor_mouth = 4

        self.motor_speed = [1] * 8
        rospy.init_node('block_player')


        # self.initiailize_robotod()
        rospy.spin()

    def run_script(self, script):
        os.system(script)
        # x = subprocess.check_output(script.split(' '))
        return

    def initiailize_robotod(self):
        scripts = {
            # 'roscore': 'roscore',
            # 'rfid': 'rosrun rosserial_python serial_node.py /dev/ttyACM0',
            'expose': 'python ~/PycharmProjects/twisted_server_ros_2_0/scripts/expose.py',
            'motion_control': 'python ~/PycharmProjects/twisted_server_ros_2_0/scripts/motion_control.py'
        }

        for script in scripts.values():
            t = threading.Thread(target=self.run_script, args=(script,))
            t.start()
            threading._sleep(1.0)


    def callback_to_robotod(self, data):
        message = data.data
        try:
            message_dict = json.loads(message)
        except:
            print('ERROR: message is not in json format.')
            return

        action = str(message_dict['action']).encode('utf-8')
        if 'parameters' in message_dict:
            parameters = message_dict['parameters']
        else:
            parameters = ""
        print("PARSE_MESSAGE")
        print(str("self."+action+"("+str(parameters)+")"))

        # TODO Shorashim change!!!
        self.block_name = parameters[0]
        self.sound_filename = parameters[1]
        if len(parameters) > 2:
            self.lip_filename = parameters[2]
        else:
            self.lip_filename = parameters[1][:-4] + '.csv'

        # Convert filenames ro proper filenames
        print(self.sound_filename)
        self.sound_filename = convert_hebrew_to_ascii(self.sound_filename)
        self.lip_filename = convert_hebrew_to_ascii(self.lip_filename)

        self.load_block(self.block_name)
        self.play()

        # self.play_sound()
        # self.play_lip()

        self.state_publisher.publish(data.data)


    def test_motors(self):
        the_range = np.sin(np.linspace(0.0, 2.0 * np.pi, 200)) * 0.5 + 0.5
        dt = 1.0 / 30.0
        for j in range(the_range.shape[0]):
            new_command = CommandPosition()
            new_command.id = [i for i in range(1, 9)]
            new_command.angle = [self.robot_angle_range[i][0] + the_range[j] * (self.robot_angle_range[i][1] - self.robot_angle_range[i][0]) for i in range(8)]
            new_command.speed = [2] * 8

            self.publisher.publish(new_command)
            time.sleep(dt)

    def callback(self, data):
        msg = data.data
        for i in range(5):
            rfid = msg[i*8:(i+1)*8]
            if '---' in rfid:
                self.rfids[i] = None
            else:
                try:
                    self.rfids[i] = rfid_to_prop[rfid]
                except:
                    print(msg)


    def update_rifd(self):
        self.is_rfid_change = False
        for i in range(5):
            if self.rfids[i] != self.rfid_prev[i]:
                self.rfid_change[i] = self.rfid_prev[i]
                self.is_rfid_change = True
            else:
                self.rfid_change[i] = None
        self.rfid_prev = deepcopy(self.rfids)
        return self.is_rfid_change

    # block things
    def load_block(self, block_filename = 'blocks/block_spider_1'):
        self.filename = block_filename
        with open(self.filename, 'rb') as input:
            play_block = pickle.load(input)

        self.full_msg_list = self.clean_msg_list(play_block[1:])

        if not self.sound_filename:
            self.sound_filename = play_block[0][0]
            if self.sound_filename:
                self.sound_filename = self.base_path + self.sound_filename
                self.sound_offset = play_block[0][1]
            else:
                self.sound_offset = None

        # convert hebrew filenames to proper filenames
        self.sound_filename = convert_hebrew_to_ascii(self.sound_filename)
        self.load_files()

        if self.lip_angle:
            self.merge_lip_and_block()

        self.duration = (self.full_msg_list[-1][0] - self.full_msg_list[0][0]).total_seconds()
        print('Block: ', block_filename, '. Duration:', self.duration, ' sound: ', self.sound_filename)

    def clean_msg_list(self, m_list):
        new_list = []
        new_list.append(m_list[0])
        for i in range(1, len(m_list)):
            if (m_list[i][0] - new_list[-1][0]).total_seconds() > 0.001:
                new_list.append(m_list[i])
        return new_list


    def merge_lip_and_block(self):
        lip_times = np.array([self.lip_angle[i][0] for i in range(len(self.lip_angle))])

        msg_list = self.full_msg_list
        new_msg_list = []
        first_item = msg_list[0]
        for iter in range(1, len(msg_list)):
            new_item = msg_list[iter]
            current_time = (new_item[0] - first_item[0]).total_seconds()
            lip_ind = np.argmin(abs(lip_times - current_time))

            current_angles = [new_item[2].angle[m] for m in range(8)]
            new_angle = self.map_angles(self.sensor_angle_range[self.motor_list['lip'][0]],
                                        self.robot_angle_range[self.motor_list['lip'][0]],
                                        self.lip_angle[lip_ind][1])
            current_angles[self.motor_list['lip'][0]] = new_angle

            new_command = CommandPosition()
            new_command.id = [i for i in range(1, 9)]
            new_command.angle = current_angles
            new_command.speed = new_item[2].speed

            new_msg_list.append([self.full_msg_list[iter][0], self.full_msg_list[1], new_command])
        self.full_msg_list = new_msg_list

    def play(self, msg_list=None, motor_commands=None, stop_on_sound=False):
        if msg_list is None:
            msg_list = self.full_msg_list
        first_item = msg_list[0]
        old_item = msg_list[0]
        is_playing = False
        real_output = []
        real_first_time = datetime.now()

        for iter in range(1, len(msg_list)):
            new_item = msg_list[iter]
            current_time = (new_item[0] - first_item[0]).total_seconds()

            real_current_time = (datetime.now() - real_first_time).total_seconds()
            dt = current_time - real_current_time

            # print(real_current_time, current_time, dt)
            if dt > 0.001:
                time.sleep(dt)
                #print(1.0 / dt)
                # calculate speed
                # print(dt, np.array(new_item[2].angle) - np.array(old_item[2].angle))

                new_speed = list(np.abs(np.array(new_item[2].angle) - np.array(old_item[2].angle)) / 2.0)

                old_item = new_item

                if motor_commands is not None:
                    new_item[2].angle = motor_commands[iter,1:]

                # DEBUG
                print('DEBUG')
                print(new_item)
                new_command = CommandPosition()
                new_command.id = [i for i in range(1, 9)]
                new_command.angle = list(new_item[2].angle)
                print(new_command.angle)
                new_command.angle[4] -= np.pi / 2.0
                new_command.angle[6] += np.pi / 2.0
                # new_command.angle[3] = self.map_angles([1.8, 3.5], [1.8, 2.5], new_command.angle[3])

                #print new_item[2].angle[3]
                # new_command.speed = None #new_speed #self.motor_speed
                # new_command.speed = [5]*len(new_item[2].angle)
                new_command.speed = [0.4, 0.4, 2, 7, 5, 5, 5, 5]
                self.publisher.publish(new_command)

                real_output.append(new_command.angle)

                if self.sound_offset is not None:
                    if not is_playing and current_time >= self.sound_offset:
                        is_playing = True
                        pygame.mixer.music.play()
                        print('playing')

                    if is_playing and stop_on_sound:
                        if not pygame.mixer.music.get_busy():
                            if float(iter) / float(len(msg_list)) > 0.80:
                                is_playing = False
                                break

        if is_playing:
            while pygame.mixer.music.get_busy():
                time.sleep(0.020)

        if self.sound_offset:
            pygame.mixer.music.stop()
            print('done playing!')
        np_real_output = np.array(real_output)
        #plt.plot(np_real_output)
        #plt.show()

    def play_msg_list(self, msg_list, stop_on_sound=False):
        first_item = msg_list[0]
        old_item = msg_list[0]
        is_playing = False
        real_output = []
        real_first_time = datetime.now()

        for iter in range(1, len(msg_list)):
            new_item = msg_list[iter]
            current_time = (new_item[0] - first_item[0]).total_seconds()

            real_current_time = (datetime.now() - real_first_time).total_seconds()
            dt = current_time - real_current_time

            # print(real_current_time, current_time, dt)
            if dt > 0.001:
                time.sleep(dt)
                #print(1.0 / dt)
                # calculate speed
                # print(dt, np.array(new_item[2].angle) - np.array(old_item[2].angle))

                new_speed = list(np.abs(np.array(new_item[2].angle) - np.array(old_item[2].angle)) / 2.0)

                old_item = new_item

                new_command = CommandPosition()
                new_command.id = [i for i in range(1, 9)]
                new_command.angle = new_item[2].angle
                # new_command.angle[3] = self.map_angles([1.8, 3.5], [1.8, 2.5], new_command.angle[3])

                #print new_item[2].angle[3]
                # new_command.speed = None #new_speed #self.motor_speed
                # new_command.speed = [5]*len(new_item[2].angle)
                new_command.speed = [0.4, 0.4, 2, 7, 5, 5, 5, 5]
                self.publisher.publish(new_command)

                real_output.append(new_command.angle)

                if self.sound_offset is not None:
                    if not is_playing and current_time >= self.sound_offset:
                        is_playing = True
                        pygame.mixer.music.play()
                        print('playing')

                    if is_playing and stop_on_sound:
                        if not pygame.mixer.music.get_busy():
                            if float(iter) / float(len(msg_list)) > 0.80:
                                is_playing = False
                                break

        if is_playing:
            while pygame.mixer.music.get_busy():
                time.sleep(0.020)

        if self.sound_offset:
            pygame.mixer.music.stop()
            print('done playing!')
        np_real_output = np.array(real_output)
        #plt.plot(np_real_output)
        #plt.show()

    def play_motor_commands(self, motor_commands, stop_on_sound=False):
        first_item = motor_commands[0, :]
        old_item = motor_commands[0, :]
        is_playing = False
        real_first_time = datetime.now()

        for iter in range(1, motor_commands.shape[0]):
            new_item = motor_commands[iter, :]
            current_time = new_item[0] - first_item[0]

            real_current_time = (datetime.now() - real_first_time).total_seconds()
            dt = current_time - real_current_time

            if dt > 0.001:
                time.sleep(dt)
                old_item = new_item

                new_command = CommandPosition()
                new_command.id = [i for i in range(1, 9)]
                new_command.angle = new_item[1:]
                # new_command.angle[3] = self.map_angles([1.8, 3.5], [1.8, 2.5], new_command.angle[3])
                #new_command.angle[3] = new_command.angle[3] + 0.4 #OG
                print new_command.angle
                # new_command.speed = None #new_speed #self.motor_speed
                # new_command.speed = [5]*len(new_item[2].angle)
                new_command.speed = [0.4, 0.4, 2, 3, 5, 5, 5, 5] #[0.4, 0.4, 2, 7, 5, 5, 5, 5]OG
                self.publisher.publish(new_command)

                if self.sound_offset is not None:
                    if not is_playing and current_time >= self.sound_offset:
                        is_playing = True
                        pygame.mixer.music.play()
                        print('playing')

                    if is_playing and stop_on_sound:
                        if not pygame.mixer.music.get_busy():
                            if float(iter) / float(len(msg_list)) > 0.80:
                                is_playing = False
                                break

        if is_playing:
            while pygame.mixer.music.get_busy():
                time.sleep(0.020)

        if self.sound_offset:
            pygame.mixer.music.stop()
            print('done playing!')

    def convert_to_motor_commands(self, full_msg_list=None):
        if not full_msg_list:
            full_msg_list = self.full_msg_list
        motor_commands = np.zeros([len(full_msg_list), 9])
        first_item = full_msg_list[0]
        old_item = full_msg_list[0]
        for iter in range(0, len(full_msg_list)):
            new_item = full_msg_list[iter]
            motor_commands[iter, 0] = (new_item[0] - first_item[0]).total_seconds()
            motor_commands[iter, 1:] = np.array(new_item[2].angle)
        return motor_commands

    def edit(self, motor_commands):
        window_size = 40
        win = hann(window_size)
        temp_motor_commands = np.copy(motor_commands)
        for d in range(0, motor_commands.shape[1]):
            if d != 4:
                #temp_motor_commands[:, d] = convolve(motor_commands[:, d], win, mode='same') / sum(win)
                # the filter
                cutoff = 0.25
                order = 6
                b, a = butter(order, cutoff)#, btype='lowpass', analog=True)
                temp_motor_commands[:, d] = filtfilt(b, a,motor_commands[:, d])
            #else:
            #    temp_motor_commands[:, d] = np.ones(temp_motor_commands[:, d].shape) * 2.3

        #filtered_motor_commands = np.copy(motor_commands)
        #filtered_motor_commands[window_size:-window_size, :] = temp_motor_commands[window_size:-window_size, :]
        filtered_motor_commands = temp_motor_commands
        # plt.plot(motor_commands[:,0], motor_commands[:,6], 'x')
        # plt.plot(filtered_motor_commands[:,0], filtered_motor_commands[:,6],  'o')
        # plt.show()

        return filtered_motor_commands

    def play_editted(self, motor_commands=None, stop_on_sound=False):
        if motor_commands is None:
            motor_commands = self.convert_to_motor_commands()
        filtered_motor_commands = self.edit(motor_commands)
        self.play_motor_commands(motor_commands=filtered_motor_commands, stop_on_sound=stop_on_sound)
        # self.play_motor_commands(motor_commands=motor_commands, stop_on_sound=stop_on_sound)

    # sound and lip things
    def load_files(self):
        self.lip_angle = []
        if self.lip_filename:
            try:
                with open(self.lip_filename, 'rb') as input:
                    self.lip_reader = csv.reader(input)  # get all topics
                    i = 0.0
                    for row in self.lip_reader:
                        self.lip_angle.append((i, float(row[0])))
                        i += 1.0/30.0
            except:
                print('No CSV file for lip has been found')
                self.lip_filename = None

        if self.sound_filename:
            with open(self.sound_filename, 'rb') as input:
                pygame.mixer.music.load(self.sound_filename)

    def play_sound(self, arg1=None, arg2=None):
        time.sleep(float(self.sound_offset))
        pygame.mixer.music.play()

    def play_lip(self, arg1=None, arg2=None):
        time.sleep(float(self.lip_offset))
        old_item = self.lip_angle[0]
        for iter in range(1, len(self.lip_angle)):
            new_item = self.lip_angle[iter]
            current_time = new_item[0]
            dt = (new_item[0] - old_item[0])
            time.sleep(dt)
            old_item = new_item
            self.publishers['/lip_angles'].publish(new_item[1])

    def play_sound_and_lip(self):

        try:
            self.play_sound()
            self.play_lip()
        except:
            self.load_files()
            self.play_sound()
            self.play_lip()

    def map_angles(self, kinect_range, robot_range, psi):
        new_angle = robot_range[0] + (psi - kinect_range[0]) * ((robot_range[1] - robot_range[0]) / (kinect_range[1] - kinect_range[0]))
        return new_angle

    # multi-blocks
    def stitch_blocks(self, block_before=None, block_after=None, motor_commands=None):
        if type(motor_commands) == type(None):
            motor_commands = self.convert_to_motor_commands()

        mouth_commands = copy(motor_commands[:, self.robot_motor_mouth])
        percent = 0.01
        window_size = 5
        win = hann(window_size)

        if block_before:
            if type(block_before) == str:
                with open(block_before, 'rb') as input:
                    play_block = pickle.load(input)
                motor_commands_before = self.convert_to_motor_commands(full_msg_list=play_block[1:])
            else:
                motor_commands_before = self.convert_to_motor_commands(full_msg_list=block_before.full_msg_list)
            n_end = int((1.0 - percent) * motor_commands_before.shape[0])
            n_begin = int(percent * motor_commands.shape[0])

            data = np.concatenate((motor_commands_before[n_end:, :], motor_commands[:n_begin + window_size, :]), axis=0)
            data[-n_begin:, 0] += data[-n_begin-1, 0]
            for d in range(data.shape[1]):
                data[:, d] = convolve(data[:, d], win, mode='same') / sum(win)
            relevant_data = data[-motor_commands[:n_begin, 1:].shape[0]-window_size:-window_size, 1:]
            motor_commands[:n_begin, 1:] = relevant_data

        if block_after:
            if type(block_after) == str:
                with open(block_after, 'rb') as input:
                    play_block = pickle.load(input)
                motor_commands_after = self.convert_to_motor_commands(full_msg_list=play_block[1:])
            else:
                motor_commands_after = self.convert_to_motor_commands(full_msg_list=block_after.full_msg_list)

            n_begin = int(percent * motor_commands_after.shape[0])
            n_end = int((1.0 - percent) * motor_commands.shape[0])

            data = np.concatenate((motor_commands[n_end - window_size:, :], motor_commands_after[:n_begin, :]), axis=0)
            data[-n_begin:, 0] += data[-n_begin-1, 0]
            for d in range(data.shape[1]):
                data[:, d] = convolve(data[:, d], win, mode='same') / sum(win)
            relevant_data = data[window_size:window_size + motor_commands[n_end:, 1:].shape[0], 1:]
            motor_commands[n_end:, 1:] = relevant_data

        motor_commands[:, self.robot_motor_mouth] = mouth_commands

        return motor_commands

    def cut_sub_block(self, start=0.0, end=-1.0):
        sub_block = play_block()
        sub_block.base_path = self.base_path
        sub_block.load_block(self.filename)

        if end < 0.0:
            end = self.duration

        if end < start:
            return None

        # go over current msg_list, and create new one
        sub_block.full_msg_list = []

        msg_list = self.full_msg_list
        first_item = msg_list[0]
        for iter in range(len(msg_list)):
            current_item = msg_list[iter]
            current_time = (current_item[0] - first_item[0]).total_seconds()
            if current_time >= start and current_time <= end:
                sub_block.full_msg_list.append(current_item)
            elif current_time > end:
                break
        sub_block.duration = (sub_block.full_msg_list[-1][0] - sub_block.full_msg_list[0][0]).total_seconds()

        return sub_block




    # behavioral filters
    def behavioral_filters(self, filtered_motor_commands):
        behavioral_motor_commands = np.copy(filtered_motor_commands)
        for d in range(filtered_motor_commands.shape[1]):
            # convert to velocity profile
            velocty_profiles = np.diff(filtered_motor_commands[:, d])

            # find zero velocity points
            v_zero = (np.diff(np.sign(np.diff(velocty_profiles))) > 0).nonzero()[0] + 1 # local min
            t_pose = np.where(np.abs(velocty_profiles[v_zero]) < 0.1)[0]

            behavioral_velocity_profile = np.copy(velocty_profiles)
            # apply filter (while maintaining area)
            for i in range(1, t_pose.shape[0]):
                t_pose_start = t_pose[i-1]
                t_pose_end = t_pose[i]
                duration_pose = v_zero[t_pose_end] - v_zero[t_pose_start]
                v_pose = velocty_profiles[v_zero[t_pose_start]:v_zero[t_pose_end]]
                area = np.sum(v_pose)

                # filter for up-down
                behavioral_pose = np.copy(v_pose)
                mid_duration = int(np.round(duration_pose/2.0))
                v_0 = v_pose[0]
                v_1 = v_pose[-1]
                max_v = (area - mid_duration * (v_0 + v_1)/2.02) / mid_duration

                first_half = behavioral_pose[:mid_duration].shape[0]
                second_half = behavioral_pose[mid_duration:].shape[0]
                behavioral_pose[:mid_duration] = np.linspace(v_pose[0], max_v, num=first_half)
                behavioral_pose[mid_duration:] = np.linspace(max_v, v_pose[-1], num=second_half)

                behavioral_velocity_profile[v_zero[t_pose_start]:v_zero[t_pose_end]] = behavioral_pose

                # plt.plot(v_pose)
                # plt.title('area: %2.3f, num_points: %d' % (np.sum(v_pose), v_pose.shape[0]))
                # plt.show()
                # plt.plot(behavioral_pose)
                # plt.title('area: %2.3f, num_points: %d' % (np.sum(behavioral_pose), behavioral_pose.shape[0]))
                # plt.show()
                # print('done')

            plt.plot(velocty_profiles)
            plt.title('area: %2.3f, num_points: %d' % (np.sum(velocty_profiles), velocty_profiles.shape[0]))
            #plt.show()
            plt.plot(behavioral_velocity_profile)
            plt.title('area: %2.3f, num_points: %d' % (np.sum(behavioral_velocity_profile), behavioral_velocity_profile.shape[0]))
            #plt.show()
            print('done')

            # find the positions
            for i in range(1, behavioral_velocity_profile.shape[0]):
                behavioral_motor_commands[i, d] = behavioral_motor_commands[i-1, d] + behavioral_velocity_profile[i] / 30.0

        return behavioral_motor_commands

try:
    # from command line: first input is an optional nao_ip
    if len(sys.argv) > 1:
        nao = RobotodListenerNode(sys.argv[1])
    else:
        nao = RobotodListenerNode()
except rospy.ROSInterruptException:
    pass
# block_player = play_block()
# block_player.test_motors()
# block_player.lip_filename = 'sounds/fuzzy/fuzzy_banana.csv'
# block_player.sound_filename = 'sounds/fuzzy/fuzzy_banana.mp3'
# block_player.load_block(block_filename='blocks/point_1.new')
# motor_commands = block_player.convert_to_motor_commands()
# filtered_motor_commands = block_player.edit(motor_commands)
# block_player.play(motor_commands=filtered_motor_commands)

