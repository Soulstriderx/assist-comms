import socket
import select
from evdev import InputDevice, categorize, ecodes, list_devices

HOST = '0.0.0.0'
PORT = 65433

DOT_KEYS = ['KEY_2', 'KEY_3', 'KEY_4', 'KEY_5', 'KEY_6', 'KEY_7']

# mapping keys 2-7 to braille dots
# 2 5
# 3 6
# 4 7
DOT_ORDER = {
    'KEY_2': 0,
    'KEY_3': 1,
    'KEY_4': 2,
    'KEY_5': 3,
    'KEY_6': 4,
    'KEY_7': 5 
}

# Make a unique set of keys pressed
pressed = set()

def encode_braille_from(keys):
    bits = ['0'] * 6
    for key in keys:
        if key in DOT_ORDER:
            bits[DOT_ORDER[key]] = '1'
    return ''.join(bits)

def send(conn, msg):
    conn.sendall((msg + '\n').encode('utf-8'))

def find_keyboard(conn):
    devices = [InputDevice(path) for path in list_devices()]
    valid_devices = []

    for device in devices:
        caps = device.capabilities()
        if ecodes.EV_KEY not in caps:
            continue

        keys = caps[ecodes.EV_KEY]
        has_letters = (
            ecodes.KEY_A in keys and
            ecodes.KEY_Z in keys and
            ecodes.KEY_SPACE in keys
        )
        if has_letters:
            valid_devices.append(device)

    if not valid_devices:
        send(conn, "ALERT: No valid keyboards detected on Pi!")
        return None

    send(conn, "ALERT: Press any key on the target Pi keyboard...")
    print("\nSent keyboard prompt to PC...\n")

    while True:
        readable, _, _ = select.select(valid_devices, [], [])
        for device in readable:
            for event in device.read():
                if event.type == ecodes.EV_KEY:
                    send(conn, f"ALERT: Connected to {device.name}")
                    print(f"Selected keyboard: {device.name} ({device.path})")
                    return device

def main():
    print(f"Starting server on {HOST}:{PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()

        print("Waiting for PC to connect...")
        conn, addr = s.accept()
        print(f"PC connected from {addr}")

        with conn:
            keyboard = find_keyboard(conn)

            if not keyboard:
                print("No keyboard found")
                send(conn, "ERROR: No keyboard found")
                return

            print(f"Activating device: {keyboard.name}")
            keyboard.grab()

            try:
                for event in keyboard.read_loop():
                    if event.type != ecodes.EV_KEY:
                        continue

                    key_event = categorize(event)
                    key = key_event.keycode
                    print(key_event.keycode)

                    if key_event.keystate == key_event.key_down:
                        if key == 'KEY_8':
                            send(conn, "ENTER")
                            pressed.clear()
                            continue

                        if key == 'KEY_SPACE':
                            send(conn, "SPACE")
                            pressed.clear()
                            continue

                        if key == 'KEY_1':
                            send(conn, "BACKSPACE")
                            pressed.clear()
                            continue

                        if key in DOT_KEYS:
                            pressed.add(key)

                    elif key_event.keystate == key_event.key_up:
                        binary = encode_braille_from(pressed)

                        if binary != "000000":
                            send(conn, binary)
                            print("Sent:", binary, pressed)

                        pressed.clear()

            finally:
                keyboard.ungrab()


if __name__ == "__main__":
    main()
