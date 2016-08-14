# VendPi Raspberry Pi Vending Machine
# Authors: Garth Vander Houwen (@garthvh), Jason Widrig (@jasonwidrig)
#
# Hardware: Venduino Laser Cut Case http://www.retrobuiltgames.com/diy-kits-shop/venduino/
#           Raspberry Pi B+, 
#           12 TM1803 RGB LEDs
#           Nokia 5110 Screen 84x48
#           4 16mm Red Push Buttons
#           4 Parallax Continuous Rotation Servos
#           16 Channel 12 bit pwm Servo Motor Driver i2c Module Board
#           Step-down Voltage Regulator 
#
# Built with with code from 
# TM1803 LEDs https://github.com/jgarff/rpi_ws281x
#
#
import time

# NeoPixel for LEDs
from neopixel import *

# Nokia 5110 Screen
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

# GPIO For Push Buttons
import RPi.GPIO as GPIO

# Import the PCA9685 module for servos
import Adafruit_PCA9685

# Configure servo pulse length
servo_length = 270  # Min pulse length out of 4096

# LED strip configuration:
LED_COUNT      = 12      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM).
LED_FREQ_HZ    = 400000  # LED signal frequency in hertz 400khz for the TM1803
LED_DMA        = 5       # DMA channel to use for generating signal 5 for the TM1803
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Nokia Screen Configuration
# Hardware SPI config:
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0
# LCD Size Variables
LCD_WIDTH = 84;
LCD_HEIGHT = 48;

# Push Button Pin Assignments
PUSH_BUTTON_A = 6  # GPIO pin for Push Button A (other end to GND)
PUSH_BUTTON_B = 13 # GPIO pin for Push Button B (other end to GND)
PUSH_BUTTON_C = 19 # GPIO pin for Push Button C (other end to GND)
PUSH_BUTTON_D = 26 # GPIO pin for Push Button D (other end to GND)
PUSH_BUTTON_HALT = 16 # GPIO pin for Push Button D (other end to GND)


# Shutdown Function
def shutdown():
    command = "/usr/bin/sudo /sbin/shutdown -h now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print output

# Define functions to change the display on screen
def changeScreenText(draw, font, line1, line2, line3, line4):
    """ Adjust the text displayed on the Nokia 5110 screen ~12 Characters per line """
    # Draw Empty rectangle on the screen
    draw.rectangle((0, 0, LCD_WIDTH, LCD_HEIGHT), outline=255, fill=255)
    # Write the text out for each line
    draw.text((0, 0),  line1, font=font)
    draw.text((0, 12), line2, font=font)
    draw.text((0, 24), line3, font=font)
    draw.text((0, 36), line4, font=font)
    # Display Image
    disp.image(image)
    disp.display()

# Define functions to animate TM1803 LEDs
def colorWipe(strip, color, wait_ms=50):
	"""Wipe color across display a pixel at a time."""
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, color)
		strip.show()
		time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):
	"""Movie theater light style chaser animation."""
	for j in range(iterations):
		for q in range(3):
			for i in range(0, strip.numPixels(), 3):
				strip.setPixelColor(i+q, color)
			strip.show()
			time.sleep(wait_ms/1000.0)
			for i in range(0, strip.numPixels(), 3):
				strip.setPixelColor(i+q, 0)

def wheel(pos):
	"""Generate rainbow colors across 0-255 positions."""
	if pos < 85:
		return Color(pos * 3, 255 - pos * 3, 0)
	elif pos < 170:
		pos -= 85
		return Color(255 - pos * 3, 0, pos * 3)
	else:
		pos -= 170
		return Color(0, pos * 3, 255 - pos * 3)
        
def dimColor (color):
    """ Color is an 32-bit int that merges the values into one """
    return (((color&0xff0000)/3)&0xff0000) + (((color&0x00ff00)/3)&0x00ff00) + (((color&0x0000ff)/3)&0x0000ff)

