import pyaudio
import wave

import hardware

class Recording:
    def __init__(self, hw):
        self.hw = hw
        self.audio = pyaudio.PyAudio()  # Create an interface to PortAudio

    def record(self):
        chunk = 1024  # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt16  # 16 bits per sample
        channels = 1
        fs = 44100  # Record at 44100 samples per second
        # filename = "output.wav"


        print('Recording')

        stream = self.audio.open(format=sample_format,
                        channels=channels,

                        rate=fs,
                        frames_per_buffer=chunk,
                        input=True)

        frames = []  # Initialize array to store frames

        # Store data in chunks for 3 seconds
        while self.hw.btn_pressed(hardware.Hardware.Buttons.Rec):
            data = stream.read(chunk)
            frames.append(data)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        # Terminate the PortAudio interface
        # p.terminate()


        print('Finished recording')

        # Save the recorded data as a WAV file
        wf = wave.open('/tmp/recording.wav', 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(self.audio.get_sample_size(sample_format))
        wf.setframerate(fs)
        wf.writeframes(b''.join(frames))
        wf.close()
        return '/tmp/recording.wav'
