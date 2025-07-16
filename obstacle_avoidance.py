#!/usr/bin/env python
import rospy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class ObstacleAvoidance:
    def __init__(self):
        # Inicjalizacja węzła ROS
        rospy.init_node('obstacle_avoidance', anonymous=True)
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.sub = rospy.Subscriber('/scan', LaserScan, self.laser_callback)
        self.move_cmd = Twist()
        self.rate = rospy.Rate(10)  # 10 Hz

    def laser_callback(self, data):
        # Odczyt danych z LiDAR
        min_distance = min(data.ranges)  # Najmniejsza odległość do przeszkody
        if min_distance < 0.5:  # Jeśli przeszkoda bliżej niż 0.5 m
            self.move_cmd.linear.x = 0.0  # Zatrzymaj robota
            self.move_cmd.angular.z = 0.5  # Obrót w prawo
            rospy.loginfo("Przeszkoda wykryta! Zatrzymanie i obrót.")
        else:
            self.move_cmd.linear.x = 0.3  # Ruch do przodu
            self.move_cmd.angular.z = 0.0
            rospy.loginfo("Droga wolna, ruch do przodu.")

        self.pub.publish(self.move_cmd)

    def run(self):
        while not rospy.is_shutdown():
            self.rate.sleep()

if __name__ == '__main__':
    try:
        robot = ObstacleAvoidance()
        robot.run()
    except rospy.ROSInterruptException:
        pass