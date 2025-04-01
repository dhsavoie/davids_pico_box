def display_wrapped_text(display, message):
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
            current_line += 1
            if current_line < max_lines:
                lines.append(word + " ")
            else:
                break
    for line in range(len(lines)):
        display.text(lines[line], 0, line * 8, 1)

    display.show()