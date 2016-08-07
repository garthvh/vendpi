# VendPi Raspberry Pi Vending Machine
# Author: Garth Vander Houwen (gartvh@yahoo.com)
#
# Hardware: Raspberry Pi B+, 12 TM1803 RGB LEDs, Nokia 5110 Screen, 4 16mm Push Buttons, 4 Parallax Continuous Rotation Servos
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

# Push Button Pin Assignments
PUSH_BUTTON_A = 6  # GPIO pin for Push Button A (other end to GND)
PUSH_BUTTON_B = 13 # GPIO pin for Push Button B (other end to GND)
PUSH_BUTTON_C = 19 # GPIO pin for Push Button C (other end to GND)
PUSH_BUTTON_D = 26 # GPIO pin for Push Button D (other end to GND)

# Define functions to change the screen
def changeScreenText(draw, font, line1, line2, line3, line4):
    """ Adjust the text displayed on the screen ~15 Characters per line """
    draw.text((0, 0),  line1, font=font)
    draw.text((0, 12), line2, font=font)
    draw.text((0, 24), line3, font=font)
    draw.text((0, 36), line4, font=font)

# Define functions which animate LEDs in various ways.
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

    # Stuff You Do Once
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
    
    # Start the Nokia Screen using Hardware SPI:
    disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
    # Initialize library.
    disp.begin(contrast=40)
    # Load default font.
    font = ImageFont.load_default()
    # Create Empty Image Object
    image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
    # Create a drawing object
    draw = ImageDraw.Draw(image)
    # Clear Screen
    draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
    # Load Initial Text
    changeScreenText(draw, font, "  Alexa & RPI ", "Trivia Vending", "   Built By   ", " Garth & Jason")
    # Display Image
    disp.image(image)
    disp.display()
    # Flash Some Colors on the LEDs
    colorWipe(strip, Color(255, 0, 0))      # Red wipe
    colorWipe(strip, Color(255, 255, 255))  # White wipe
    colorWipe(strip, Color(0, 255, 0))      # Blue wipe
    colorWipe(strip, Color(0, 0, 255))      # Green wipe
    
    
    print ('Garth and Jason''s Super Fancy ')
    print ('Alexa Powered Pi Vending App is Running')
    print ('Press Ctrl-C to quit.')
    while True:
        # Flip back to white lights after the button action has run
        colorWipe(strip, Color(255, 255, 255))   # White wipe
        
        image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
        # Load Initial Text
        changeScreenText(draw, font, "  Alexa & RPI ", "Trivia Vending", "   Built By   ", " Garth & Jason")
        # Display Image
        disp.image(image)
        disp.display()
        # Button States        
        button_a_state = GPIO.input(PUSH_BUTTON_A)
        button_b_state = GPIO.input(PUSH_BUTTON_B)
        button_c_state = GPIO.input(PUSH_BUTTON_C)
        button_d_state = GPIO.input(PUSH_BUTTON_D)
        # A Button
        if button_a_state == False:
            print('Button A Pressed')
            # Draw Empty rectangle on the screen
            draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
            # Write some text
            changeScreenText(draw, font, "  You Pressed ", "   Button A   ", "   Enjoy the  ", "     Cylon    ")
            # Display Image
            disp.image(image)
            disp.display()
            for t in range (0, 10,1):
                nightrider(strip, Color(255,0,0), 65)
            for t in range (0, 10,1):
                nightrider(strip, Color(0,0,255), 65)
            time.sleep(0.2)
        # B Button    
        if button_b_state == False:
            print('Button B Pressed')
            # Draw Empty rectangle on the screen
            draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
            # Button Box Size Variables
            box_width = ((LCD.LCDWIDTH / 2) -4)
            box_height = ((LCD.LCDHEIGHT / 2) -4)
            # Write some text
            changeScreenText(draw, font, "  You Pressed ", "   Button B   ", "   Enjoy the  ", "   Rainbows    ")
            # Display Image
            disp.image(image)
            disp.display()
            # Draw Button Images
            # A Button 2,2,22,22
            #draw.rectangle((2,2, box_width, box_height), outline=0, fill=255)
            #print(box_width)
            #print(box_height)
            #print(LCD.LCDWIDTH)
            #print(LCD.LCDHEIGHT)

            rainbow(strip)
            time.sleep(0.2)
            
        if button_c_state == False:
            print('Button C Pressed')
            # Draw Empty rectangle on the screen
            draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
            # Write some text
            changeScreenText(draw, font, "  You Pressed ", "   Button C   ", "   Enjoy the  ", " Rainbow Cycle  ")
            # Display Image
            disp.image(image)
            disp.display()
            rainbow(strip)
            rainbowCycle(strip)
            time.sleep(0.2)
            
        if button_d_state == False:
            print('Button D Pressed')
            # Draw Empty rectangle on the screen
            draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
            # Write some text
            changeScreenText(draw, font, "  You Pressed ", "   Button D   ", "Enjoy the RBW", " Theater Chase  ")
            # Display Image
            disp.image(image)
            disp.display()
            # Theater chase animations.
            theaterChase(strip, Color(127, 127, 127))  # White theater chase
            theaterChase(strip, Color(127,   0,   0))  # Red theater chase
            theaterChase(strip, Color(  0,   0, 127))  # Blue theater chase
            theaterChaseRainbow(strip)
            time.sleep(0.2)