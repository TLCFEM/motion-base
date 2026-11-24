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
import pytest

from mb.record.integrator import (
    GERKN,
    GSSE,
    GSSSSU0,
    GSSSSV0,
    ICL,
    OALTS,
    WAT2,
    BatheExplicit,
    BatheTwoStep,
    GeneralisedAlpha,
    GeneralisedAlphaExplicit,
    GeneralizedAlpha,
    GeneralizedAlphaExplicit,
    GSSSSOptimal,
    Newmark,
    Tchamwa,
)

# (id, factory, expected order for a prescribed smooth acceleration)
INTEGRATORS = [
    ("newmark", lambda: Newmark(), 2),
    ("generalized-alpha", lambda: GeneralizedAlpha(), 1),
    ("generalized-alpha-explicit", lambda: GeneralizedAlphaExplicit(), 1),
    ("gssss-u0", lambda: GSSSSU0(1.0, 1.0, 1.0), 2),
    ("gssss-v0", lambda: GSSSSV0(1.0, 1.0, 1.0), 2),
    ("gssss-optimal", lambda: GSSSSOptimal(), 1),
    ("gsse", lambda: GSSE(), 2),
    ("icl", lambda: ICL(), 2),
    ("tchamwa", lambda: Tchamwa(), 1),
    ("bathe-explicit", lambda: BatheExplicit(), 2),
    ("bathe-two-step", lambda: BatheTwoStep(), 2),
    ("oalts", lambda: OALTS(), 2),
    ("wat2", lambda: WAT2(), 2),
]

IDS = [item[0] for item in INTEGRATORS]
FACTORIES = [item[1] for item in INTEGRATORS]
ORDERS = {item[0]: item[2] for item in INTEGRATORS}


def _exact_response(omega: float, time: np.ndarray):
    return (
        (omega * time - np.sin(omega * time)) / omega**2,
        (1.0 - np.cos(omega * time)) / omega,
    )


@pytest.mark.parametrize("factory", FACTORIES, ids=IDS)
def test_zero_acceleration(factory):
    acceleration = np.zeros(16)
    displacement, velocity = factory().integrate(0.01, acceleration)

    assert displacement.shape == acceleration.shape
    assert velocity.shape == acceleration.shape
    assert displacement == pytest.approx(0.0)
    assert velocity == pytest.approx(0.0)


@pytest.mark.parametrize("factory", FACTORIES, ids=IDS)
def test_integrate_accepts_list(factory):
    displacement, velocity = factory().integrate(0.01, [1.0, 2.0, 3.0, 4.0])

    assert displacement.shape == (4,)
    assert velocity.shape == (4,)
    assert np.all(np.isfinite(displacement))
    assert np.all(np.isfinite(velocity))


# All schemes except Tchamwa are exact for a constant acceleration.  Tchamwa
# intentionally uses a modified displacement update while its velocity is
# still exact.
@pytest.mark.parametrize(
    "factory",
    [factory for name, factory, _ in INTEGRATORS if name != "tchamwa"],
    ids=[name for name, _, _ in INTEGRATORS if name != "tchamwa"],
)
def test_constant_acceleration(factory):
    interval = 0.02
    magnitude = 3.0
    acceleration = np.full(40, magnitude)
    time = interval * np.arange(acceleration.size)

    displacement, velocity = factory().integrate(interval, acceleration)

    assert displacement == pytest.approx(0.5 * magnitude * time**2, abs=1e-12)
    assert velocity == pytest.approx(magnitude * time, abs=1e-12)


def test_tchamwa_constant_acceleration():
    interval = 0.02
    magnitude = 3.0
    acceleration = np.full(10, magnitude)
    time = interval * np.arange(acceleration.size)

    integrator = Tchamwa()
    displacement, velocity = integrator.integrate(interval, acceleration)

    assert velocity == pytest.approx(magnitude * time, abs=1e-12)
    assert displacement[0] == 0.0
    for i in range(1, acceleration.size):
        expected = (
            displacement[i - 1]
            + interval * velocity[i - 1]
            + integrator.phi * interval**2 * acceleration[i - 1]
        )
        assert displacement[i] == pytest.approx(expected, abs=1e-15)


@pytest.mark.parametrize("factory", FACTORIES, ids=IDS)
def test_sinusoidal_convergence(factory, request):
    """Check the expected order of accuracy for a smooth acceleration history."""
    name = request.node.callspec.id
    expected_order = ORDERS[name]
    omega = 2.0 * np.pi

    errors = []
    for interval in (1.0 / 128.0, 1.0 / 256.0):
        time = np.arange(0.0, 1.0 + interval / 2.0, interval)
        acceleration = np.sin(omega * time)
        displacement, velocity = factory().integrate(interval, acceleration)
        exact_displacement, exact_velocity = _exact_response(omega, time)
        errors.append(
            (
                np.max(np.abs(displacement - exact_displacement)),
                np.max(np.abs(velocity - exact_velocity)),
            )
        )

    displacement_order = np.log2(errors[0][0] / errors[1][0])
    velocity_order = np.log2(errors[0][1] / errors[1][1])

    assert displacement_order == pytest.approx(expected_order, abs=0.15)
    assert velocity_order == pytest.approx(expected_order, abs=0.15)


