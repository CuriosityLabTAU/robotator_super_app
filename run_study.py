import os
import threading
import time
import sys
import requests


def intro(group_id=0, nao_ip='192.168.0.101'):
    start_working(group_id, nao_ip)

    time.sleep(60)


def start_working(group_id, nao_ip):

    def worker1():
        os.system('python ~/PycharmProjects/twisted_server_ros_2_0/scripts/nao_ros_listener.py ' + nao_ip)
        # os.system('python ~/pycharm/curious_game/nao_ros.py ' + nao_ip)
        return

    def worker6():
        os.system('rosbag record -a -o data/robotator_' + str(group_id) + '.bag')

    def worker10():
        os.system('python run_manager.py')

    def worker11(): # initialize server
        os.system('python tablet_node.py')

    def worker12():
        os.system('rostopic pub -1 /to_tablet std_msgs/String "start"')


    t1 = threading.Thread(target=worker1)
    t1.start()
    threading._sleep(2.5)

    t10 = threading.Thread(target=worker10)
    t10.start()
    threading._sleep(0.5)

    t11 = threading.Thread(target=worker11)
    t11.start()
    threading._sleep(0.5)

    raw_input('Press any key to start ...')

    t12 = threading.Thread(target=worker12)
    t12.start()
    threading._sleep(0.2)


if len(sys.argv) > 1:
    print('sys.argv', sys.argv)
    intro(int(sys.argv[1]), sys.argv[2])
else:
    intro()