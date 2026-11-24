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

"""Time integration methods for sampled acceleration histories.

The classes in this module translate the undamped time integration methods
shipped with suanPan.  Every integrator exposes the same interface as
:class:`Newmark`::

    displacement, velocity = integrator.integrate(interval, acceleration)

``acceleration`` is an array-like object sampled at equally spaced times and
``interval`` is the spacing between consecutive samples.  Multi-dimensional
input is flattened to one dimension.  The returned arrays are one-dimensional,
have the same number of elements as the input and start from zero initial
displacement and velocity.

For multi-stage schemes the intermediate stage accelerations are reconstructed
from the two adjacent samples by linear interpolation (or extrapolation when a
stage time lies outside the step).  The update equations are otherwise those
used by suanPan.

Scheme parameters are stored as attributes.  Spectral radii are clamped to
their admissible ranges on construction, following suanPan.

:class:`Newmark` is implemented as a numba jitclass and therefore does not
inherit from :class:`Integrator`; it follows the same ``integrate`` protocol.
"""

from collections.abc import Sequence
from enum import StrEnum

import numpy as np
from numba import float64, njit
from numba.experimental import jitclass

__all__ = [
    "BatheExplicit",
    "BatheTwoStep",
    "GERKN",
    "GSSE",
    "GSSSS",
    "GSSSSOptimal",
    "GSSSSU0",
    "GSSSSV0",
    "GeneralisedAlpha",
    "GeneralisedAlphaExplicit",
    "GeneralizedAlpha",
    "GeneralizedAlphaExplicit",
    "ICL",
    "IntegrationType",
    "Integrator",
    "Newmark",
    "OALTS",
    "Tchamwa",
    "WAT2",
    "create_integrator",
]


class IntegrationType(StrEnum):
    """Names of the time integration methods available for processing."""

    Newmark = "Newmark"
    GeneralizedAlpha = "GeneralizedAlpha"
    GeneralizedAlphaExplicit = "GeneralizedAlphaExplicit"
    GSSSSU0 = "GSSSSU0"
    GSSSSV0 = "GSSSSV0"
    GSSSSOptimal = "GSSSSOptimal"
    GSSE = "GSSE"
    ICL = "ICL"
    Tchamwa = "Tchamwa"
    BatheExplicit = "BatheExplicit"
    BatheTwoStep = "BatheTwoStep"
    OALTS = "OALTS"
    WAT2 = "WAT2"

    # British spellings, matching the names accepted by the suanPan parser.
    GeneralisedAlpha = "GeneralizedAlpha"
    GeneralisedAlphaExplicit = "GeneralizedAlphaExplicit"

    @classmethod
    def _missing_(cls, value):
        """Accept case-insensitive names and common spelling variants."""
        if not isinstance(value, str):
            return None

        key = value.strip().lower().replace("-", "").replace("_", "").replace(" ", "")
        aliases = {
            "newmark": cls.Newmark,
            "generalizedalpha": cls.GeneralizedAlpha,
            "generalisedalpha": cls.GeneralizedAlpha,
            "generalizedalphaexplicit": cls.GeneralizedAlphaExplicit,
            "generalisedalphaexplicit": cls.GeneralizedAlphaExplicit,
            "gssssu0": cls.GSSSSU0,
            "gssssv0": cls.GSSSSV0,
            "gssssoptimal": cls.GSSSSOptimal,
            "gsse": cls.GSSE,
            "icl": cls.ICL,
            "tchamwa": cls.Tchamwa,
            "batheexplicit": cls.BatheExplicit,
            "bathetwostep": cls.BatheTwoStep,
            "oalts": cls.OALTS,
            "wat2": cls.WAT2,
        }
        return aliases.get(key)


