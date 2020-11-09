import pip_manager
pip_manager.install_missing("pysndfx")

from pysndfx import AudioEffectsChain

from os import listdir
import numpy as np
import math

song_dir = "songs"
attenuate_db = 0
accentuate_db = 2


def bass_line_freq(track):
    sample_track = list(track)

    # c-value
    est_mean = np.mean(sample_track)

    # a-value
    est_std = 3 * np.std(sample_track) / (math.sqrt(2))

    bass_factor = int(round((est_std - est_mean) * 0.005))

    return bass_factor * 2


def low_pass(filename):

    fx = (
        AudioEffectsChain().lowpass(130, 100)
    )
    fx(filename, "BOOSTED-"+filename.split("/")[-1])

    return "BOOSTED-"+filename.split("/")[-1]


if __name__ == "__main__":
    low_pass("music.mp3")
