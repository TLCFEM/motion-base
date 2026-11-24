#  Copyright (C) 2022-2026 Theodore Chang
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

import numpy as np
from numba import float64, njit
from numba.experimental import jitclass


@jitclass(
    [
        ("beta", float64),
        ("gamma", float64),
    ]
)
class Newmark:
    def __init__(self, gamma: float = 0.5, beta: float = 0.25):
        self.gamma = gamma
        self.beta = beta

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        acceleration = np.asarray(acceleration, dtype=np.float64)
        displacement: np.ndarray = np.zeros_like(acceleration)
        velocity: np.ndarray = np.zeros_like(acceleration)

        fa: float = interval * self.gamma
        fb: float = interval - fa
        fc: float = interval**2 * self.beta
        fd: float = interval**2 * 0.5 - fc

        for i in range(1, len(acceleration)):
            velocity[i] = (
                velocity[i - 1] + fb * acceleration[i - 1] + fa * acceleration[i]
            )
            displacement[i] = (
                displacement[i - 1]
                + velocity[i - 1] * interval
                + fd * acceleration[i - 1]
                + fc * acceleration[i]
            )

        return displacement, velocity


# ---------------------------------------------------------------------------
# Time integration methods
#
# The classes below are Python translations of the undamped time integration
# methods shipped with suanPan.  Each class stores the parameters of the
# corresponding scheme and exposes the same ``integrate`` interface as
# :class:`Newmark`, that is, displacement and velocity are recovered from a
# sampled acceleration history.
#
# The acceleration history is assumed to be sampled at equally spaced full
# time steps.  For multi-stage schemes the intermediate stage accelerations
# are reconstructed from the two adjacent samples by linear interpolation.
# The update equations are otherwise identical to those used by suanPan and
# converge as the sampling is refined.
# ---------------------------------------------------------------------------


