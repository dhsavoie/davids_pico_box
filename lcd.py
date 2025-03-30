from machine import Pin
from time import sleep

class LCD:
    def __init__(self, rs, e, d4, d5, d6, d7):
        self.rs = Pin(rs, Pin.OUT)
        self.e = Pin(e, Pin.OUT)
        self.data_pins = [Pin(d4, Pin.OUT), Pin(d5, Pin.OUT), Pin(d6, Pin.OUT), Pin(d7, Pin.OUT)]
        self.initialize()

    def pulse_enable(self):
        """pulse the enable pin to send data """
        self.e.value(1)
        sleep(0.0005)
        self.e.value(0)
        sleep(0.0005)

    def send_nibble(self, nibble):
        """ send 4 bit data to the LCD """
        for i in range(4):
            self.data_pins[i].value((nibble >> i) & 1)
        self.pulse_enable()

    def send_byte(self, byte, is_command=True):
        """ send a full byte in 2 nibbles """
        self.rs.value(0 if is_command else 1) # 0 = command, 1 = data
        self.send_nibble(byte >> 4) # send high nibble
        self.send_nibble(byte & 0x0F) # send low nibble

    def initialize(self):
        """ initialize the LCD in 4 bit mode """
        sleep(0.05) # wait for LCD to power up
        self.send_nibble(0x03) # force 8 bit mode
        sleep(0.005)
        self.send_nibble(0x03)
        sleep(0.001)
        self.send_nibble(0x03)
        self.send_nibble(0x02) # set to 4 bit mode

        # function set: 4 bit mode, 2 lines, 5x8 dots
        self.send_byte(0x28)
        # display on, cursor off, blink off
        self.send_byte(0x0C)
        # clear display
        self.send_byte(0x01)
        sleep(0.002)
        # entry mode set: increment, no shift
        self.send_byte(0x06)

    def clear(self):
        """ clear the display """
        self.send_byte(0x01)
        sleep(0.002)

    def write(self, text):
        """ write a string to the display """
        for char in text:
            self.send_byte(ord(char), is_command=False)

    def scroll_left(self, delay=0.3, steps=16):
        """Scroll text left across the display."""
        for _ in range(steps):
            self.send_byte(0x18)  # Shift display left
            sleep(delay)

    def scroll_right(self, delay=0.3, steps=16):
        """Scroll text right across the display."""
        for _ in range(steps):
            self.send_byte(0x1C)  # Shift display right
            sleep(delay)

# RS is purple- gp13
# enable is green- gp12
# d4 11, d5 10, d6 9, d7 8 
