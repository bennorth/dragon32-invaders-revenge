import math
from dataclasses import dataclass, astuple
import numpy as np
import numpy.typing as npt
from scipy.stats import linregress
import scipy.io.wavfile as scipy_wav


############################################################################

FS_IN = 44100
FS_OUT = 48000
K_SQUARING = 6.5
CROSSING_THRESHOLD = 0.4
MIN_HPERIOD = 0.5 / (24.0e3)


############################################################################

@dataclass
class CrossingInfo:
    crossing_idxs: npt.ArrayLike
    half_periods: npt.ArrayLike

    @classmethod
    def from_data(cls, data):
        thresholded = (data > CROSSING_THRESHOLD).astype(np.int8)
        crossing_idxs = np.where(np.diff(thresholded))[0]
        half_periods = np.diff(crossing_idxs)
        return cls(crossing_idxs, half_periods)


def float_data(fname, data_slice=None):
    sample_rate, sound_data = scipy_wav.read(fname)
    if sample_rate != FS_IN:
        raise ValueError(
            f"expecting sample rate of {FS_IN} but got {sample_rate}"
        )

    data = sound_data / 32768.0
    if data_slice is not None:
        data = data[data_slice]

    return data


############################################################################

@dataclass
class Gap:
    duration_chirps: float

    def synthesised(self, chirp_duration):
        return np.zeros(
            (int(self.duration_chirps * chirp_duration * FS_OUT),),
            dtype=np.float64
        )


############################################################################

@dataclass
class Chirp:
    half_period_0: float
    d_half_period: float
    len_chirps: float

    def __str__(self):
        hp0_ms = f"{(1.0e3 * self.half_period_0):.6f}"
        dhp_us = f"{(1.0e6 * self.d_half_period):.3f}"
        return f"<Chirp: f0 {(0.5 / self.half_period_0):6.1f}; {hp0_ms} / {dhp_us}>"

    @classmethod
    def from_mean(cls, chirps):
        data = np.array([astuple(ch) for ch in chirps])
        return cls(*data.mean(axis=0))

    def synthesised(self, chirp_duration):
        xp1 = 0.0
        yp1 = 0.0
        xp = [xp1]
        yp = [yp1]
        hperiod = self.half_period_0
        wave_duration = self.len_chirps * chirp_duration
        while xp[-1] < wave_duration or (len(xp) % 2 == 0):
            xp1 += hperiod
            yp1 += math.pi
            xp.append(xp1)
            yp.append(yp1)
            hperiod += self.d_half_period
            hperiod = max(hperiod, MIN_HPERIOD)

        interp_node_ts = np.array(xp)
        interp_node_phs = np.array(yp)

        n_samples = int(xp1 * FS_OUT)
        chirp_xs = np.arange(n_samples, dtype=np.float64)
        chirp_ts = chirp_xs / FS_OUT
        chirp_phs = np.interp(chirp_ts, interp_node_ts, interp_node_phs)
        chirp_ys = np.tanh(K_SQUARING * np.sin(chirp_phs))

        return chirp_ys

    @classmethod
    def from_half_periods(cls, half_periods):
        regr_xs = np.arange(len(half_periods))
        regr_ys = half_periods
        regr_data = linregress(regr_xs, regr_ys)
        return cls(
            regr_data.intercept / FS_IN,
            regr_data.slope / FS_IN,
            1,
        )


############################################################################

@dataclass
class SoundEffect:
    fragments: [Chirp | Gap]

    def synthesised(self, chirp_duration):
        chunks = [
            chirp.synthesised(chirp_duration)
            for chirp in self.fragments
        ]
        lead_in_out = [np.zeros(int(0.001 * FS_OUT), dtype=np.float64)]
        return np.concat(lead_in_out + chunks + lead_in_out)

    @classmethod
    def from_wav_file(cls, fname, n_chirps, data_slice=None):
        data = float_data(fname, data_slice)

        xinfo = CrossingInfo.from_data(data)
        n_gaps = n_chirps - 1

        if n_gaps == 0:
            return cls([Chirp.from_half_periods(xinfo.half_periods)])

        # The longest n_breaks "half periods" are in fact gaps between
        # chirps.
        s_hperiods = sorted(xinfo.half_periods, reverse=True)

        # s_hperiods[n_gaps-1] should be the shortest gap between
        # chirps, and s_hperiods[n_gaps] the longest true half-period
        # of a chirp.  Split the difference.
        threshold = np.mean([s_hperiods[n_gaps - 1], s_hperiods[n_gaps]])

        gap_idxs = [int(i) for i in np.where(xinfo.half_periods > threshold)[0]]
        chirps = []
        for gi0, gi1 in zip([0] + gap_idxs, gap_idxs + [len(xinfo.half_periods)]):
            # Last half-wave seems to often get truncated, so omit
            # from regression.
            chirp_hperiods = xinfo.half_periods[gi0 + 1:gi1 - 1]
            chirps.append(Chirp.from_half_periods(chirp_hperiods))

        return cls(chirps)

    def write_wav(self, fname, chirp_duration):
        samples = (self.synthesised(chirp_duration) * 24000.0).astype(np.int16)
        scipy_wav.write(fname, FS_OUT, samples)


