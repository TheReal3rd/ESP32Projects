from machine import Pin, PWM

#Found somewhere on the internet. I can't remember where.

class Servo:
    __servo_pwm_freq = 50
    __min_u10_duty = 26 - 0
    __max_u10_duty = 123- 0
    min_angle = 0
    max_angle = 180
    current_angle = 0.001


    def __init__(self, pin, maxAngle= 180, minAngle= 0):
        self.max_angle = maxAngle
        self.min_angle = minAngle
        self.__initialise(pin)


    def update_settings(self, servo_pwm_freq, min_u10_duty, max_u10_duty, min_angle, max_angle, pin):
        self.__servo_pwm_freq = servo_pwm_freq
        self.__min_u10_duty = min_u10_duty
        self.__max_u10_duty = max_u10_duty
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.__initialise(pin)


    def move(self, angle):

        angle = round(angle, 2)
 
        if angle == self.current_angle:
            return
        self.current_angle = angle

        duty_u10 = self.__angle_to_u10_duty(angle)
        self.__motor.duty(duty_u10)

    def __angle_to_u10_duty(self, angle):
        return int((angle - self.min_angle) * self.__angle_conversion_factor) + self.__min_u10_duty


    def __initialise(self, pin):
        self.current_angle = -0.001
        self.__angle_conversion_factor = (self.__max_u10_duty - self.__min_u10_duty) / (self.max_angle - self.min_angle)
        self.__motor = PWM(Pin(pin))
        self.__motor.freq(self.__servo_pwm_freq)


