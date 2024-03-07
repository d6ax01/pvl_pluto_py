from __future__ import with_statement
from waiting import wait
import os
import sys
import time
import python_ezimotor_api
import motion
import winsys

# motor ===============================================
gMotor = -1
# =====================================================

def motor_open(want_home_position_at_start):
    motor = python_ezimotor_api.EziMotor(motion.com_port)
    if motor.IsConnected() == False:
        sys.exit('Motor is not connected')
    motor.SetServoParam(motion.axis_no, motion.max_speed, motion.neg_limit, motion.pos_limit, motion.origin_type,
                        motion.speed_origin, motion.motor_type, motion.resolution)
    motor.SetMoveProfile(motion.axis_no, 150, motion.acceleration, motion.deceleration)

    # Alarm Reset
    if motor.IsAlarm(motion.axis_no) == True:
        motor.AlarmReset(motion.axis_no)
        time.sleep(0.5)

    # Servo On
    if motor.ServoOn(motion.axis_no, True) == False:
        sys.exit('Motor is not ServoOn. Please contact s/w engineer.')

    time.sleep(0.5)

    if motor.IsServoOn(motion.axis_no) == False:
        motor.ServoOn(motion.axis_no, True)
        time.sleep(0.5)

    return motor
        
def motor_close(motor):
    # Close motor
    ##motor.MoveAbsolute(motion.axis_no, 50)
    motor.ServoOn(motion.axis_no, False)
    motor.Close()

def is_motor_ready(motor, axis_no):
    if motor.IsMotionDone(axis_no) == False:
        return True
    return False

def motor_clear():
    global gMotor
    gMotor.ServoOn(motion.axis_no, False)
    gMotor.Close()
    want_home_position_at_start = True
    gMotor = motor_open(want_home_position_at_start)

def motor_move(distance, motion_abs):
    if gMotor == -1:
        raise SystemError

    print(f'Motor move {distance}mm')
    if gMotor.ABSMove_Chk(motion.axis_no, motion_abs) == False:
        print(f' => Oops: Motor could not move {distance}')
        motor_clear()

    gMotor.MoveAbsolute(motion.axis_no, motion_abs)
    wait(lambda: is_motor_ready(gMotor, motion.axis_no), timeout_seconds=120, waiting_for="Motor move to be ready")
    time.sleep(1)
    # input("Press Enter to continue...")


if __name__ == "__main__" :

    if not winsys.is_admin():
        print('[ERROR] You should run this program with administrator')
        sys.exit(-1)

    # 모터 초기화 *****************************************************************************************************
    # motor create
    want_home_position_at_start = True
    motion_obj = motion.Motion()
    gMotor = motor_open(want_home_position_at_start)
    if (want_home_position_at_start):
        # Move motor at home position
        # motor.ServoHomeStart(motion.axis_no)
        motor_move(distance=500, motion_abs=500)  # 2022_11_30, 지그교체
        #motor_move(distance=300, motion_abs=195.5)  # 2022_11_30, 지그교체
        time.sleep(0.5)

    motor_close(gMotor)
    print('Finish')