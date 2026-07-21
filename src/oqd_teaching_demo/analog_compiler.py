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

import math

import numpy as np

from oqd_teaching_demo.analog import AnalogProgramSpec, AmplitudeEnvelope
from oqd_teaching_demo.program import Program

SAFE_MATH_NAMESPACE = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
    "abs": abs,
    "pi": math.pi,
    "e": math.e,
}


def evaluate_envelope(envelope: AmplitudeEnvelope, t: float, duration: float) -> float:
    if envelope.kind == "constant":
        return envelope.value

    elif envelope.kind == "linear":
        if duration > 0:
            frac = t / duration
        else:
            frac = 1.0
        return envelope.start + (envelope.end - envelope.start) * frac

    elif envelope.kind == "sinusoidal":
        return math.sin(envelope.frequency * t + envelope.phase)

    elif envelope.kind == "expression":
        namespace = {**SAFE_MATH_NAMESPACE, "t": t}
        try:
            return float(eval(envelope.expression, {"__builtins__": {}}, namespace))
        except Exception:
            return 0.0

    return 1.0


def compile_to_program(spec: AnalogProgramSpec, dt: float = 0.1) -> Program:
    all_intensities = []

    for step in spec.steps:
        n_steps = max(1, int(step.duration / dt))
        t_array = np.linspace(0, step.duration, n_steps, endpoint=False)

        for t in t_array:
            ion_intensity = [0.0] * spec.n_ions
            for term in step.terms:
                if term.pauli == "I":
                    continue
                amp = abs(term.coefficient * evaluate_envelope(term.envelope, t, step.duration))
                idx = min(term.ion, spec.n_ions - 1)
                ion_intensity[idx] += amp

            ion_intensity = [max(0.0, min(1.0, v)) for v in ion_intensity]
            all_intensities.append(ion_intensity)

    if not all_intensities:
        all_intensities = [[0.0] * spec.n_ions]

    return Program(red_lasers_intensity=all_intensities, dt=dt)
