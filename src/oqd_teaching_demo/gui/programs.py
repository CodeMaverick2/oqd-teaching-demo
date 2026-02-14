# Copyright 2024-2025 Open Quantum Design

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import numpy as np

from oqd_teaching_demo.program import Program
from oqd_teaching_demo.analog import AnalogProgramSpec, EvolveStep, HamiltonianTerm, AmplitudeEnvelope


def digital_simple():
    n = 10

    red_lasers_intensity = list(
        zip(
            [0, 0.5, 0.75, 0.9, 1.0] * (n // 5),
            [0, 0.5, 0.75, 0.9, 1.0] * (n // 5),
            [0, 0.5, 0.75, 0.9, 1.0] * (n // 5),
            [0, 0.5, 0.75, 0.9, 1.0] * (n // 5),
        )
    )

    program = Program(
        # camera_trigger = (n-1) * [0] + [1],
        red_lasers_intensity=red_lasers_intensity,
        # phonon_com = n * [1],
        dt=0.2,
    )
    return program


def digital_shor():
    repeats = 4
    red_lasers_intensity = list(
        zip(
            [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1] * repeats,
            [1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1] * repeats,
            [1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1] * repeats,
            [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1] * repeats,
        )
    )
    program = Program(red_lasers_intensity=red_lasers_intensity, dt=0.25)
    return program


def digital_random(n: int = 20):
    red_lasers_intensity = list(
        zip(
            list(np.random.randint(0, 2, n)),
            list(np.random.randint(0, 2, n)),
            list(np.random.randint(0, 2, n)),
            list(np.random.randint(0, 2, n)),
        )
    )
    program = Program(red_lasers_intensity=red_lasers_intensity, dt=0.25)
    return program


def analog_ising(n: int = 60):
    t = np.arange(n)
    dt = 0.1
    period = 0.1
    red_lasers_intensity = list(
        zip(
            list((np.sin(t * dt / period + 0) + 1) / 2),
            list((np.sin(t * dt / period + 0) + 1) / 2),
            list((np.sin(t * dt / period + np.pi / 2) + 1) / 2),
            list((np.sin(t * dt / period + np.pi / 2) + 1) / 2),
        )
    )
    program = Program(red_lasers_intensity=red_lasers_intensity, dt=dt)
    return program


def analog_all_to_all(n: int = 60):
    t = np.arange(n)
    dt = 0.1
    period = 0.2
    red_lasers_intensity = list(
        zip(
            list((np.sin(t * dt / period + 0) + 1) / 2),
            list((np.sin(t * dt / period + 0) + 1) / 2),
            list((np.sin(t * dt / period + 0) + 1) / 2),
            list((np.sin(t * dt / period + 0) + 1) / 2),
        )
    )
    program = Program(red_lasers_intensity=red_lasers_intensity, dt=dt)
    return program


def preset_rabi_flopping() -> AnalogProgramSpec:
    return AnalogProgramSpec(
        n_ions=4,
        steps=[
            EvolveStep(
                terms=[
                    HamiltonianTerm(
                        pauli="X",
                        ion=0,
                        coefficient=1.0,
                        envelope=AmplitudeEnvelope(kind="constant", value=1.0),
                    ),
                ],
                duration=2.0,
            ),
        ],
    )


def preset_ising() -> AnalogProgramSpec:
    terms = []
    for i in range(3):
        terms.append(
            HamiltonianTerm(
                pauli="X",
                ion=i,
                coefficient=0.5,
                envelope=AmplitudeEnvelope(
                    kind="sinusoidal", frequency=1.0, phase=0.0
                ),
            )
        )
        terms.append(
            HamiltonianTerm(
                pauli="X",
                ion=i + 1,
                coefficient=0.5,
                envelope=AmplitudeEnvelope(
                    kind="sinusoidal", frequency=1.0, phase=0.0
                ),
            )
        )
    for i in range(4):
        terms.append(
            HamiltonianTerm(
                pauli="Z",
                ion=i,
                coefficient=0.3,
                envelope=AmplitudeEnvelope(kind="constant", value=1.0),
            )
        )

    return AnalogProgramSpec(
        n_ions=4,
        steps=[EvolveStep(terms=terms, duration=3.0)],
    )


def preset_all_to_all() -> AnalogProgramSpec:
    terms = []
    for i in range(4):
        terms.append(
            HamiltonianTerm(
                pauli="X",
                ion=i,
                coefficient=0.5,
                envelope=AmplitudeEnvelope(
                    kind="sinusoidal", frequency=0.5, phase=0.0
                ),
            )
        )

    return AnalogProgramSpec(
        n_ions=4,
        steps=[EvolveStep(terms=terms, duration=6.0)],
    )
