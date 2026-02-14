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

from oqd_teaching_demo.analog import AnalogProgramSpec, AmplitudeEnvelope, HamiltonianTerm


def make_pauli(name: str) -> dict:
    return {"class_": f"Pauli{name}"}


def make_kron_chain(pauli: str, ion: int, n_ions: int) -> dict:
    operators = []
    for i in range(n_ions):
        if i == ion:
            operators.append(make_pauli(pauli))
        else:
            operators.append(make_pauli("I"))

    if len(operators) == 1:
        return operators[0]

    result = {"class_": "OperatorKron", "op1": operators[0], "op2": operators[1]}
    for i in range(2, len(operators)):
        result = {"class_": "OperatorKron", "op1": result, "op2": operators[i]}
    return result


def make_math_expr(envelope: AmplitudeEnvelope, duration: float) -> dict:
    if envelope.kind == "constant":
        return {"class_": "MathNum", "value": envelope.value}

    elif envelope.kind == "linear":
        # start + (end - start) * (t / duration)
        t_normalized = {
            "class_": "MathDiv",
            "expr1": {"class_": "MathVar", "name": "t"},
            "expr2": {"class_": "MathNum", "value": duration},
        }
        return {
            "class_": "MathAdd",
            "expr1": {"class_": "MathNum", "value": envelope.start},
            "expr2": {
                "class_": "MathMul",
                "expr1": {"class_": "MathNum", "value": envelope.end - envelope.start},
                "expr2": t_normalized,
            },
        }

    elif envelope.kind == "sinusoidal":
        # sin(frequency * t + phase)
        return {
            "class_": "MathFunc",
            "func": "sin",
            "expr": {
                "class_": "MathAdd",
                "expr1": {
                    "class_": "MathMul",
                    "expr1": {"class_": "MathNum", "value": envelope.frequency},
                    "expr2": {"class_": "MathVar", "name": "t"},
                },
                "expr2": {"class_": "MathNum", "value": envelope.phase},
            },
        }

    elif envelope.kind == "expression":
        # For free-text expressions, represent as a string comment alongside a MathNum placeholder.
        # Full parsing would require oqd-core's MathStr parser at runtime.
        return {"class_": "MathNum", "value": 1.0, "_expression": envelope.expression}

    return {"class_": "MathNum", "value": 1.0}


def _build_term_operator(term: HamiltonianTerm, n_ions: int, duration: float) -> dict:
    kron = make_kron_chain(term.pauli, term.ion, n_ions)
    math_expr = make_math_expr(term.envelope, duration)

    coeff = {
        "class_": "MathMul",
        "expr1": {"class_": "MathNum", "value": term.coefficient},
        "expr2": math_expr,
    }

    return {
        "class_": "OperatorScalarMul",
        "op": kron,
        "expr": coeff,
    }


def _combine_terms(term_ops: list[dict]) -> dict:
    if len(term_ops) == 1:
        return term_ops[0]

    result = {"class_": "OperatorAdd", "op1": term_ops[0], "op2": term_ops[1]}
    for i in range(2, len(term_ops)):
        result = {"class_": "OperatorAdd", "op1": result, "op2": term_ops[i]}
    return result


def build_analog_circuit(spec: AnalogProgramSpec) -> dict:
    sequence = []

    for step in spec.steps:
        term_ops = [_build_term_operator(t, spec.n_ions, step.duration) for t in step.terms]
        hamiltonian = _combine_terms(term_ops) if term_ops else make_pauli("I")

        sequence.append({
            "class_": "Evolve",
            "key": "evolve",
            "gate": {
                "class_": "AnalogGate",
                "hamiltonian": hamiltonian,
            },
            "duration": step.duration,
        })

    return {
        "class_": "AnalogCircuit",
        "n_qreg": spec.n_ions,
        "n_qmode": None,
        "sequence": sequence,
    }
