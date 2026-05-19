import socket
import threading
import time
import paramiko
import customtkinter as ctk
from modules.tts import speak

# =================================================================================
# Config
# =================================================================================
PI_HOST = "10.1.104.93"
PI_PORT = 65433
PI_USER = "alex"
PI_PASS = "12345"
PI_CMD  = "sudo python3 Project/braille_parser.py"

BRAILLE_DECODER = {
    '100000': 'a', '110000': 'b', '100100': 'c', '100110': 'd',
    '100010': 'e', '110100': 'f', '110110': 'g', '110010': 'h',
    '010100': 'i', '010110': 'j', '101000': 'k', '111000': 'l',
    '101100': 'm', '101110': 'n', '101010': 'o', '111100': 'p',
    '111110': 'q', '111010': 'r', '011100': 's', '011110': 't',
    '101001': 'u', '111001': 'v', '010111': 'w', '101101': 'x',
    '101111': 'y', '101011': 'z', '010000': ',', '010011': '.',
    '000000': ' '
}
NUMBER_MAP = {
    'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5',
    'f': '6', 'g': '7', 'h': '8', 'i': '9', 'j': '0'
}

def _decode_braille(line):
    return ''.join(BRAILLE_DECODER.get(b, '?') for b in line.split())

# =================================================================================
# Braille Tab
# =================================================================================
class BrailleTab:
    def __init__(self, parent, sentence_box: ctk.CTkTextbox):
        self.sentence_box  = sentence_box
        self._socket       = None
        self._running      = False
        self._build_ui(parent)

    def _build_ui(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        # Centre column takes 25% of width on each side = buttons fill 50% centred
        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.place(relx=0.5, rely=0.5, anchor="center")

        self.status = ctk.CTkLabel(controls, text="● Disconnected",
                                font=ctk.CTkFont(size=12), text_color="#ef5350")
        self.status.pack(pady=(0, 16))

        btn_cfg = dict(width=300, height=48, font=ctk.CTkFont(size=14))

        ctk.CTkButton(controls, text="Connect to Pi",
                    command=self._connect,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    width=300, height=48).pack(pady=6)
        ctk.CTkButton(controls, text="Disconnect",
                    command=self.disconnect,
                    fg_color="#455a64", hover_color="#546e7a",
                      **btn_cfg).pack(pady=6)

    # ---- Controls ----
    def _connect(self):
        if self._running:
            return
        self._set_status("● Connecting...", "#ffa726")
        threading.Thread(target=self._ssh_then_listen, daemon=True).start()

    def disconnect(self):
        self._running = False
        if self._socket:
            try: self._socket.close()
            except Exception: pass
            self._socket = None
        try:
            self._set_status("● Disconnected", "#ef5350")
        except Exception:
            pass

    def _speak(self):
        text = self.sentence_box.get("1.0", "end-1c").strip()
        speak(text)
        self.sentence_box.delete("1.0", "end")

    # ---- SSH + socket ----
    def _ssh_then_listen(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=PI_HOST, username=PI_USER, password=PI_PASS)
            stdin, stdout, stderr = ssh.exec_command(PI_CMD, get_pty=True)
            stdin.write(PI_PASS + "\n")
            stdin.flush()
            time.sleep(2)
        except Exception as e:
            self._set_status(f"● SSH failed: {e}", "#ef5350")
            return

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((PI_HOST, PI_PORT))
            self._running = True
            self._set_status("● Connected", "#66bb6a")
            self._listen()
        except Exception as e:
            self._set_status(f"● Socket failed: {e}", "#ef5350")

    def _listen(self):
        buf          = ""
        capital_mode = False
        number_mode  = False
        try:
            while self._running:
                chunk = self._socket.recv(4096).decode("utf-8")
                if not chunk:
                    break
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith("ALERT:"):

                        prompt_text = line.replace("ALERT:", "").strip()
                        
                        if "Press" in prompt_text:
                            self._set_status(f"● {prompt_text}", "#ffa726")
                        else:
                            self._set_status(f"● {prompt_text}", "#66bb6a")
                        continue
                    
                    if line == "SPACE":
                        self._append(" ")
                    elif line == "ENTER":
                        self._speak()
                    elif line == "BACKSPACE":
                        self.sentence_box.after(0, self._backspace)
                    elif line == "000001":
                        capital_mode = True
                    elif line == "001111":
                        number_mode = True
                    else:
                        decoded = _decode_braille(line)
                        if number_mode:
                            decoded     = NUMBER_MAP.get(decoded, decoded)
                            number_mode = False
                        if capital_mode:
                            decoded      = decoded.upper()
                            capital_mode = False
                        self._append(decoded)
        except Exception:
            pass
        finally:
            self._running = False
            self._set_status("● Disconnected", "#ef5350")

    def _append(self, char):
        def _do():
            self.sentence_box.insert("end", char)
            self.sentence_box.see("end")
        self.sentence_box.after(0, _do)

    def _backspace(self):
        content = self.sentence_box.get("1.0", "end-1c")
        if content:
            self.sentence_box.delete("end-2c", "end-1c")

    def _set_status(self, text, color):
        try:
            self.status.after(0, lambda: self.status.configure(
                text=text, text_color=color))
        except Exception:
            pass