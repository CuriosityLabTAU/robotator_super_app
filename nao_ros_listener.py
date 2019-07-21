import json
import rospy
from std_msgs.msg import String
from nao_alproxy import NaoALProxy
import sys


class NaoListenerNode():
    def __init__(self, nao_ip=None):
        self.nao_alproxy = NaoALProxy(nao_ip)
        self.nao_alproxy.start_nao()
        self.publisher = rospy.Publisher('nao_state', String, queue_size=1)
        rospy.init_node('nao_listener_node') #init a listener:
        rospy.Subscriber('to_nao', String, self.callback_to_nao, queue_size=1)
        # rospy.Subscriber('nao_state', String, self.callback_nao_state)
        print('=========== NaoListenerNode =============')
        rospy.spin() #spin() simply keeps python from exiting until this node is stopped

    def callback_to_nao (self, data):
        # print("callback_robotator", data.data)
        message = data.data
        # rospy.loginfo(message)
        self.nao_alproxy.parse_message(message)
        # print("finished", message)
        self.publisher.publish(data.data) #publish to nao_state to indicate that the robot command is complete

    #def callback_nao_state (self, data):
    #    print("nao_ros_listener callback_nao_state", data.data)

if __name__ == '__main__':
    try:
        # from command line: first input is an optional nao_ip
        if len(sys.argv) > 1:
            nao = NaoListenerNode(sys.argv[1])
        else:
            nao = NaoListenerNode()
    except rospy.ROSInterruptException:
        pass