############################################################################

if __name__ == "__main__":
    # Normal/special defender hit tails
    chirp_info = []
    for stem in ["normal-defender-hit", "special-defender-hit"]:
        for idx in range(3):
            fname = f"samples/{stem}-{idx}.wav"
            s = SoundEffect.from_wav_file(fname, 15)
            chirp_info.append(s.fragments)
    chirp_info_t = list(zip(*chirp_info))
    mean_chirps = [Chirp.from_mean(ci) for ci in chirp_info_t]
    for ch in mean_chirps:
        print(ch)

    print(np.mean([ch.d_half_period for ch in mean_chirps if ch.d_half_period > 5.0e-6]))
    print("end of defender hit tails")

if __name__ == "__main_1_":
    chirp_info = []
    for idx in range(3):
        fname = f"samples/special-defender-hit-initial-{idx}.wav"
        s = SoundEffect.from_wav_file(fname, 2)
        chirp_info.append(s.fragments)
    chirp_info_t = list(zip(*chirp_info))
    mean_chirps = [Chirp.from_mean(ci) for ci in chirp_info_t]
    for ch in mean_chirps:
        print(ch)

if __name__ == "__main_1_":
    chirp_info = []
    for idx in range(3):
        fname = f"samples/defender-base-hit-{idx}.wav"
        s = SoundEffect.from_wav_file(fname, 48)
        chirp_info.append(s.fragments)
    chirp_info_t = list(zip(*chirp_info))
    mean_chirps = [Chirp.from_mean(ci) for ci in chirp_info_t]
    for ch in mean_chirps:
        print(ch)

if __name__ == "__main_1_":
    chirp_info = []
    for idx in range(3):
        fname = f"samples/player-shot-{idx}.wav"
        s = SoundEffect.from_wav_file(fname, 6)
        chirp_info.append(s.fragments)
    chirp_info_t = list(zip(*chirp_info))
    mean_chirps = [Chirp.from_mean(ci) for ci in chirp_info_t]
    for ch in mean_chirps:
        print(ch)
    print(np.mean([ch.d_half_period for ch in mean_chirps]))

if __name__ == "__main_1_":
    chirp_info = []
    for idx in range(3):
        fname = f"samples/end-of-game-{idx}.wav"
        s = SoundEffect.from_wav_file(fname, 1)
        chirp_info.append(s.fragments)
    chirp_info_t = list(zip(*chirp_info))
    mean_chirps = [Chirp.from_mean(ci) for ci in chirp_info_t]
    for ch in mean_chirps:
        print(ch)

if __name__ == "__main__":
    chirp_info = []
    for idx in range(3):
        fname = f"samples/shot-hit-{idx}.wav"
        s = SoundEffect.from_wav_file(fname, 1)
        chirp_info.append(s.fragments)
    chirp_info_t = list(zip(*chirp_info))
    mean_chirps = [Chirp.from_mean(ci) for ci in chirp_info_t]
    for ch in mean_chirps:
        print(ch)

