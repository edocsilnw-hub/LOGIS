import queue
import numpy as np
import sounddevice as sd

speech_queue = queue.Queue()

# ==========================================================
# VOX-CASTER SYSTEM
# ==========================================================

try:
    from voicebox.tts import ESpeakNG, ESpeakConfig
    from voicebox.effects import Vocoder, Normalize
    
    # Engine generates at 22,050 Hz
    tts_engine = ESpeakNG(config=ESpeakConfig(voice='en-us', speed=145))
    effects = [Vocoder.build(), Normalize()]
    print("--- VOX-CASTER ENGINE ARMED (22kHz Source) ---")
except Exception as e:
    print(f"--- VOX-CASTER ERROR: {e} ---")
    tts_engine = None

def vox_worker():
    """Worker thread that handles resampling and hardware injection."""
    print("--- VOX-CASTER DAEMON ONLINE (Target: 48kHz / Device 3) ---")
    while True:
        text = speech_queue.get()
        if text is None: break  # Shutdown signal
        
        try:
            # A. Generate raw 22050Hz audio
            audio = tts_engine.get_speech(text)
            for effect in effects:
                audio = effect.apply(audio)

            # B. LINEAR RESAMPLING (22050 -> 48000)
            current_data = audio.sample_rate_array
            old_samplerate = audio.sample_rate # 22050
            new_samplerate = 48000
            
            duration = len(current_data) / old_samplerate
            time_old = np.linspace(0, duration, len(current_data))
            time_new = np.linspace(0, duration, int(len(current_data) * (new_samplerate / old_samplerate)))
            
            resampled_data = np.interp(time_new, time_old, current_data)

            # C. Hardware Injection to Arctis Nova 7 (Device 3)
            sd.play(resampled_data, new_samplerate)
            sd.wait() 
            
        except Exception as e:
            print(f"[VOX ERROR] {e}")
        
        speech_queue.task_done()



def logis_speak(text):
    """Adds a message to the queue to prevent thread collisions."""
    if not tts_engine:
        return
        
    # Scrubbing artifacts
    clean_text = text.replace("*", "").replace("#", "").replace("`", "").replace("_", "")
    if clean_text.strip():
        speech_queue.put(clean_text)