@jitclass(
    [
        ("beta", float64),
        ("gamma", float64),
    ]
)
class Newmark:
    """Classical Newmark method.

    Parameters
    ----------
    gamma : float, optional
        Velocity weighting factor, by default 0.5.
    beta : float, optional
        Displacement weighting factor, by default 0.25.
    """

    def __init__(self, gamma: float = 0.5, beta: float = 0.25):
        self.gamma = gamma
        self.beta = beta

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        acceleration = np.asarray(acceleration, dtype=np.float64).ravel()
        return _integrate_newmark_like(
            float(interval), float(self.gamma), float(self.beta), acceleration
        )


def _as_float_array(acceleration: np.ndarray) -> np.ndarray:
    """Return a flat, contiguous ``float64`` view/copy of the input."""
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


def _clamp(value: float, lower: float, upper: float) -> float:
    """Clamp ``value`` to the closed interval ``[lower, upper]``."""
    return min(upper, max(lower, float(value)))


def _clamp_unit(value: float) -> float:
    """Clamp ``value`` to the unit interval."""
    return _clamp(value, 0.0, 1.0)


def _three_radii(
    r1: float | Sequence[float],
    r2: float | None,
    r3: float | None,
) -> tuple[float, float, float]:
    """Normalise and sort the three spectral radii used by GSSSS U0/V0."""
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
    """Common interface for the translated time integration methods.

    Subclasses implement :meth:`integrate`, which converts a sampled
    acceleration history into displacement and velocity histories, both with
    zero initial conditions.
    """

    def integrate(
        self, interval: float, acceleration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Integrate the acceleration history.

        Parameters
        ----------
        interval : float
            Time interval between consecutive acceleration samples.
        acceleration : array_like
            Sampled acceleration history.  The input is flattened to one
            dimension before integration.

        Returns
        -------
        tuple of numpy.ndarray
            Displacement and velocity histories.
        """
        raise NotImplementedError(f"{type(self).__name__} must implement integrate().")


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

    The scheme can be parameterised in two ways.

    * ``GeneralizedAlpha(spectral_radius)`` selects the spectral radius at
      infinity; ``alpha_f`` and ``alpha_m`` are then derived from it.
    * ``GeneralizedAlpha(alpha_f, alpha_m)`` uses the two alpha parameters
      directly.  They are clamped to their admissible ranges, matching
      suanPan.

    Parameters
    ----------
    spectral_radius : float, optional
        Spectral radius at infinity, by default 0.5.  When ``alpha_m`` is
        given, this argument is interpreted as ``alpha_f`` instead.
    alpha_m : float, optional
        Mass-weighted alpha parameter.  Providing it selects the direct
        ``(alpha_f, alpha_m)`` parameterisation.
    """

    def __init__(self, spectral_radius: float = 0.5, alpha_m: float | None = None):
        if alpha_m is None:
            radius = _clamp_unit(spectral_radius)
            alpha_f = radius / (radius + 1.0)
            alpha_m = (2.0 * radius - 1.0) / (radius + 1.0)
            self.spectral_radius: float | None = radius
        else:
            alpha_f = _clamp(spectral_radius, 0.0, 0.5)
            alpha_m = _clamp(alpha_m, -1.0, alpha_f)
            self.spectral_radius = None

        gamma = 0.5 - alpha_m + alpha_f
        beta = 0.25 * (gamma + 0.5) ** 2

        super().__init__(gamma, beta)

        self.alpha_f: float = alpha_f
        self.alpha_m: float = alpha_m


class GeneralizedAlphaExplicit(Integrator):
    """Explicit generalized-alpha method.

    Parameters
    ----------
    spectral_radius : float, optional
        Spectral radius at infinity, by default 0.5.  It is clamped to
        ``[0, 1]``.
    """

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
    """Base class for the generalized single-step single-solve schemes.

    The GSSSS family uses the Newmark kinematic update with
    ``beta = l3`` and ``gamma = l5``.  The remaining scheme constants are
    stored for reference but do not enter the acceleration-to-motion
    conversion.
    """

    def __init__(self, l3: float, l5: float):
        self.l3: float = l3
        self.l5: float = l5
        super().__init__(l5, l3)


class GSSSSU0(GSSSS):
    """GSSSS U0 scheme.

    The three spectral radii may be supplied as a sequence, as three separate
    arguments, or as one scalar used for all three.  They are sorted and
    clamped to ``[0, 1]``, matching suanPan.
    """

    def __init__(
        self,
        r1: float | Sequence[float] = 1.0,
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
    """GSSSS V0 scheme.

    The three spectral radii may be supplied as a sequence, as three separate
    arguments, or as one scalar used for all three.  They are sorted and
    clamped to ``[0, 1]``, matching suanPan.
    """

    def __init__(
        self,
        r1: float | Sequence[float] = 1.0,
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
    """GSSSS optimal scheme.

    Parameters
    ----------
    spectral_radius : float, optional
        Spectral radius at infinity, by default 0.5.  It is clamped to
        ``[0, 1]``.
    """

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
    """Generalized explicit integration method (doi:10.1002/nme.6574).

    Parameters
    ----------
    rs : float, optional
        Spectral radius of the explicit stage, by default 0.5.
    rb : float, optional
        Spectral radius of the final stage.  It defaults to ``rs``.  Both
        parameters are clamped to ``[0, 1]``.
    """

    def __init__(self, rs: float = 0.5, rb: float | None = None):
        rs = _clamp_unit(rs)
        rb = rs if rb is None else _clamp_unit(rb)

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
    """ICL explicit scheme, a specialisation of :class:`GSSE`.

    Parameters
    ----------
    spectral_radius : float, optional
        Spectral radius, by default 0.5.  It is clamped to ``[0.5, 1]``.
    """

    def __init__(self, spectral_radius: float = 0.5):
        radius = _clamp(spectral_radius, 0.5, 1.0)
        rs = 0.5 * (1.0 / radius - 1.0)

        super().__init__(rs, radius)

        self.spectral_radius = radius


class Tchamwa(Integrator):
    """Tchamwa explicit scheme.

    Parameters
    ----------
    spectral_radius : float, optional
        Spectral radius, by default 0.5.  It is clamped to ``[0, 1]``.
    """

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
    """Explicit Bathe scheme (doi:10.1016/j.compstruc.2013.06.007).

    Each full step is split into a trapezoidal sub-step of length ``p * h``
    and a second sub-step of length ``(1 - p) * h``.

    Parameters
    ----------
    spectral_radius : float, optional
        Spectral radius, by default 0.5.  It is clamped to ``[0, 1]``.
    """

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
    """Implicit Bathe two-step scheme.

    Each full step is split into a trapezoidal sub-step of length
    ``gamma * h`` and a three-point Euler sub-step of length
    ``(1 - gamma) * h``.

    Parameters
    ----------
    spectral_radius : float, optional
        Spectral radius, by default 0.  It is clamped to ``[0, 1]``.
    gamma : float, optional
        Fraction of the step used by the first sub-step, by default 0.5.
        Values outside ``(0, 1)`` are replaced by 0.5, matching suanPan.
    """

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
    """OALTS scheme (doi:10.1002/nme.6188).

    The first step uses the trapezoidal rule; subsequent steps use the
    two-step OALTS recurrence.

    Parameters
    ----------
    spectral_radius : float, optional
        Spectral radius, by default 0.5.  It is clamped to ``[0, 1]``.
    """

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
    """Generalized explicit Runge-Kutta-Nystrom scheme.

    This is a low-level base class: all stage coefficients must be supplied.
    For a prescribed acceleration history only the final velocity and
    displacement weights (``vb*`` and ``ub*``) are used; the remaining
    coefficients describe the underlying two-stage scheme and are stored for
    reference.

    See doi:10.1002/nme.7658.
    """

    def __init__(
        self,
        c1: float,
        c2: float,
        va10: float,
        va20: float,
        va21: float,
        vb0: float,
        vb1: float,
        vb2: float,
        ua10: float,
        ua20: float,
        ua21: float,
        ub0: float,
        ub1: float,
        ub2: float,
        ab0: float,
        ab1: float,
        ab2: float,
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
    """WAT2 scheme, the concrete member of the GERKN family in suanPan.

    Parameters
    ----------
    parameter : float, optional
        Scheme parameter, by default ``1 / 3``.  It is clamped to
        ``[0, 1]`` and mapped to the internal parameter range
        ``[0.3, 0.4]``.
    """

    def __init__(self, parameter: float = 1.0 / 3.0):
        parameter = _clamp_unit(parameter)
        radius = 0.1 * parameter + 0.3

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


def _value(parameters: dict, name: str, default: float) -> float:
    value = parameters.get(name)
    return default if value is None else float(value)


def create_integrator(
    integration_type: IntegrationType | str = IntegrationType.Newmark,
    **parameters,
) -> Integrator:
    """Create a time integrator from its name and scheme parameters.

    Parameters that are not used by the selected scheme are ignored.  Missing
    parameters fall back to the defaults of the corresponding integrator.
    """
    integration_type = IntegrationType(integration_type)

    if integration_type is IntegrationType.Newmark:
        return Newmark(
            _value(parameters, "gamma", 0.5), _value(parameters, "beta", 0.25)
        )

    if integration_type is IntegrationType.GeneralizedAlpha:
        alpha_f = parameters.get("alpha_f")
        alpha_m = parameters.get("alpha_m")
        if alpha_f is not None and alpha_m is not None:
            return GeneralizedAlpha(float(alpha_f), float(alpha_m))
        return GeneralizedAlpha(_value(parameters, "spectral_radius", 0.5))

    if integration_type is IntegrationType.GeneralizedAlphaExplicit:
        return GeneralizedAlphaExplicit(_value(parameters, "spectral_radius", 0.5))

    if integration_type is IntegrationType.GSSSSU0:
        radius = parameters.get("spectral_radius")
        default = 1.0 if radius is None else float(radius)
        return GSSSSU0(
            _value(parameters, "r1", default),
            _value(parameters, "r2", default),
            _value(parameters, "r3", default),
        )

    if integration_type is IntegrationType.GSSSSV0:
        radius = parameters.get("spectral_radius")
        default = 1.0 if radius is None else float(radius)
        return GSSSSV0(
            _value(parameters, "r1", default),
            _value(parameters, "r2", default),
            _value(parameters, "r3", default),
        )

    if integration_type is IntegrationType.GSSSSOptimal:
        return GSSSSOptimal(_value(parameters, "spectral_radius", 0.5))

    if integration_type is IntegrationType.GSSE:
        rb = parameters.get("rb")
        rs = parameters.get("rs")
        if rs is None:
            rs = parameters.get("spectral_radius", 0.5)
        return GSSE(float(rs), None if rb is None else float(rb))

    if integration_type is IntegrationType.ICL:
        return ICL(_value(parameters, "spectral_radius", 0.5))

    if integration_type is IntegrationType.Tchamwa:
        return Tchamwa(_value(parameters, "spectral_radius", 0.5))

    if integration_type is IntegrationType.BatheExplicit:
        return BatheExplicit(_value(parameters, "spectral_radius", 0.5))

    if integration_type is IntegrationType.BatheTwoStep:
        return BatheTwoStep(
            _value(parameters, "spectral_radius", 0.0),
            _value(parameters, "gamma", 0.5),
        )

    if integration_type is IntegrationType.OALTS:
        return OALTS(_value(parameters, "spectral_radius", 0.5))

    if integration_type is IntegrationType.WAT2:
        return WAT2(_value(parameters, "parameter", 1.0 / 3.0))

    raise ValueError(f"Unsupported integration type: {integration_type}.")


# The British spellings are accepted by the suanPan parser as aliases.
GeneralisedAlpha = GeneralizedAlpha
GeneralisedAlphaExplicit = GeneralizedAlphaExplicit