def rainbow(strip, wait_ms=20, iterations=1):
	"""Draw rainbow that fades across all pixels at once."""
	for j in range(256*iterations):
		for i in range(strip.numPixels()):
			strip.setPixelColor(i, wheel((i+j) & 255))
		strip.show()
		time.sleep(wait_ms/1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):
	"""Draw rainbow that uniformly distributes itself across all pixels."""
	for j in range(256*iterations):
		for i in range(strip.numPixels()):
			strip.setPixelColor(i, wheel(((i * 256 / strip.numPixels()) + j) & 255))
		strip.show()
		time.sleep(wait_ms/1000.0)

def theaterChaseRainbow(strip, wait_ms=50):
	"""Rainbow movie theater light style chaser animation."""
	for j in range(256):
		for q in range(3):
			for i in range(0, strip.numPixels(), 3):
				strip.setPixelColor(i+q, wheel((i+j) % 255))
			strip.show()
			time.sleep(wait_ms/1000.0)
			for i in range(0, strip.numPixels(), 3):
				strip.setPixelColor(i+q, 0)
                
def nightrider(stick, color, wait_ms=70):
    """ kitt / cylon scanner """
    for i in range(stick.numPixels()):
            stick.setPixelColor(i,color)
            stick.setPixelColor(i-1,dimColor(color))
            stick.show()
            time.sleep(wait_ms/1000.0)
            stick.setPixelColor(i,0)
            stick.setPixelColor(i-1,0)
    # reverse the direction
    for i in xrange((stick.numPixels())-1,-1,-1):
            stick.setPixelColor(i,color)
            stick.setPixelColor(i+1,dimColor(color))
            stick.show()
            time.sleep(wait_ms/1000.0)
            stick.setPixelColor(i,0)
            stick.setPixelColor(i+1,0)