if __name__ == "__main__":
    chirps = []
    for fname, slice_argss in [
            (
                "samples/player-hit-0.wav",
                [(800, 2720), (2720, 4580), (4580, 8700)],
            ),
            (
                "samples/player-hit-1.wav",
                [(1300, 3200), (3200, 5050), (5050, 9200)],
            ),
            (
                "samples/player-hit-2.wav",
                [(1050, 2930), (2930, 4770), (4770, 8950)],
            )
    ]:
        for slice_args in slice_argss:
            s = SoundEffect.from_wav_file(fname, 1, slice(*slice_args))
            chirps.append(s.fragments[0])
            print(chirps[-1])
    mean_chirp = Chirp.from_mean(chirps)
    print()
    print(mean_chirp)
    # <Chirp: f0 7807.3; 0.064042 / 31.281>

if __name__ == "__main__":
    std_d_hp = 5.71e-6  # From mean() above
    std_chirp_duration = 18.7e-3

    player_hit_chirps = [
        Chirp(0.064e-3, 31.3e-6, 2.2),
        Chirp(0.064e-3, 31.3e-6, 2.2),
        Chirp(0.064e-3, 31.3e-6, 4.9),
    ]
    for hp0 in np.linspace(1.53e-3, 1.10e-3, 11):
        player_hit_chirps.append(Chirp(hp0, -13.5e-6, 2.5))
    player_hit = SoundEffect(player_hit_chirps)

    defender_hit_tail = [
        Chirp(0.354e-3, std_d_hp, 1.0),
        Chirp(0.353e-3, std_d_hp, 1.0),
        Chirp(0.319e-3, std_d_hp, 1.0),
        Chirp(0.330e-3, std_d_hp, 1.0),
        Chirp(0.271e-3, 0.0, 1.0),
        Chirp(0.270e-3, 0.0, 1.0),
        Chirp(0.477e-3, std_d_hp, 1.0),
        Chirp(0.520e-3, std_d_hp, 1.0),
        Chirp(0.435e-3, std_d_hp, 1.0),
        Chirp(0.492e-3, std_d_hp, 1.0),
        Chirp(0.416e-3, std_d_hp, 1.0),
        Chirp(0.458e-3, std_d_hp, 1.0),
        Gap(1.0),
        Chirp(0.374e-3, std_d_hp, 1.0),
        Chirp(0.431e-3, std_d_hp, 1.0)
    ]
    normal_defender_hit = SoundEffect(
        [
            Chirp(0.517e-3, 0.5 * std_d_hp, 3.0),
            Gap(2.5),
        ]
        + defender_hit_tail
    )
    special_defender_hit = SoundEffect(
        [
            Chirp(0.742e-3, -std_d_hp, 1.5),
            Chirp(0.742e-3, -std_d_hp, 1.5),
            Gap(2.5),
        ]
        + defender_hit_tail
    )

    player_chirp_d_hp = 14.4e-6;
    player_shot = SoundEffect(
        [
            Chirp(0.501e-3, player_chirp_d_hp, 1.0),
            Chirp(0.484e-3, player_chirp_d_hp, 1.0),
            Chirp(0.920e-3, player_chirp_d_hp, 1.0),
            Chirp(1.362e-3, player_chirp_d_hp, 1.0),
            Chirp(1.792e-3, player_chirp_d_hp, 1.0),
            Chirp(2.228e-3, player_chirp_d_hp, 1.0)
        ]
    )

    # Dumped from output from above, averaged in groups of 4 (or
    # sometimes 2) in spreadsheet.
    defender_base_hit = SoundEffect(
        [Chirp(1.330e-3, 1.2 * std_d_hp, 1.0)] * 2
        + [Chirp(1.396e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.200e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.259e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.327e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.395e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.723e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.800e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.859e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.929e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.720e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.788e-3, 1.2 * std_d_hp, 1.0)] * 4
        + [Chirp(1.868e-3, 1.2 * std_d_hp, 1.0)] * 2
    )

    shot_hit = SoundEffect([Chirp(3.539e-3, 3 * std_d_hp, 0.5)])

    end_of_game = SoundEffect([Chirp(0.063853e-3, 31.29e-6, 75)])

    player_hit.write_wav("ph.wav", std_chirp_duration)
    normal_defender_hit.write_wav("ndh.wav", std_chirp_duration)
    special_defender_hit.write_wav("sdh.wav", std_chirp_duration)
    player_shot.write_wav("psh.wav", std_chirp_duration)
    defender_base_hit.write_wav("dbh.wav", std_chirp_duration)
    end_of_game.write_wav("eog.wav", std_chirp_duration)
    shot_hit.write_wav("sh.wav", std_chirp_duration)

    print("done")
