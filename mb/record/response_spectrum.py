#  Copyright (C) 2022 Theodore Chang
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os

import numpy as np
from joblib import Parallel, delayed
from numba import float64
from numba.experimental import jitclass


@jitclass([
    ('omega', float64),
    ('zeta', float64),
    ('alpha', float64),
    ('beta', float64),
    ('gamma', float64),
    ('a', float64),
    ('b', float64),
    ('c', float64),
])
class Oscillator:
    def __init__(self, o: float, z: float):
        self.omega: float = o
        self.zeta: float = z
        self.alpha: float = self.omega * self.zeta
        self.beta: float = self.omega * np.sqrt(1 - self.zeta ** 2)
        self.gamma: float = 0
        self.a: float = 0
        self.b: float = 0
        self.c: float = 0

    @property
    def factor(self):
        return self.gamma * self.a

    @staticmethod
    def amplitude(data: np.ndarray):
        return np.max(np.abs(data))

    def compute_parameter(self, interval: float):
        exp_term = np.exp(-self.alpha * interval)

        self.a = exp_term * np.sin(self.beta * interval) / self.beta
        self.b = 2 * exp_term * np.cos(self.beta * interval)
        self.c = exp_term ** 2

        self.gamma = (1 - self.b + self.c) / self.a / interval / self.omega ** 2

    def populate(self, motion: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        displacement: np.ndarray = np.zeros_like(motion, dtype=np.float64)
        displacement[1] = self.b * displacement[0] - motion[0]

        for i in range(2, len(motion)):
            displacement[i] = self.b * displacement[i - 1] - self.c * displacement[i - 2] - motion[i - 1]

        velocity: np.ndarray = np.zeros_like(motion, dtype=np.float64)
        velocity[1:] = np.diff(displacement)

        acceleration: np.ndarray = np.zeros_like(motion, dtype=np.float64)
        acceleration[1:] = np.diff(velocity)

        return displacement, velocity, acceleration

    def compute_response(self, interval: float, motion: np.ndarray) -> np.ndarray:
        self.compute_parameter(interval)

        displacement, velocity, acceleration = self.populate(motion)

        displacement *= self.factor * interval
        velocity *= self.factor
        acceleration *= self.factor / interval

        return np.column_stack((displacement, velocity, acceleration))

    def compute_maximum_response(self, interval: float, motion: np.ndarray) -> np.ndarray:
        self.compute_parameter(interval)

        displacement, velocity, acceleration = self.populate(motion)

        return np.array([
            self.amplitude(displacement) * self.factor * interval,
            self.amplitude(velocity) * self.factor,
            self.amplitude(acceleration * self.factor / interval + motion)])


def response_spectrum(damping_ratio: float, interval: float, motion: np.ndarray, period: np.ndarray) -> np.ndarray:
    def compute_task(p):
        oscillator = Oscillator(2 * np.pi / p, damping_ratio)
        return oscillator.compute_maximum_response(interval, motion)

    spectrum = np.array(Parallel(n_jobs=len(os.sched_getaffinity(0)), prefer='threads')(
        delayed(compute_task)(p) for p in period))
    # spectrum = np.array(compute_task(p) for p in period)

    return np.column_stack((period, spectrum))


def sdof_response(damping_ratio: float, interval: float, freq: float, motion: np.ndarray) -> np.ndarray:
    oscillator = Oscillator(2 * np.pi * freq, damping_ratio)
    return np.column_stack((interval * np.arange(len(motion)), oscillator.compute_response(interval, motion)))
