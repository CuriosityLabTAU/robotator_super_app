import pickle
import numpy as np
from copy import copy
from scipy.signal import hann, convolve
from datetime import timedelta
from dynamixel_hr_ros.msg import *
import pandas as pd


class block():

    def __init__(self):

        self.base_path = '.'

        self.sound_filename = None
        self.sound_offset = 0.0
        self.lip_filename = None
        self.lip_offset = 0.0

        self.filename = None
        self.duration = 0.0

        self.lip_angle = []
        self.motor_list = {'skeleton': [0, 1, 4, 5, 6, 7], 'head_pose': [2], 'lip': [3],
                           'full': [0, 1, 2, 3, 4, 5, 6, 7], 'full_idx': [1, 2, 3, 4, 5, 6, 7, 8]}
        self.robot_angle_range = [[0.0, 5.0],  # [1.1, 3.9],
                                  [2.8, 1.6],
                                  [2, 3.3], [1.8, 2.5],  # [2.2, 2.5]#[1.8, 2.5], #[2.5, 3.5], #
                                  [4.1, 0.9], [1.3, 3],
                                  [1, 4.1], [2.5, 3.75]]
        self.sensor_angle_range = [[-np.pi, np.pi], [0, np.pi / 2],
                                   [-0.2, 0.2], [0, 254],
                                   [-np.pi / 2, np.pi / 2], [np.pi / 2, 0],
                                   [-np.pi / 2, np.pi / 2], [0, np.pi / 2]]
        self.robot_kinect_angles = [0, 1, 0, 0, 2, 3, 4, 5]

        self.robot_motors_no_mouth = [0, 1, 2, 4, 5, 6, 7]
        self.robot_motor_mouth = 4

        self.motor_speed = [1] * 8

    # block things
    def load_block(self, block_filename = 'blocks/block_spider_1'):
        self.filename = block_filename
        with open(self.filename, 'rb') as input:
            play_block = pickle.load(input)
        self.play_block = play_block

        self.full_msg_list = self.clean_msg_list(play_block[1:])

        if not self.sound_filename:
            self.sound_filename = play_block[0][0]
            if self.sound_filename:
                self.sound_filename = self.base_path + self.sound_filename
                self.sound_offset = play_block[0][1]
            else:
                self.sound_offset = None

        self.load_files()

        if self.lip_angle:
            self.merge_lip_and_block()

        self.duration = (self.full_msg_list[-1][0] - self.full_msg_list[0][0]).total_seconds()
        print('Block: ', block_filename, '. Duration:', self.duration, ' sound: ', self.sound_filename)

    def save_stitched_block(self, filename, motor_commands):
        new_block = []
        new_block.append(self.play_block[0])
        basic_item = copy(self.play_block[1])
        cmd_pos = CommandPosition()

        for i, m in enumerate(motor_commands):
            new_cmd_pos = copy(cmd_pos)
            new_cmd_pos.angle = motor_commands[i, 1:]
            new_item = (
                    basic_item[0] + timedelta(seconds=motor_commands[i, 0]),
                    basic_item[1],
                    new_cmd_pos
            )
            new_block.append(new_item)
        pickle.dump(new_block, open(filename, 'w+'))

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

    def add_blocks(self, motor_command1, motor_command2):
        new_motor_commands = np.concatenate((motor_command1, motor_command2))
        t = 0
        j = motor_command1.shape[0]
        for i, m in enumerate(motor_command2):
            last_time = motor_command1[-1, 0]
            new_addition = motor_command2[i, 0]
            new_motor_commands[j, 0] = last_time + new_addition
            j += 1

        return new_motor_commands

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


combos = [
    [20, 10],
    [10, 15],
    [25, 10],
    [30, 10],
    [25, 20],
    [20, 30],
    [40, 15],
    [30, 30],
    [45, 20],
    [40, 30]
]

for c in combos:
    print('-------', c[0], c[1], c[0]+c[1])
    filename_1 = 'robot_files/robotod/blocks/explain_%d.new' % c[0]
    filename_2 = 'robot_files/robotod/blocks/explain_%d.new' % c[1]
    filename_3 = 'robot_files/robotod/blocks/explain_%d.new' % (c[0] + c[1])

    block_1 = block()
    block_1.load_block(filename_1)
    mc_1 = block_1.stitch_blocks(block_before=filename_2)

    block_2 = block()
    block_2.load_block(filename_2)
    mc_2 = block_2.stitch_blocks(block_after=filename_1)

    new_motor_commands = block_1.add_blocks(mc_1, mc_2)
    block_1.save_stitched_block(filename_3, new_motor_commands)

    block_final = block()
    block_final.load_block(filename_3)

    filename_1 = 'robot_files/robotod/blocks/explain_%d.csv' % c[0]
    filename_2 = 'robot_files/robotod/blocks/explain_%d.csv' % c[1]
    filename_3 = 'robot_files/robotod/blocks/explain_%d.csv' % (c[0] + c[1])

    x1 = pd.DataFrame.from_csv(filename_1)
    x2 = pd.DataFrame.from_csv(filename_2)
    x3 = pd.concat([x1, x2])
    x3.to_csv(filename_3)