def _as_float_array(acceleration: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(np.asarray(acceleration, dtype=np.float64).ravel())


@njit
def _integrate_newmark_like(
    interval: float,
    gamma: float,
    beta: float,
    acceleration: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    displacement = np.zeros_like(acceleration)
    velocity = np.zeros_like(acceleration)

    fa = interval * gamma
    fb = interval - fa
    fc = interval**2 * beta
    fd = 0.5 * interval**2 - fc

    for i in range(1, len(acceleration)):
        velocity[i] = velocity[i - 1] + fb * acceleration[i - 1] + fa * acceleration[i]
        displacement[i] = (
            displacement[i - 1]
            + velocity[i - 1] * interval
            + fd * acceleration[i - 1]
            + fc * acceleration[i]
        )

    return displacement, velocity


@njit
def _integrate_tchamwa(
    interval: float,
    phi: float,
    acceleration: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    displacement = np.zeros_like(acceleration)
    velocity = np.zeros_like(acceleration)

    for i in range(1, len(acceleration)):
        velocity[i] = velocity[i - 1] + interval * acceleration[i - 1]
        displacement[i] = (
            displacement[i - 1]
            + interval * velocity[i - 1]
            + phi * interval**2 * acceleration[i - 1]
        )

    return displacement, velocity


@njit
def _integrate_generalized_alpha_explicit(
    interval: float,
    beta: float,
    acceleration: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    displacement = np.zeros_like(acceleration)
    velocity = np.zeros_like(acceleration)

    for i in range(1, len(acceleration)):
        velocity[i] = velocity[i - 1] + interval * acceleration[i - 1]
        displacement[i] = (
            displacement[i - 1]
            + interval * velocity[i - 1]
            + interval**2
            * ((0.5 - beta) * acceleration[i - 1] + beta * acceleration[i])
        )

    return displacement, velocity


@njit
def _integrate_bathe_explicit(
    interval: float,
    p: float,
    q0: float,
    q1: float,
    q2: float,
    acceleration: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    displacement = np.zeros_like(acceleration)
    velocity = np.zeros_like(acceleration)

    h1 = p * interval
    h2 = interval - h1

    for i in range(1, len(acceleration)):
        a0 = acceleration[i - 1]
        a1 = acceleration[i]
        am = a0 + p * (a1 - a0)

        # first (trapezoidal) sub-step
        um = displacement[i - 1] + h1 * velocity[i - 1] + 0.5 * h1**2 * a0
        vm = velocity[i - 1] + 0.5 * h1 * (a0 + am)

        # second (Bathe) sub-step
        displacement[i] = um + h2 * vm + 0.5 * h2**2 * am
        velocity[i] = vm + h2 * (q0 * a0 + (0.5 + q1) * am + q2 * a1)

    return displacement, velocity


@njit
def _integrate_bathe_two_step(
    interval: float,
    gamma: float,
    q0: float,
    q1: float,
    q2: float,
    acceleration: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    displacement = np.zeros_like(acceleration)
    velocity = np.zeros_like(acceleration)

    h1 = gamma * interval

    for i in range(1, len(acceleration)):
        a0 = acceleration[i - 1]
        a1 = acceleration[i]
        am = a0 + gamma * (a1 - a0)

        # first (trapezoidal) sub-step
        vm = velocity[i - 1] + 0.5 * h1 * (a0 + am)

        # second (three-point Euler) sub-step
        velocity[i] = velocity[i - 1] + interval * (q0 * a0 + q1 * am + q2 * a1)
        displacement[i] = displacement[i - 1] + interval * (
            q0 * velocity[i - 1] + q1 * vm + q2 * velocity[i]
        )

    return displacement, velocity


@njit
def _integrate_oalts(
    interval: float,
    a1: float,
    a2: float,
    b0: float,
    b10: float,
    b20: float,
    acceleration: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    displacement = np.zeros_like(acceleration)
    velocity = np.zeros_like(acceleration)

    if len(acceleration) < 2:
        return displacement, velocity

    # the first step starts with the trapezoidal rule
    velocity[1] = velocity[0] + 0.5 * interval * (acceleration[0] + acceleration[1])
    displacement[1] = displacement[0] + 0.5 * interval * (velocity[0] + velocity[1])

    p1 = 1.0 / (b0 * interval)

    for i in range(2, len(acceleration)):
        velocity[i] = (
            acceleration[i] / p1
            - a1 * velocity[i - 1]
            - a2 * velocity[i - 2]
            + (b10 * acceleration[i - 1] + b20 * acceleration[i - 2]) / p1
        )
        displacement[i] = (
            velocity[i] / p1
            - a1 * displacement[i - 1]
            - a2 * displacement[i - 2]
            + (b10 * velocity[i - 1] + b20 * velocity[i - 2]) / p1
        )

    return displacement, velocity


@njit
def _integrate_gerkn(
    interval: float,
    c1: float,
    c2: float,
    vb0: float,
    vb1: float,
    vb2: float,
    ub0: float,
    ub1: float,
    ub2: float,
    acceleration: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    displacement = np.zeros_like(acceleration)
    velocity = np.zeros_like(acceleration)

    for i in range(1, len(acceleration)):
        a0 = acceleration[i - 1]
        a1 = acceleration[i]
        da = a1 - a0
        ac = a0 + c1 * da
        at = a0 + c2 * da

        velocity[i] = velocity[i - 1] + interval * (vb0 * a0 + vb1 * ac + vb2 * at)
        displacement[i] = (
            displacement[i - 1]
            + interval * velocity[i - 1]
            + interval**2 * (ub0 * a0 + ub1 * ac + ub2 * at)
        )

    return displacement, velocity


def _clamp_unit(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _three_radii(
    r1: float | np.ndarray,
    r2: float | None,
    r3: float | None,
) -> tuple[float, float, float]:
    if r2 is None and r3 is None:
        if np.ndim(r1) == 0:
            values = [float(r1)] * 3
        else:
            values = [float(value) for value in np.ravel(r1)]
    elif r2 is None or r3 is None:
        raise ValueError("Either one sequence or three spectral radii are required.")
    else:
        values = [float(r1), float(r2), float(r3)]

    if len(values) != 3:
        raise ValueError("Exactly three spectral radii are required.")

    return tuple(sorted(_clamp_unit(value) for value in values))


class Integrator:
    """Common interface for the translated time integration methods."""

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        raise NotImplementedError


class _NewmarkLike(Integrator):
    """Base class for schemes sharing the Newmark kinematic update."""

    def __init__(self, gamma: float, beta: float):
        self.gamma: float = gamma
        self.beta: float = beta

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        return _integrate_newmark_like(
            float(interval),
            self.gamma,
            self.beta,
            _as_float_array(acceleration),
        )


class GeneralizedAlpha(_NewmarkLike):
    """Generalized-alpha method (doi:10.1115/1.2900803).

    With a single argument the spectral radius at infinity is expected; with
    two arguments the ``alpha_f`` and ``alpha_m`` parameters are used directly.
    """

    def __init__(self, spectral_radius: float = 0.5, alpha_m: float | None = None):
        if alpha_m is None:
            radius = _clamp_unit(spectral_radius)
            alpha_f = radius / (radius + 1.0)
            alpha_m = (2.0 * radius - 1.0) / (radius + 1.0)
            self.spectral_radius: float | None = radius
        else:
            alpha_f = min(0.5, max(float(spectral_radius), 0.0))
            alpha_m = min(alpha_f, max(float(alpha_m), -1.0))
            self.spectral_radius = None

        gamma = 0.5 - alpha_m + alpha_f
        beta = 0.25 * (gamma + 0.5) ** 2

        super().__init__(gamma, beta)

        self.alpha_f: float = alpha_f
        self.alpha_m: float = alpha_m


class GeneralizedAlphaExplicit(Integrator):
    """Explicit generalized-alpha method."""

    def __init__(self, spectral_radius: float = 0.5):
        radius = _clamp_unit(spectral_radius)

        self.spectral_radius: float = radius
        self.beta: float = (radius**2 - 5.0 * radius + 10.0) / (
            6.0 * (radius - 2.0) * (radius + 1.0)
        )
        self.alpha_m: float = (2.0 * radius - 1.0) / (1.0 + radius)
        self.alpha_f: float = self.alpha_m - 0.5

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        return _integrate_generalized_alpha_explicit(
            float(interval), self.beta, _as_float_array(acceleration)
        )


class GSSSS(_NewmarkLike):
    """Base class for the generalized single-step single-solve schemes."""

    def __init__(self, l3: float, l5: float):
        self.l3: float = l3
        self.l5: float = l5
        super().__init__(l5, l3)


class GSSSSU0(GSSSS):
    """GSSSS U0 scheme (spectral radii are sorted and clamped to [0, 1])."""

    def __init__(
        self,
        r1: float | np.ndarray = 1.0,
        r2: float | None = None,
        r3: float | None = None,
    ):
        r1, r2, r3 = _three_radii(r1, r2, r3)

        l3 = 1.0 / (1.0 + r1) / (1.0 + r2)
        l5 = 0.5 * (3.0 + r1 + r2 - r1 * r2) * l3
        w1 = 1.0 / (1.0 + r3)
        w3g3 = l3 * w1
        w2g5 = l5 * w1
        w1g6 = (2.0 + r1 + r2 + r3 - r1 * r2 * r3) * w3g3

        super().__init__(l3, l5)

        self.r1, self.r2, self.r3 = r1, r2, r3
        self.w1, self.w3g3, self.w2g5, self.w1g6 = w1, w3g3, w2g5, w1g6


class GSSSSV0(GSSSS):
    """GSSSS V0 scheme (spectral radii are sorted and clamped to [0, 1])."""

    def __init__(
        self,
        r1: float | np.ndarray = 1.0,
        r2: float | None = None,
        r3: float | None = None,
    ):
        r1, r2, r3 = _three_radii(r1, r2, r3)

        l3 = 0.5 / (1.0 + r3)
        l5 = 2.0 * l3

        t0 = 9.0 - 11.0 * r1 - 11.0 * r2 + 19.0 * r1 * r2
        t1 = -30.0 * (3.0 - 4.0 * r1 - 4.0 * r2 + 6.0 * r1 * r2)
        t2 = 7.5 * (25.0 - 37.0 * r1 - 37.0 * r2 + 53.0 * r1 * r2)
        t3 = -35.0 * (3.0 - 5.0 * r1 - 5.0 * r2 + 7.0 * r1 * r2)

        w1 = (t0 / 2.0 + t1 / 3.0 + t2 / 4.0 + t3 / 5.0) / (
            t0 + t1 / 2.0 + t2 / 3.0 + t3 / 4.0
        )
        w3g3 = l5 / (1.0 + r1) / (1.0 + r2)
        w2g5 = 2.0 * w3g3
        w1g6 = (2.0 + r1 + r2 + r3 - r1 * r2 * r3) * w3g3

        super().__init__(l3, l5)

        self.r1, self.r2, self.r3 = r1, r2, r3
        self.w1, self.w3g3, self.w2g5, self.w1g6 = w1, w3g3, w2g5, w1g6


class GSSSSOptimal(GSSSS):
    """GSSSS optimal scheme."""

    def __init__(self, spectral_radius: float = 0.5):
        radius = _clamp_unit(spectral_radius)

        l3 = 0.5 / (1.0 + radius)
        l5 = 2.0 * l3
        w1 = l5
        w3g3 = l3 * l5
        w2g5 = l5 * l5
        w1g6 = (1.0 + radius) * (3.0 - radius) * w3g3

        super().__init__(l3, l5)

        self.spectral_radius = radius
        self.w1, self.w3g3, self.w2g5, self.w1g6 = w1, w3g3, w2g5, w1g6


class GSSE(_NewmarkLike):
    """Generalized explicit integration method (doi:10.1002/nme.6574)."""

    def __init__(self, rs: float = 0.5, rb: float | None = None):
        if rb is None:
            rs = _clamp_unit(rs)
            rb = rs
        else:
            rs = float(rs)
            rb = float(rb)

        c = (2.0 + rs - rb * rs) / (rb * rs + rb + rs + 1.0)
        ua0 = 0.5 * c**2
        va0 = c
        ub = (
            (
                rb * (rb - 1.0) * rs**3
                + 0.5 * (rb - 1.0) * (rb**2 + 6.0 * rb - 1.0) * rs**2
                + (1.0 - 5.0 * rb) * rs
                + 1.0
                - rb
            )
            / (-1.0 - rb)
            / (1.0 + rs)
            / (rb * rs - rs - 2.0) ** 2
        )
        vb = 0.5 / c
        ab = 1.0 / c

        super().__init__(vb, ub)

        self.rs: float = rs
        self.rb: float = rb
        self.c: float = c
        self.ua0: float = ua0
        self.va0: float = va0
        self.ub: float = ub
        self.vb: float = vb
        self.ab: float = ab


class ICL(GSSE):
    """ICL explicit scheme, a specialization of :class:`GSSE`."""

    def __init__(self, spectral_radius: float = 0.5):
        radius = min(1.0, max(0.5, float(spectral_radius)))
        rs = 0.5 * (1.0 / radius - 1.0)

        super().__init__(rs, radius)

        self.spectral_radius = radius


class Tchamwa(Integrator):
    """Tchamwa explicit scheme."""

    def __init__(self, spectral_radius: float = 0.5):
        radius = _clamp_unit(spectral_radius)
        self.spectral_radius: float = radius
        self.phi: float = 2.0 / (1.0 + radius)

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        return _integrate_tchamwa(
            float(interval), self.phi, _as_float_array(acceleration)
        )


class BatheExplicit(Integrator):
    """Explicit Bathe scheme (doi:10.1016/j.compstruc.2013.06.007)."""

    def __init__(self, spectral_radius: float = 0.5):
        radius = _clamp_unit(spectral_radius)

        p = 2.0 / (2.0 + np.sqrt(2.0 + 2.0 * radius))
        q1 = (0.5 - p) / p / (1.0 - p)
        q2 = 0.5 - p * q1
        q0 = 0.5 - q1 - q2

        self.spectral_radius: float = radius
        self.p: float = p
        self.q0: float = q0
        self.q1: float = q1
        self.q2: float = q2

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        return _integrate_bathe_explicit(
            float(interval),
            self.p,
            self.q0,
            self.q1,
            self.q2,
            _as_float_array(acceleration),
        )


class BatheTwoStep(Integrator):
    """Implicit Bathe two-step scheme."""

    def __init__(self, spectral_radius: float = 0.0, gamma: float = 0.5):
        radius = _clamp_unit(spectral_radius)
        gamma = float(gamma)
        if not 0.0 < gamma < 1.0:
            gamma = 0.5

        q1 = (radius + 1.0) / (2.0 * gamma * (radius - 1.0) + 4.0)
        q2 = 0.5 - gamma * q1
        q0 = 1.0 - q1 - q2

        self.spectral_radius: float = radius
        self.gamma: float = gamma
        self.q0: float = q0
        self.q1: float = q1
        self.q2: float = q2

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        return _integrate_bathe_two_step(
            float(interval),
            self.gamma,
            self.q0,
            self.q1,
            self.q2,
            _as_float_array(acceleration),
        )


class OALTS(Integrator):
    """OALTS scheme (doi:10.1002/nme.6188)."""

    def __init__(self, spectral_radius: float = 0.5):
        radius = _clamp_unit(spectral_radius)

        a1 = (4.0 * radius - 4.0) / (3.0 - radius)
        a2 = -1.0 - a1
        b0 = 2.0 / (1.0 + radius) / (3.0 - radius)
        b1 = 2.0 - 2.0 * b0 + 0.5 * a1
        b2 = 0.5 * a1 + b0
        b10 = b1 / b0
        b20 = b2 / b0

        self.spectral_radius: float = radius
        self.a1: float = a1
        self.a2: float = a2
        self.b0: float = b0
        self.b1: float = b1
        self.b2: float = b2
        self.b10: float = b10
        self.b20: float = b20

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        return _integrate_oalts(
            float(interval),
            self.a1,
            self.a2,
            self.b0,
            self.b10,
            self.b20,
            _as_float_array(acceleration),
        )


class GERKN(Integrator):
    """Generalized explicit Runge-Kutta-Nystrom scheme (doi:10.1002/nme.7658)."""

    def __init__(
        self,
        c1: float = 0.0,
        c2: float = 0.0,
        va10: float = 0.0,
        va20: float = 0.0,
        va21: float = 0.0,
        vb0: float = 0.0,
        vb1: float = 0.0,
        vb2: float = 0.0,
        ua10: float = 0.0,
        ua20: float = 0.0,
        ua21: float = 0.0,
        ub0: float = 0.0,
        ub1: float = 0.0,
        ub2: float = 0.0,
        ab0: float = 0.0,
        ab1: float = 0.0,
        ab2: float = 0.0,
    ):
        self.c1: float = c1
        self.c2: float = c2
        self.va10, self.va20, self.va21 = va10, va20, va21
        self.vb0, self.vb1, self.vb2 = vb0, vb1, vb2
        self.ua10, self.ua20, self.ua21 = ua10, ua20, ua21
        self.ub0, self.ub1, self.ub2 = ub0, ub1, ub2
        self.ab0, self.ab1, self.ab2 = ab0, ab1, ab2

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        return _integrate_gerkn(
            float(interval),
            self.c1,
            self.c2,
            self.vb0,
            self.vb1,
            self.vb2,
            self.ub0,
            self.ub1,
            self.ub2,
            _as_float_array(acceleration),
        )


class WAT2(GERKN):
    """WAT2 scheme, the concrete member of the GERKN family in suanPan."""

    def __init__(self, parameter: float = 1.0 / 3.0):
        radius = 0.1 * _clamp_unit(parameter) + 0.3

        e = 2.0 * radius - 1.0
        d = 3.0 * radius**2 - 3.0 * radius + 1.0
        f = radius * d
        e2 = e**2

        c1 = radius
        c2 = (3.0 * c1 - 2.0) / 3.0 / e

        va10 = c1
        va21 = 2.0 / 9.0 * d / c1 / e2
        va20 = c2 - va21

        ua10 = c1 / 6.0
        ua20 = (3.0 * c1 - 1.0) / 18.0 / c1
        ua21 = d / 18.0 / c1 / e2

        vb0 = 0.0
        vb1 = 0.25 / d
        vb2 = 1.0 - vb1

        ub0 = (4.0 * c1 - 1.0) / 12.0 / c1
        ub1 = (6.0 * c1**2 - 5.0 * c1 + 2.0) / 24.0 / f
        ub2 = 0.5 - ub0 - ub1

        ab0 = (1.0 - 3.0 * c1) / c1
        ab1 = (-3.0 * c1**2 + 4.0 * c1 - 1.0) / f
        ab2 = 1.0 - ab0 - ab1

        super().__init__(
            c1,
            c2,
            va10,
            va20,
            va21,
            vb0,
            vb1,
            vb2,
            ua10,
            ua20,
            ua21,
            ub0,
            ub1,
            ub2,
            ab0,
            ab1,
            ab2,
        )

        self.parameter: float = parameter
        self.radius: float = radius


# Alternative British spelling used by suanPan.
GeneralisedAlpha = GeneralizedAlpha
GeneralisedAlphaExplicit = GeneralizedAlphaExplicit
