#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import threading
import time
import sys
from run_condition import *
import requests


lecture_number = 1
the_activity = ''

def intro(group_id=0, nao_ip='192.168.0.104'):
    start_working(group_id, nao_ip)

    time.sleep(60)


def start_working(group_id, nao_ip):

    def worker_tablet_coordinator_backend():
        print('starting the tablet coordinator backend...')
        os.system('./tablet_coordinator_backend.sh > /dev/null 2>&1')
        return

    def worker_tablet_coordinator_frontend():
        print('starting the tablet coordinator frontend...')
        os.system('./tablet_coordinator_frontend.sh > /dev/null 2>&1')
        return

    def worker_roscore():
        print('starting roscore ...')
        os.system('roscore > /dev/null 2>&1')
        return

    def worker_robot():
        print('starting %s ...' % which_robot)
        if which_robot == 'nao':
            os.system('python nao_ros_listener.py ' + nao_ip)
        # os.system('python ~/pycharm/curious_game/nao_ros.py ' + nao_ip)
        elif which_robot == 'robotod':
            # os.system('python robotod_ros_listener.py > /dev/null 2>&1')
            os.system('python robotod_ros_listener.py')
        return

    def worker_sensors():
        print('starting sensors...')
        os.system('./run_sensors.sh') # > /dev/null 2>&1')
        return

    def worker_activate_patricc():
        os.system('rostopic pub -1 /patricc_activation_mode std_msgs/String "face_tracking|motion_control"')

    def worker_rosbag():
        os.system('rosbag record -a -o data/robotator_' + str(group_id) + '.bag')

    def worker_manager():
        if the_activity == '':
            os.system('python run_manager.py')
        else:
            os.system('python run_manager.py %s' % the_activity)

    def worker_start_study():
        os.system('rostopic pub -1 /tablet_to_manager std_msgs/String "start the study"')

    def run_thread(worker):
        threading.Thread(target=worker).start()
        threading._sleep(2.0)

    def select_activity():
        lectures = requests.get('http://localhost:8003/apilocaladmin/api/v1/admin/lectures').json()
        print('These are the lectures in the database:')
        for i, lecture in enumerate(lectures):
            print(i, lecture['name'])
        x = raw_input('Select lecture to run ...')
        x = int(x)
        return lectures[x]['name']

    # first, run the tablet coordinator, backend and then frontend
    if is_database:
        run_thread(worker_tablet_coordinator_backend)
        run_thread(worker_tablet_coordinator_frontend)

    # next open roscore
    run_thread(worker_roscore)

    # sensor suit
    if is_sensor:
        run_thread(worker_sensors)
        threading._sleep(6.0)

    if is_robot:
        run_thread(worker_robot)
        run_thread(worker_activate_patricc)

    the_activity = select_activity()

    # run the manager
    # run_thread(worker_manager)

    # start recording
    run_thread((worker_rosbag))



    run_thread(worker_start_study)


if len(sys.argv) > 1:
    print('sys.argv', sys.argv)
    intro(int(sys.argv[1]), sys.argv[2])
else:
    intro()