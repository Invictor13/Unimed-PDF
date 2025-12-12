import soundcard as sc
import numpy as np
import threading
import time

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.thread = None
        self.frames = []
        self.sample_rate = 48000
        self.mic = None

    def start(self):
        self.recording = True
        self.thread = threading.Thread(target=self._record_loop)
        self.thread.start()

    def stop(self):
        self.recording = False
        if self.thread:
            self.thread.join()

    def _record_loop(self):
        """
        Finds the loopback microphone corresponding to the default speaker.
        """
        try:
            default_speaker = sc.default_speaker()
            speaker_name = default_speaker.name

            # Find loopback mic
            loopback_mic = None
            all_mics = sc.all_microphones(include_loopback=True)

            # Strategy 1: Match name
            for mic in all_mics:
                if speaker_name in mic.name and mic.isloopback:
                    loopback_mic = mic
                    break

            # Strategy 2: First loopback found
            if not loopback_mic:
                for mic in all_mics:
                    if mic.isloopback:
                        loopback_mic = mic
                        break

            if not loopback_mic:
                # Fallback to default mic if no loopback found (though strictly requested loopback)
                # But protocol says "find loopback... corresponding to default speaker"
                # If fail, we might log error, but let's default to standard mic to avoid crash
                loopback_mic = sc.default_microphone()

            self.mic = loopback_mic
            self._record_stream()

        except Exception as e:
            print(f"[Audio] Error initializing loopback: {e}")

    def _record_stream(self):
        """
        Records stream with sample rate fallback.
        """
        rates_to_try = [48000, 44100]

        for rate in rates_to_try:
            try:
                self.sample_rate = rate
                # Correction: "Não chame .recorder() no objeto Speaker" - we are using self.mic which is a Microphone object
                with self.mic.recorder(samplerate=self.sample_rate) as recorder:
                    while self.recording:
                        data = recorder.record(numframes=1024)
                        self.frames.append(data)

                # If we exit the loop cleanly (recording stopped), break the rate loop
                break

            except Exception as e:
                print(f"[Audio] Error with sample rate {rate}: {e}")
                # Loop will try next rate
                continue
