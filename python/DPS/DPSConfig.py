import numpy as np

class DataProcessing:

    @staticmethod
    def LookUpTable(LogFactor, freq, t, dt, N):
        for k in range(N - len(t)):
            dt = np.append(dt, max(freq, t[-1] / LogFactor))
            t = np.append(t, sum(dt))

        return t

    @staticmethod
    def PV2int(PVinfo):
        return np.round(PVinfo).astype(int)

    @staticmethod
    def PV2time(PVinfo, T):
        return np.array([T[x] for k, x in enumerate(PVinfo)])