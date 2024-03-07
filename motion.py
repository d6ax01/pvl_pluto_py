from __future__ import with_statement
import json

class Motion():

    def __init__(self):
        global axis_no
        global max_speed
        global neg_limit
        global pos_limit
        global origin_type 
        global speed_origin
        global motor_type
        global resolution
        global com_port
        global acceleration
        global deceleration
        
        try:
            with open('motion.json', 'r') as jsonfile:
                motion_json = json.load(jsonfile)

                axis_no = motion_json['motor']['axis_no']
                max_speed = motion_json['motor']['max_speed']
                neg_limit = motion_json['motor']['neg_limit']
                pos_limit = motion_json['motor']['pos_limit']
                origin_type = motion_json['motor']['origin_type']
                speed_origin = motion_json['motor']['speed_origin']
                motor_type = motion_json['motor']['motor_type']
                resolution = motion_json['motor']['resolution']
                com_port = motion_json['config']['port_num']
                acceleration = motion_json['default']['acceleration']
                deceleration = motion_json['default']['deceleration']
        
        except KeyError as error:
            print('KeyError', error)

        except Exception as error:
            print('Exception', error)
