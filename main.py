import customtkinter as ctk
from modules.tts import speak
from modules.asl import ASLTab
from modules.braille_receiver import BrailleTab


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Assistive Communication System")
        self.geometry("1100x720")
        self.resizable(True, True)
        self.bind("<F11>", lambda e: self.attributes(
            "-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)   # tabs stretch
        self.rowconfigure(1, weight=0)   # sentence box fixed at bottom

        # =============================================================
        # Tabs — ASL and Braille each write into the shared sentence box
        # =============================================================
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=16, pady=(16, 0))
        self.tabview.add("ASL Signing")
        self.tabview.add("Braille Input")

        # =============================================================
        # Shared sentence box — lives in main, passed to both modules
        # =============================================================
        bottom = ctk.CTkFrame(self, corner_radius=12)
        bottom.grid(row=1, column=0, sticky="ew", padx=16, pady=16)
        bottom.columnconfigure(0, weight=1)

        ctk.CTkLabel(bottom, text="Sentence",
                    font=ctk.CTkFont(size=12),
                    text_color="gray").grid(
                    row=0, column=0, sticky="w", padx=16, pady=(8, 0))

        self.sentence_box = ctk.CTkTextbox(
            bottom, height=150, font=ctk.CTkFont(size=16), wrap="word")
        self.sentence_box.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 8))

        btn_row = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        btn_row.columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_row, text="🔊  Speak & Clear",
                    command=self._speak_and_clear,
                    height=40, fg_color="#1565c0", hover_color="#1976d2",
                    font=ctk.CTkFont(size=14, weight="bold")).grid(
                    row=0, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkButton(btn_row, text="Clear",
                    command=self._clear_box,
                    height=40, fg_color="#37474f", hover_color="#455a64",
                    font=ctk.CTkFont(size=14)).grid(
                    row=0, column=1, padx=(4, 0), sticky="ew")

        # =============================================================
        # Wire up modules — pass the shared sentence_box into each
        # =============================================================
        self.asl     = ASLTab(self.tabview.tab("ASL Signing"),
                            self.sentence_box)
        self.braille = BrailleTab(self.tabview.tab("Braille Input"),
                                self.sentence_box)

    def _speak_and_clear(self):
        text = self.sentence_box.get("1.0", "end-1c").strip()
        speak(text)
        self.sentence_box.delete("1.0", "end")

    def _clear_box(self):
        self.sentence_box.delete("1.0", "end")
        self.asl.clear_asl()

    def on_close(self):
        self.asl.stop(closing=True)
        self.braille.disconnect()
        self.after(150, self.destroy)


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()