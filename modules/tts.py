import asyncio
import queue
import threading
import io
import time
import pygame
import edge_tts

pygame.mixer.init()
speech_queue = queue.Queue()

def tts_worker():
    while True:
        text = speech_queue.get()
        if text is None:
            break
        try:
            communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
            audio_buffer = io.BytesIO()
            async def _stream(buf=audio_buffer, comm=communicate):
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        buf.write(chunk["data"])
            asyncio.run(_stream())
            audio_buffer.seek(0)
            pygame.mixer.music.load(audio_buffer)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception as e:
            print("TTS ERROR:", e)

_tts_thread = threading.Thread(target=tts_worker, daemon=True)
_tts_thread.start()

def speak(text):
    if text and text.strip():
        speech_queue.put(text)