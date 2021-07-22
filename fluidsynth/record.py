import time
import numpy
import pyaudio
import fluidsynth
import os
import wave

class RecordAudio:

    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 2
    fs = 44100  # Record at 44100 samples per second
    filename = "output.wav"

    def __init__(self):
        self.__fix_pulseaudio()
        self.raw_audio_strings = []
        self.pa = pyaudio.PyAudio()
        self.strm = self.pa.open(
            format = self.sample_format,
            channels = self.channels, 
            rate = self.fs, 
            output = True)

    def add_record(self, raw_audio_strings):
        self.raw_audio_strings.append(raw_audio_strings)

    def remove_record(self, index):
        del self.raw_audio_strings[index]

    def remove_all(self):
        self.raw_audio_strings = []

    def play(self, index):
        self.strm.write(self.raw_audio_strings[index])

    def play_all(self):
        complete_audio = b"".join(self.raw_audio_strings)
        self.strm.write(complete_audio)

    def create_wav_file(self):
        print("hi")

    def undo(self):
        del self.raw_audio_strings[-1]

    def export_record(self):
        complete_audio = b"".join(self.raw_audio_strings)
        wf = wave.open("output.wav", "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.pa.get_sample_size(self.sample_format))
        wf.setframerate(self.fs)
        wf.writeframes(complete_audio)
        wf.close()


    def __fix_pulseaudio(self):
        os.system("aconnect -x && pulseaudio --kill && systemctl --user stop pulseaudio.socket && systemctl --user stop pulseaudio.service && sleep 2 && pulseaudio --start")


s = []

fl = fluidsynth.Synth()

# Initial silence is 1 second
s = numpy.append(s, fl.get_samples(44100 * 1))
fl.start(driver='alsa')
sfid = fl.sfload('./pns_drum.sf2')
fl.program_select(0, sfid, 0, 0)

fl.noteon(0, 35, 100)

# Chord is held for 2 seconds
for i in range(2):
    s = numpy.append(s, fl.get_samples(int(44100 * 1.4)))
    fl.noteon(0, 38, 100)
    fl.noteon(0, 46, 100)

# Chord is held for 2 seconds
s = numpy.append(s, fl.get_samples(44100 * 1))

fl.noteon(0, 46, 100)

# Decay of chord is held for 1 second
s = numpy.append(s, fl.get_samples(44100 * 1))

fl.delete()

samps = fluidsynth.raw_audio_string(s)

recorder = RecordAudio()

recorder.add_record(samps)

recorder.add_record(samps)

recorder.undo()


recorder.play_all()

recorder.export_record()