# Main program logic follows:
if __name__ == '__main__':

    ###  Stuff You Do Once  ###
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    # Set GPIO mode
    GPIO.setmode(GPIO.BCM)
    # Setup with Pull Up for Push Button Pins
    GPIO.setup(PUSH_BUTTON_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PUSH_BUTTON_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PUSH_BUTTON_C, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PUSH_BUTTON_D, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PUSH_BUTTON_HALT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Set Width and Height Variables
    LCD_WIDTH = LCD.LCDWIDTH
    LCD_HEIGHT = LCD.LCDHEIGHT
    # Start the Nokia Screen using Hardware SPI:
    disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
    # Initialize library.
    disp.begin(contrast=45)
    # Load a tt font find more fonts at: http://www.dafont.com/bitmap.php	
    # ImageFont.load_default()
    font = ImageFont.truetype('fonts/DroidSansMono.ttf', 12) 
    # Create Empty Image Object
    image = Image.new('1', (LCD_WIDTH, LCD_HEIGHT))
    # Create a drawing object
    draw = ImageDraw.Draw(image)
    # Load Initial Text
    changeScreenText(draw, font, " ALEXA & PI", "TRIVIA SKILL", "   VENDING", "   MACHINE")
    # Flash Some Colors on the LEDs
    colorWipe(strip, Color(255, 0, 0))      # Red wipe
    colorWipe(strip, Color(255, 255, 255))  # White wipe
    colorWipe(strip, Color(0, 255, 0))      # Blue wipe
    colorWipe(strip, Color(0, 0, 255))      # Green wipe
    # Print Some text and button pushs to the console
    print ('Garth and Jason made this super fancy ')
    print ('Alexa Powered Pi Vending App that is running')
    print ('Press Ctrl-C to quit.')
    # Initialise the PCA9685 using the default address (0x40) and I2C bus for the PI2.
    pwm = Adafruit_PCA9685.PCA9685(address=0x40, busnum=1)
    # Set frequency to 60hz, good for servos.
    pwm.set_pwm_freq(60)
    # Loop
    while True:
        # Flip back to white lights after the button action has run
        colorWipe(strip, Color(255, 255, 255))   # White wipe
        
        # Button States        
        button_a_state = GPIO.input(PUSH_BUTTON_A)
        button_b_state = GPIO.input(PUSH_BUTTON_B)
        button_c_state = GPIO.input(PUSH_BUTTON_C)
        button_d_state = GPIO.input(PUSH_BUTTON_D)
        button_halt_state = GPIO.input(PUSH_BUTTON_HALT)
        # A Button
        if button_a_state == False:
            print('Button A Pressed')
            # Write some text
            changeScreenText(draw, font, "YOU PRESSED", "BUTTON A", "ENJOY THE", "CYLON")
            # Night Rider / Cylon
            for t in range (0, 10,1):
                nightrider(strip, Color(255,0,0), 65)
            for t in range (0, 10,1):
                nightrider(strip, Color(0,0,255), 65)
            time.sleep(0.2)
            # Move servo on channel O.
            pwm.set_pwm(0, 0, servo_length)
            time.sleep(1)
            # Stop moving servo
            pwm.set_pwm(0, 0, 0)
            # Load Initial Text after everything has run
            changeScreenText(draw, font, " ALEXA & PI", "TRIVIA SKILL", "  VENDING", "  MACHINE")
        # B Button    
        if button_b_state == False:
            print('Button B Pressed')
            # Button Box Size Variables
            box_width = ((LCD.LCDWIDTH / 2) -4)
            box_height = ((LCD.LCDHEIGHT / 2) -4)
            # Write some text
            changeScreenText(draw, font, "YOU PRESSED", "BUTTON B", "ENJOY THE", "RAINBOWS")
            # Draw Button Images
            # A Button 2,2,22,22
            #draw.rectangle((2,2, box_width, box_height), outline=0, fill=255)
            rainbow(strip)
            rainbowCycle(strip)
            theaterChaseRainbow(strip)
            time.sleep(0.2)
            # Move servo on channel 1.
            pwm.set_pwm(1, 0, servo_length)
            time.sleep(1)
            # Stop moving servo
            pwm.set_pwm(1, 0, 0)
            # Load Initial Text after everything has run
            changeScreenText(draw, font, " ALEXA & PI", "TRIVIA SKILL", "   VENDING", "   MACHINE")
        # C Button      
        if button_c_state == False:
            print('Button C Pressed')
            # Write some text
            changeScreenText(draw, font, "YOU PRESSED", "BUTTON C", "ENJOY THE", "RBW CYCLE")
            rainbow(strip)
            rainbowCycle(strip)
            time.sleep(0.2)
            # Move servo on channel 2.
            pwm.set_pwm(2, 0, servo_length)
            time.sleep(1)
            # Stop moving servo
            pwm.set_pwm(2, 0, 0)
            # Load Initial Text after everything has run
            changeScreenText(draw, font, " ALEXA & PI", "TRIVIA SKILL", "   VENDING", "   MACHINE")
        # D Button      
        if button_d_state == False:
            print('Button D Pressed')
            # Write some text
            changeScreenText(draw, font, "YOU PRESSED", "BUTTON D", "ENJOY THE RBW", "THEATER CHASE")
            # Theater chase animations.
            theaterChase(strip, Color(127,   0,   0))  # Red theater chase
            theaterChase(strip, Color(127, 127, 127))  # White theater chase
            theaterChase(strip, Color(  0,   0, 127))  # Blue theater chase
            theaterChaseRainbow(strip)
            time.sleep(0.2)
            # Move servo on channel 3.
            pwm.set_pwm(3, 0, servo_length)
            time.sleep(1)
            # Stop moving servo
            pwm.set_pwm(3, 0, 0)
            # Load Initial Text after everything has run
            changeScreenText(draw, font, " ALEXA & PI", "TRIVIA SKILL", "   VENDING", "   MACHINE")
            # Halt Button      
        if button_halt_state == False:
            print('Shutdown Button Pressed')
            # Write some text
            changeScreenText(draw, font, "YOU PRESSED", "BTN SHUTDOWN", "SHUTTING DOWN", "GOODBYE")
            shutdown()