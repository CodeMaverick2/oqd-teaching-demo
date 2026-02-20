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

import json
import threading

from nicegui import ui

from oqd_teaching_demo.analog import (
    AnalogProgramSpec,
    EvolveStep,
    HamiltonianTerm,
    AmplitudeEnvelope,
)
from oqd_teaching_demo.ir_builder import build_analog_circuit
from oqd_teaching_demo.analog_compiler import compile_to_program
from oqd_teaching_demo.gui.programs import (
    preset_rabi_flopping,
    preset_ising,
)


def analog_builder_card(board, stream_ip: str):
    spec = AnalogProgramSpec()

    steps_container = None
    json_output = None
    run_thread = None

    def rebuild_steps_ui():
        nonlocal steps_container
        if steps_container is None:
            return
        steps_container.clear()
        with steps_container:
            _render_ion_chain()
            for si, step in enumerate(spec.steps):
                _render_step(si, step)
            ui.button("+ Add Evolution Step", on_click=add_step).props("flat color=primary")

    def _render_ion_chain():
        with ui.row().classes("items-center gap-1 mb-2"):
            ui.label("Ion Chain:").classes("text-sm font-bold")
            for i in range(spec.n_ions):
                if i > 0:
                    ui.label("\u2014").classes("text-xs text-grey")
                ui.badge(str(i), color="primary").props("rounded")
            ui.number(
                "Ions",
                value=spec.n_ions,
                min=1,
                max=8,
                step=1,
                on_change=lambda e: _set_n_ions(e.value),
            ).classes("w-20 ml-4").props("dense")

    def _set_n_ions(val):
        if val is None:
            return
        spec.n_ions = int(val)
        for step in spec.steps:
            for term in step.terms:
                if term.ion >= spec.n_ions:
                    term.ion = spec.n_ions - 1
        rebuild_steps_ui()

    def _render_step(si, step):
        with ui.card().classes("w-full mb-2"):
            with ui.row().classes("items-center w-full"):
                ui.label(f"Step {si + 1}").classes("text-sm font-bold")
                ui.number(
                    "Duration (s)",
                    value=step.duration,
                    min=0.01,
                    step=0.1,
                    format="%.2f",
                    on_change=lambda e, si=si: _set_duration(si, e.value),
                ).classes("w-32").props("dense")
                ui.space()
                if len(spec.steps) > 1:
                    ui.button(
                        icon="delete",
                        on_click=lambda _, si=si: remove_step(si),
                    ).props("flat round color=negative size=sm")

            for ti, term in enumerate(step.terms):
                _render_term(si, ti, term)

            ui.button(
                "+ Add Term",
                on_click=lambda _, si=si: add_term(si),
            ).props("flat color=primary size=sm")

    def _set_duration(si, val):
        if val is not None and 0 <= si < len(spec.steps):
            spec.steps[si].duration = float(val)

    def _render_term(si, ti, term):
        with ui.row().classes("items-center gap-2 w-full"):
            ui.toggle(
                ["I", "X", "Y", "Z"],
                value=term.pauli,
                on_change=lambda e, si=si, ti=ti: _set_pauli(si, ti, e.value),
            ).props("dense size=sm")

            ui.select(
                list(range(spec.n_ions)),
                value=term.ion,
                label="Ion",
                on_change=lambda e, si=si, ti=ti: _set_ion(si, ti, e.value),
            ).classes("w-20").props("dense")

            ui.number(
                "Coeff",
                value=term.coefficient,
                step=0.1,
                format="%.3f",
                on_change=lambda e, si=si, ti=ti: _set_coeff(si, ti, e.value),
            ).classes("w-28").props("dense")

            ui.select(
                ["constant", "linear", "sinusoidal", "expression"],
                value=term.envelope.kind,
                label="Envelope",
                on_change=lambda e, si=si, ti=ti: _set_envelope_kind(si, ti, e.value),
            ).classes("w-32").props("dense")

            _render_envelope_params(si, ti, term.envelope)

            ui.button(
                icon="close",
                on_click=lambda _, si=si, ti=ti: remove_term(si, ti),
            ).props("flat round color=negative size=sm")

    def _render_envelope_params(si, ti, envelope):
        if envelope.kind == "constant":
            ui.number(
                "Value",
                value=envelope.value,
                step=0.1,
                format="%.3f",
                on_change=lambda e, si=si, ti=ti: _set_env_param(si, ti, "value", e.value),
            ).classes("w-24").props("dense")

        elif envelope.kind == "linear":
            ui.number(
                "Start",
                value=envelope.start,
                step=0.1,
                format="%.2f",
                on_change=lambda e, si=si, ti=ti: _set_env_param(si, ti, "start", e.value),
            ).classes("w-20").props("dense")
            ui.number(
                "End",
                value=envelope.end,
                step=0.1,
                format="%.2f",
                on_change=lambda e, si=si, ti=ti: _set_env_param(si, ti, "end", e.value),
            ).classes("w-20").props("dense")

        elif envelope.kind == "sinusoidal":
            ui.number(
                "Freq",
                value=envelope.frequency,
                step=0.1,
                format="%.2f",
                on_change=lambda e, si=si, ti=ti: _set_env_param(si, ti, "frequency", e.value),
            ).classes("w-20").props("dense")
            ui.number(
                "Phase",
                value=envelope.phase,
                step=0.1,
                format="%.2f",
                on_change=lambda e, si=si, ti=ti: _set_env_param(si, ti, "phase", e.value),
            ).classes("w-20").props("dense")

        elif envelope.kind == "expression":
            ui.input(
                "f(t) =",
                value=envelope.expression,
                on_change=lambda e, si=si, ti=ti: _set_env_param(si, ti, "expression", e.value),
            ).classes("w-40").props("dense")

    def _set_pauli(si, ti, val):
        if val is not None:
            spec.steps[si].terms[ti].pauli = val

    def _set_ion(si, ti, val):
        if val is not None:
            spec.steps[si].terms[ti].ion = int(val)

    def _set_coeff(si, ti, val):
        if val is not None:
            spec.steps[si].terms[ti].coefficient = float(val)

    def _set_envelope_kind(si, ti, val):
        if val is not None:
            spec.steps[si].terms[ti].envelope = AmplitudeEnvelope(kind=val)
            rebuild_steps_ui()

    def _set_env_param(si, ti, param, val):
        if val is not None:
            setattr(spec.steps[si].terms[ti].envelope, param, val)

    def add_step():
        spec.steps.append(EvolveStep())
        rebuild_steps_ui()

    def remove_step(si):
        if len(spec.steps) > 1:
            spec.steps.pop(si)
            rebuild_steps_ui()

    def add_term(si):
        spec.steps[si].terms.append(HamiltonianTerm())
        rebuild_steps_ui()

    def remove_term(si, ti):
        if len(spec.steps[si].terms) > 1:
            spec.steps[si].terms.pop(ti)
            rebuild_steps_ui()

    def load_preset(preset_fn):
        nonlocal spec
        spec = preset_fn()
        rebuild_steps_ui()
        ui.notify("Preset loaded", type="positive")

    def show_ir_json():
        nonlocal json_output
        try:
            circuit = build_analog_circuit(spec)
            text = json.dumps(circuit.model_dump(serialize_as_any=True), indent=2)
            if json_output is not None:
                json_output.set_content(text)
            ui.notify("IR JSON generated", type="positive")
        except Exception as e:
            ui.notify(f"Error generating IR: {e}", type="negative")

    def run_program():
        nonlocal run_thread
        try:
            program = compile_to_program(spec)
            board.device._stop_event.clear()

            def _run():
                board.device.run(program)

            run_thread = threading.Thread(target=_run, daemon=True)
            run_thread.start()
            ui.notify(f"Running program ({len(program)} steps)", type="info")
        except Exception as e:
            ui.notify(f"Error: {e}", type="negative")

    def stop_program():
        board.device.stop()
        ui.notify("Program stopped", type="warning")

    with ui.dialog() as analog_dialog, ui.card().classes("w-full").style("max-width: 900px"):
        ui.label("Analog Program Builder").style(
            "color: #6E93D6; font-size: 200%; font-weight: 300"
        )

        steps_container = ui.column().classes("w-full")
        rebuild_steps_ui()

        ui.separator()

        with ui.row().classes("items-center gap-2"):
            ui.label("Presets:").classes("text-sm font-bold")
            ui.button("Rabi Flopping", on_click=lambda: load_preset(preset_rabi_flopping)).props("flat")
            ui.button("Ising Model", on_click=lambda: load_preset(preset_ising)).props("flat")

        ui.separator()

        with ui.row().classes("items-center gap-2"):
            ui.button("Show IR JSON", on_click=show_ir_json).props("color=primary")
            ui.button("Run Program", icon="play_arrow", on_click=run_program).props("color=positive")
            ui.button("Stop", icon="stop", on_click=stop_program).props("color=negative")

        json_output = ui.code("", language="json").classes("w-full")

        with ui.card().classes("w-full"):
            ui.image(stream_ip)

    return analog_dialog