def test_gssss_reduces_to_newmark():
    interval = 0.01
    acceleration = np.sin(np.linspace(0.0, 2.0 * np.pi, 101))

    expected = Newmark().integrate(interval, acceleration)

    for integrator in (
        GSSSSU0(1.0, 1.0, 1.0),
        GSSSSV0(1.0, 1.0, 1.0),
        GSSSSOptimal(1.0),
    ):
        result = integrator.integrate(interval, acceleration)
        assert result[0] == pytest.approx(expected[0])
        assert result[1] == pytest.approx(expected[1])


def test_gsse_reduces_to_newmark():
    interval = 0.01
    acceleration = np.sin(np.linspace(0.0, 2.0 * np.pi, 101))

    integrator = GSSE(0.7, 0.8)
    expected = Newmark(integrator.vb, integrator.ub).integrate(interval, acceleration)
    result = integrator.integrate(interval, acceleration)

    assert result[0] == pytest.approx(expected[0])
    assert result[1] == pytest.approx(expected[1])


def test_parameter_storage_and_clamping():
    alpha = GeneralizedAlpha(0.5)
    assert alpha.alpha_f == pytest.approx(1.0 / 3.0)
    assert alpha.alpha_m == pytest.approx(0.0)
    assert alpha.gamma == pytest.approx(5.0 / 6.0)
    assert alpha.beta == pytest.approx(4.0 / 9.0)

    custom = GeneralizedAlpha(0.4, 0.2)
    assert custom.alpha_f == pytest.approx(0.4)
    assert custom.alpha_m == pytest.approx(0.2)
    assert custom.gamma == pytest.approx(0.5 - 0.2 + 0.4)

    gssss = GSSSSU0(1.5, -0.5, 0.25)
    assert (gssss.r1, gssss.r2, gssss.r3) == pytest.approx((0.0, 0.25, 1.0))
    assert GSSSSV0([0.9, 0.6, 0.3]).r3 == pytest.approx(0.9)

    assert Tchamwa(2.0).spectral_radius == 1.0
    assert Tchamwa(2.0).phi == 1.0
    assert Tchamwa(-1.0).spectral_radius == 0.0
    assert Tchamwa(-1.0).phi == 2.0

    assert BatheTwoStep(0.5, 0.0).gamma == 0.5
    assert BatheTwoStep(0.5, 1.0).gamma == 0.5
    assert BatheTwoStep(0.5, 0.4).gamma == 0.4
    assert ICL(0.2).spectral_radius == 0.5
    assert ICL(1.5).spectral_radius == 1.0


def test_bathe_two_step_single_sample():
    displacement, velocity = BatheTwoStep().integrate(0.01, np.ones(1))

    assert displacement == pytest.approx(0.0)
    assert velocity == pytest.approx(0.0)


@pytest.mark.parametrize("radius", [0.0, 0.2, 0.5, 0.8, 1.0])
def test_bathe_two_step_constant_acceleration_various_radii(radius):
    interval = 0.01
    magnitude = 2.0
    acceleration = np.full(20, magnitude)
    time = interval * np.arange(acceleration.size)

    displacement, velocity = BatheTwoStep(radius).integrate(interval, acceleration)

    assert displacement == pytest.approx(0.5 * magnitude * time**2, abs=1e-12)
    assert velocity == pytest.approx(magnitude * time, abs=1e-12)


@pytest.mark.parametrize("radius", [0.0, 0.2, 0.5, 0.8, 1.0])
def test_oalts_constant_acceleration_various_radii(radius):
    interval = 0.01
    magnitude = 2.0
    acceleration = np.full(20, magnitude)
    time = interval * np.arange(acceleration.size)

    displacement, velocity = OALTS(radius).integrate(interval, acceleration)

    assert displacement == pytest.approx(0.5 * magnitude * time**2, abs=1e-12)
    assert velocity == pytest.approx(magnitude * time, abs=1e-12)


@pytest.mark.parametrize("factory", FACTORIES, ids=IDS)
def test_multidimensional_input_is_flattened(factory):
    acceleration = np.arange(6.0).reshape(2, 3)

    displacement, velocity = factory().integrate(0.01, acceleration)
    expected_displacement, expected_velocity = factory().integrate(
        0.01, acceleration.ravel()
    )

    assert displacement.shape == (6,)
    assert velocity.shape == (6,)
    assert displacement == pytest.approx(expected_displacement)
    assert velocity == pytest.approx(expected_velocity)


def test_gsse_clamps_both_radii():
    integrator = GSSE(2.0, -1.0)

    assert integrator.rs == 1.0
    assert integrator.rb == 0.0


def test_wat2_clamps_parameter_and_maps_to_internal_radius():
    assert WAT2(2.0).parameter == 1.0
    assert WAT2(2.0).radius == pytest.approx(0.4)
    assert WAT2(-1.0).parameter == 0.0
    assert WAT2(-1.0).radius == pytest.approx(0.3)


def test_gssss_accepts_scalar_or_three_radii():
    scalar = GSSSSU0(0.5)
    assert (scalar.r1, scalar.r2, scalar.r3) == pytest.approx((0.5, 0.5, 0.5))

    with pytest.raises(ValueError):
        GSSSSU0([0.2, 0.4])
    with pytest.raises(ValueError):
        GSSSSU0(0.2, 0.4)


def test_gerkn_requires_all_coefficients():
    with pytest.raises(TypeError):
        GERKN()


def test_british_spelling_aliases():
    assert GeneralisedAlpha is GeneralizedAlpha
    assert GeneralisedAlphaExplicit is GeneralizedAlphaExplicit
