import numpy as np
from scipy import signal

class TraditionalClassifier:
    def predict(self, x, fs):
        c3 = x[0] - np.mean(x[1:, :], axis=0)

        fmin = 7
        fmax = 13

        f, Pxx = signal.welch(c3, fs, nperseg=fs)
        ind_min = np.argmax(f > fmin) - 1
        ind_max = np.argmax(f > fmax) - 1
        return np.trapz(Pxx[ind_min: ind_max], f[ind_min: ind_max])
