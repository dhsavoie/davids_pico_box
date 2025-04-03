import machine
import time
import micropython

# Button setup
button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)

# Shared flag
button_pressed_bool = False

# Debounce delay in milliseconds
debounce_delay = 500  # Adjust as needed

# Debounce delay
last_press_time = 0

# Interrupt handler
def button_pressed(pin):
    global button_pressed_bool, last_press_time

    # Debounce check (ignore triggers within 200ms)
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_press_time) > debounce_delay:
        last_press_time = current_time  # Update last press time
        button_pressed_bool = True
        # micropython.schedule(set_button_flag, 0)  # Schedule task outside of IRQ

# Function to safely update the flag
def set_button_flag(_):
    global button_pressed_bool
    button_pressed_bool = True

# Attach interrupt (detects when button goes from HIGH -> LOW)
button.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_pressed)

while True:
    if button_pressed_bool:
        print("Button pressed!")
        button_pressed_bool = False  # Reset flag
        time.sleep(0.1)  # Small delay to avoid over-processing
