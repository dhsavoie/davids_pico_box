from sh1106 import *
from machine import Pin, I2C
import framebuf

# NOTES
"""
(0,0) is the top left corner of the display.

The display is 128x64 pixels.







"""

def display_wrapped_text(message):
    display.fill(0)  # Clear screen
    max_chars_per_line = 16  # Each line fits 16 characters
    max_lines = 8  # The screen has 8 lines total

    message_split = message.split()
    lines = [""]
    current_line = 0
    for word in message_split:
        if (len(word) + len(lines[current_line])) <= max_chars_per_line:
            lines[current_line] += word + " "
        else:
            # print(f"New line! Finished line is: {lines[current_line]}")
            # display.text(lines[current_line], 0, current_line * 8, 1)
            current_line += 1
            if current_line < max_lines:
                lines.append(word + " ")
            else:
                break
    for line in range(len(lines)):
        display.text(lines[line], 0, line * 8, 1)


    # for i in range(min(len(message) // max_chars_per_line + 1, max_lines)):
    #     start = i * max_chars_per_line
    #     end = start + max_chars_per_line
    #     display.text(message[start:end], 0, i * 8, 1)

    display.show()  # Update the screen

i2c = I2C(1, sda=Pin(18), scl=Pin(19), freq=400000)
print(i2c.scan())
display = SH1106_I2C(128, 64, i2c, addr=0x3C, rotate=180)

# Clear the screen
display.fill(0)

# # Write "Hello, World!" at position (0, 0)
# display.text("Hello, World!", 10, 10, 1)

# # Show the text on the display
# display.show()

# display.hline(0, 20, 128, 2)  # Draw a horizontal line at y=20
# display.vline(64, 0, 64, 2)  # Draw a vertical line at x=64
# display.show()


# # 16x16 pixel smiley face bitmap (1-bit monochrome)
# smiley = bytearray([
#     0b00111100, 0b00111100,  
#     0b01000010, 0b01000010,  
#     0b10100101, 0b10100101,  
#     0b10000001, 0b10000001,  
#     0b10100101, 0b10100101,  
#     0b10011001, 0b10011001,  
#     0b01000010, 0b01000010,  
#     0b00111100, 0b00111100
# ])

# # Create a frame buffer
# fb = framebuf.FrameBuffer(smiley, 16, 8, framebuf.MONO_HLSB)

# # Clear screen and draw the image at (50,20)
# display.fill(0)
# display.blit(fb, 50, 20)
# display.show()

# 16x16 pixel heart bitmap (1-bit monochrome)
full_heart = bytearray([
    0b00001110, 0b01110000,
    0b00011111, 0b11111000,
    0b00111111, 0b11111100,
    0b01111111, 0b11111110,
    0b01111111, 0b11111110,
    0b01111111, 0b11111110,
    0b00111111, 0b11111100,
    0b00011111, 0b11111000,
    0b00001111, 0b11110000,
    0b00000111, 0b11100000,
    0b00000011, 0b11000000,
    0b00000001, 0b10000000,
    0b00000000, 0b00000000,
])

heart = bytearray([
    0b00001110, 0b01110000,
    0b00010001, 0b10001000,
    0b00100000, 0b00000100,
    0b01000000, 0b00000010,
    0b01000000, 0b00000010,
    0b01000000, 0b00000010,
    0b00100000, 0b00000100,
    0b00010000, 0b00001000,
    0b00001000, 0b00010000,
    0b00000100, 0b00100000,
    0b00000010, 0b01000000,
    0b00000001, 0b10000000,
])

display_wrapped_text("Good morning")
# Create a 16x13 framebuffer for the heart
fb = framebuf.FrameBuffer(heart, 16, 12, framebuf.MONO_HLSB)

# Clear the display
# display.fill(0)

# Draw the heart at (56, 20) (centered on a 128x64 screen)
display.blit(fb, 128-15, 64-12)

# Update display
display.show()

big_heart = bytearray([
    0b00001111, 0b11110000, 0b00001111, 0b11110000,
    0b00010000, 0b00001000, 0b00010000, 0b00001000,
    0b00100000, 0b00000100, 0b00100000, 0b00000100,
    0b01000000, 0b00000010, 0b01000000, 0b00000010,
    0b01000000, 0b00000001, 0b10000000, 0b00000010,
    0b01000000, 0b00000000, 0b00000000, 0b00000010,
    0b01000000, 0b00000000, 0b00000000, 0b00000010,
    0b01000000, 0b00000000, 0b00000000, 0b00000010,
    0b00100000, 0b00000000, 0b00000000, 0b00000100,
    0b00010000, 0b00000000, 0b00000000, 0b00001000,
    0b00001000, 0b00000000, 0b00000000, 0b00010000,
    0b00000100, 0b00000000, 0b00000000, 0b00100000,
    0b00000010, 0b00000000, 0b00000000, 0b01000000,
    0b00000001, 0b00000000, 0b00000000, 0b10000000,
    0b00000000, 0b10000000, 0b00000001, 0b00000000,
    0b00000000, 0b01000000, 0b00000010, 0b00000000,
    0b00000000, 0b00100000, 0b00000100, 0b00000000,
    0b00000000, 0b00010000, 0b00001000, 0b00000000,
    0b00000000, 0b00001000, 0b00010000, 0b00000000,
    0b00000000, 0b00000100, 0b00100000, 0b00000000,
    0b00000000, 0b00000010, 0b01000000, 0b00000000,
    0b00000000, 0b00000001, 0b10000000, 0b00000000,




])

fb = framebuf.FrameBuffer(big_heart, 32, 22, framebuf.MONO_HLSB)

# Clear the display
display.fill(0)

# Draw the heart at (56, 20) (centered on a 128x64 screen)
display.blit(fb, 0, 0)

# Update display
display.show()