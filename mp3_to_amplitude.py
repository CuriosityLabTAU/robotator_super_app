import scipy.io.wavfile
import pydub
import matplotlib.pyplot as plt
import numpy as np
import csv
from scipy import signal
import os
from os import listdir


def plot_signal(signal, rate):
    # create a time variable in seconds
    time = np.arange(0, float(len(signal)), 1) / rate
    # plot amplitude (or loudness) over time
    plt.figure(1)
    plt.plot(time, signal, linewidth=0.01, alpha=0.7, color='#ff7f00')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.show()

def downsample(signal1, rate1, rate2, norm_factor):  # rate1 = current sample rate. rate2 = desired sample rate
    #norm factor is used to scale the signal's amplitude
    r1 = float(rate1)
    r2 = float(rate2)
    l1 = len(signal1)
    l2 = (l1 * r2) / r1
    interval = l1 / l2
    signal2 = []
    i = 0
    index = 0
    while index < l1:
        # print i
        signal2.append(signal1[index] / norm_factor)
        index = int(np.rint(i * interval))
        i += 1
    return signal2


def write2csv(signal, file_name):
    with open(file_name, 'wb') as f:
        wr = csv.writer(f)
        for val in signal:
            wr.writerow([val])


def mp3_2_amplitude(mp3_file_name):
    #read mp3 file
    mp3 = pydub.AudioSegment.from_mp3(mp3_file_name)
    #convert to wav
    mp3.export("file.wav", format="wav")
    #read wav file
    rate,audData=scipy.io.wavfile.read("file.wav")
    try:
        signal = audData[:,0] #left sound channel. for second channel (if stereo) change indes to 1
    except:
        signal = audData[:]  # left sound channel. for second channel (if stereo) change indes to 1
    amplitude = np.abs(signal)
    return amplitude, rate


def mp3_to_lip_csv(the_path, mp3_name):
    mp3_file_name = the_path + mp3_name
    signal1, rate1 = mp3_2_amplitude(mp3_file_name)
    #plot_signal(signal1, rate1)

    rate2 = 30 # frequency of Patricc motion player
    norm_factor = 30 # CHANGED TODO 50 # this is the optimal norm factor I found
    signal2 = downsample(signal1, rate1, rate2, norm_factor)

    csv_name = mp3_name[:-4] + '.csv'
    write2csv(signal2, the_path + csv_name)


def path_to_lip_csv(the_path):
    mp3_files = [f for f in listdir(the_path) if '.mp3' in f]

    for m in mp3_files:
        mp3_to_lip_csv(the_path, m)

# path_to_lip_csv('/home/curious/PycharmProjects/run_general_robot_script/roboroots/01_fuzzy/sounds/')