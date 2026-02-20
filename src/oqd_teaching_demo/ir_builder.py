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

from functools import reduce

from oqd_core.interface.analog.operation import AnalogCircuit, AnalogGate
from oqd_core.interface.analog.operator import (
    PauliI,
    PauliX,
    PauliY,
    PauliZ,
)
from oqd_core.interface.math import MathNum, MathVar, MathFunc, MathMul, MathAdd, MathDiv, MathStr

from oqd_teaching_demo.analog import AnalogProgramSpec, AmplitudeEnvelope, HamiltonianTerm

PAULI_MAP = {
    "I": PauliI,
    "X": PauliX,
    "Y": PauliY,
    "Z": PauliZ,
}


def _make_kron_chain(pauli_name, ion, n_ions):
    operators = []
    for i in range(n_ions):
        if i == ion:
            operators.append(PAULI_MAP[pauli_name]())
        else:
            operators.append(PauliI())

    return reduce(lambda a, b: a @ b, operators)


def _make_math_expr(envelope, duration):
    if envelope.kind == "constant":
        return MathNum(value=envelope.value)

    elif envelope.kind == "linear":
        # start + (end - start) * (t / duration)
        t = MathVar(name="t")
        t_normalized = MathDiv(expr1=t, expr2=MathNum(value=duration))
        slope = MathNum(value=envelope.end - envelope.start)
        return MathAdd(
            expr1=MathNum(value=envelope.start),
            expr2=MathMul(expr1=slope, expr2=t_normalized),
        )

    elif envelope.kind == "sinusoidal":
        # sin(frequency * t + phase)
        t = MathVar(name="t")
        inner = MathAdd(
            expr1=MathMul(expr1=MathNum(value=envelope.frequency), expr2=t),
            expr2=MathNum(value=envelope.phase),
        )
        return MathFunc(func="sin", expr=inner)

    elif envelope.kind == "expression":
        return MathStr(string=envelope.expression)

    return MathNum(value=1.0)


def _build_term_operator(term, n_ions, duration):
    kron = _make_kron_chain(term.pauli, term.ion, n_ions)
    math_expr = _make_math_expr(term.envelope, duration)
    coeff_expr = MathMul(expr1=MathNum(value=term.coefficient), expr2=math_expr)
    return coeff_expr * kron


def _combine_terms(term_ops):
    return reduce(lambda a, b: a + b, term_ops)


def build_analog_circuit(spec):
    circuit = AnalogCircuit()

    for step in spec.steps:
        term_ops = [_build_term_operator(t, spec.n_ions, step.duration) for t in step.terms]
        hamiltonian = _combine_terms(term_ops) if term_ops else PauliI()

        gate = AnalogGate(hamiltonian=hamiltonian)
        circuit.evolve(gate=gate, duration=step.duration)

    circuit.measure()

    return circuit
