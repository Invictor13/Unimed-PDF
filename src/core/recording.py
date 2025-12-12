import os
import time
import threading
import cv2
import numpy as np
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from .audio_recorder import AudioRecorder

class VideoWorker:
    def __init__(self, output_path="temp_video.avi"):
        self.output_path = output_path
        self.writer = None
        self.recording = False
        self.thread = None

    def start(self):
        self.recording = True
        self.thread = threading.Thread(target=self._record_loop)
        self.thread.start()

    def _record_loop(self):
        # Basic mock implementation of screen recording using OpenCV
        # In a real app, this would capture screen content.
        # Here we just generate noise to simulate video file creation.
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.writer = cv2.VideoWriter(self.output_path, fourcc, 20.0, (640, 480))

        while self.recording:
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            self.writer.write(frame)
            time.sleep(0.05)

        # We don't close here, we rely on stop_writer to be explicit as per protocol

    def stop_writer(self):
        self.recording = False
        if self.thread:
            self.thread.join()
        if self.writer:
            self.writer.release()
            self.writer = None

class RecordingService:
    def __init__(self):
        self.video_worker = VideoWorker("temp_video.avi")
        self.audio_recorder = AudioRecorder()
        self.output_path = "output.mp4"
        self.temp_video = "temp_video.avi"
        self.temp_audio = "temp_audio.wav"

    def start_recording(self):
        # Ensure temps are clean
        if os.path.exists(self.temp_video): os.remove(self.temp_video)
        if os.path.exists(self.temp_audio): os.remove(self.temp_audio)

        self.video_worker.start()
        self.audio_recorder.start()

    def stop_recording(self):
        try:
            # Clean up resources explicitly
            if self.video_worker:
                self.video_worker.stop_writer()

            if self.audio_recorder:
                self.audio_recorder.stop()

            # Protocol: Safety delay
            time.sleep(2.0)

            # Start merge
            self.merge_video_audio()

        except Exception as e:
            print(f"Error stopping recording: {e}")

    def merge_video_audio(self):
        """
        Merges video and audio with retry logic to avoid WinError 32.
        """
        attempts = 3
        for i in range(attempts):
            try:
                if not os.path.exists(self.temp_video):
                    print(f"Video temp file missing: {self.temp_video}")
                    return
                # Audio might be missing if no mic found, handle gracefully
                has_audio = os.path.exists(self.temp_audio)

                video_clip = VideoFileClip(self.temp_video)

                if has_audio:
                    audio_clip = AudioFileClip(self.temp_audio)
                    final_clip = video_clip.with_audio(audio_clip)
                else:
                    final_clip = video_clip

                final_clip.write_videofile(self.output_path, codec="libx264", audio_codec="aac" if has_audio else None)

                video_clip.close()
                if has_audio:
                    audio_clip.close()

                # Cleanup temps
                if os.path.exists(self.temp_video):
                    os.remove(self.temp_video)
                if has_audio and os.path.exists(self.temp_audio):
                    os.remove(self.temp_audio)

                print("Merge successful.")
                break

            except PermissionError as e: # Catch WinError 32 (file in use)
                print(f"Merge attempt {i+1} failed: {e}")
                time.sleep(1.0) # Wait before retry
            except Exception as e:
                print(f"Merge error: {e}")
                import traceback
                traceback.print_exc()
                break
