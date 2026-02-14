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

from typing import Literal
from pydantic import BaseModel, Field


class AmplitudeEnvelope(BaseModel):
    kind: Literal["constant", "linear", "sinusoidal", "expression"] = "constant"
    # constant
    value: float = 1.0
    # linear
    start: float = 0.0
    end: float = 1.0
    # sinusoidal
    frequency: float = 1.0
    phase: float = 0.0
    # expression (free-text math expression using variable 't')
    expression: str = "1.0"


class HamiltonianTerm(BaseModel):
    pauli: Literal["I", "X", "Y", "Z"] = "X"
    ion: int = 0
    coefficient: float = 1.0
    envelope: AmplitudeEnvelope = Field(default_factory=AmplitudeEnvelope)


class EvolveStep(BaseModel):
    terms: list[HamiltonianTerm] = Field(default_factory=lambda: [HamiltonianTerm()])
    duration: float = 1.0


class AnalogProgramSpec(BaseModel):
    n_ions: int = 4
    steps: list[EvolveStep] = Field(default_factory=lambda: [EvolveStep()])
