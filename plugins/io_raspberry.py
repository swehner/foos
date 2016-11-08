import time
import logging
import ctypes
import time
import RPi.GPIO as GPIO
from .io_base import IOBase
import foos.config as config

logger = logging.getLogger(__name__)

#The button should be connected to GND
class Button:
    def __init__(self, bus, pin_number, name, debounce_time_ms = 20):
        self.pin = pin_number
        self.name = name
        self.bus = bus
        if self.pin:
            GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
            GPIO.add_event_detect(self.pin, GPIO.BOTH, callback = self.button_changed, bouncetime = debounce_time_ms)
            self.button_state = GPIO.input(self.pin)
        else:
            logger.warn("Cannot init button {0}, pin not specified".format(self.name))
        
    def button_changed(self, channel):
        input = GPIO.input(self.pin)
        if input == self.button_state:
            return;
        self.button_state = input
        logger.info("{0} button changed to {1}!".format(self.name, input));
        event_data = {'source': 'rpi', 'btn': self.name, 'state': 'up' if input else 'down'}
        if event_data:
            self.bus.notify('button_event', event_data)

    def __del__(self):
        if self.pin:
            GPIO.remove_event_detect(self.pin)

class GoalDetector:
    def __init__(self, bus, pin_number, team):
        self.bus = bus
        self.pin = pin_number
        self.team = team
        if self.pin:
            #GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
            GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.on_goal, bouncetime=10)
        else:
            logger.warn("Cannot init GoalDetector {0}, pin not specified".format(self.team))
    def __del__(self):
        if self.pin:
            GPIO.remove_event_detect(self.pin)
            
    def on_goal(self, channel):
        logger.info("Goal {}!".format(self.team))
        self.bus.notify('goal_event', {'source': 'rpi', 'team': self.team})

class IRBarrierPwmGenerator:
    def __init__(self, pwm_pin):
        self.pin = pwm_pin
        self.wpi = ctypes.CDLL("libwiringPi.so")
        
        self.wpi.wiringPiSetupGpio() # Initialize wiringPi -- using Broadcom pin numbers

        PWM_OUTPUT=2
        PWM_MODE_MS=0

        self.wpi.pinMode(self.pin, PWM_OUTPUT) # Set PWM LED as PWM output
            
        # Raspberry base PWM frequency: 19,200,000 Hz
        # Resulted frequency: base freq / 101 / 5 = 38.019 kHz
        # Signal duty cycle = 3/5 = ~60%
        self.wpi.pwmSetMode(PWM_MODE_MS)
        self.wpi.pwmSetClock(101)
        self.wpi.pwmSetRange(5)
        self.wpi.pwmWrite(self.pin, 2)
        logger.info("IR PWM started")
        
    def __del__(self):
        self.wpi.pwmWrite(self.pin, 0);
        logger.info("IR PWM stopped")
        
class Plugin(IOBase):
    def __init__(self, bus):
        GPIO.setmode(GPIO.BOARD)
        
        self.goal_pin_black = config.io_raspberry_pins["irbarrier_team_black"]
        self.goal_pin_yellow = config.io_raspberry_pins["irbarrier_team_yellow"]

        self.ok_button_pin = config.io_raspberry_pins["ok_button"]
        self.ir_barrier_pwm_pin = config.io_raspberry_pins["irbarrier_pwm"]

        self.yellow_plus_pin = config.io_raspberry_pins["yellow_plus"]
        self.yellow_minus_pin = config.io_raspberry_pins["yellow_minus"]

        self.black_plus_pin = config.io_raspberry_pins["black_plus"]
        self.black_minus_pin = config.io_raspberry_pins["black_minus"]
        
        self.ir_barrier_pwm = IRBarrierPwmGenerator(self.ir_barrier_pwm_pin)

        time.sleep(0.5)   # let the PWM really start before starting detectors
            
        self.goal_detector_black = GoalDetector(bus, self.goal_pin_black, "black")
        self.goal_detector_yellow = GoalDetector(bus, self.goal_pin_yellow, "yellow")

        self.yellow_plus_button = Button(bus, self.yellow_plus_pin, 'yellow_plus')
        self.yellow_minus_button = Button(bus, self.yellow_minus_pin, 'yellow_minus')
        
        self.black_plus_button = Button(bus, self.black_plus_pin, 'black_plus')
        self.black_minus_button = Button(bus, self.black_minus_pin, 'black_minus')

        self.ok_button = Button(bus, self.ok_button_pin, 'ok')
            
        super().__init__(bus)

    def reader_thread(self):
        while True:
            #Do nothing for now
            time.sleep(1)
            
    def writer_thread(self):
        while True:
            line = self.write_queue.get()
            #Do nothing for now
            time.sleep(1)

        
