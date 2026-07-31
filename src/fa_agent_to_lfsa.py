"""Combine a finite-state automaton and an agent to produce an LFSA.

Interactive use:
    Click an IDE's "Run Python File" button and follow the prompts.

Optional command-line use:
    python src/fa_agent_to_lfsa.py FA.json AGENT.json OUTPUT.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .CC import PROJECT_ROOT, RESULT_DIRECTORY, save_lfsa
except ImportError:
    from CC import (  # type: ignore[no-redef]
        PROJECT_ROOT,
        RESULT_DIRECTORY,
        save_lfsa,
    )


MODEL_DIRECTORY = PROJECT_ROOT / "data" / "models"
AGENT_DIRECTORY = PROJECT_ROOT / "data" / "agents"
DATA_DIRECTORY = PROJECT_ROOT / "data"


def _freeze(value: Any) -> Any:
    """Convert JSON arrays to hashable tuples."""

    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def load_fa(path: Path) -> dict[str, Any]:
    """Load and validate a plain finite-state automaton."""

    with path.open("r", encoding="utf-8") as stream:
        raw = json.load(stream)

    required = {"states", "events", "transitions", "initial_states"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"{path} is missing FA fields: {sorted(missing)}")

    states = {_freeze(state) for state in raw["states"]}
    events = {
        _freeze(
            event_entry["event"]
            if isinstance(event_entry, dict)
            else event_entry
        )
        for event_entry in raw["events"]
    }
    initial_states = {_freeze(state) for state in raw["initial_states"]}

    if not states:
        raise ValueError(f"{path}: states must not be empty")
    if not initial_states:
        raise ValueError(f"{path}: initial_states must not be empty")
    if not initial_states <= states:
        raise ValueError(f"{path}: initial_states contains an unknown state")

    transitions: set[tuple[Any, Any, Any]] = set()
    for entry in raw["transitions"]:
        source = _freeze(entry["source"])
        event = _freeze(entry["event"])
        target = _freeze(entry["target"])

        if source not in states or target not in states:
            raise ValueError(f"{path}: transition contains an unknown state")
        if event not in events:
            raise ValueError(
                f"{path}: transition contains unknown event {event!r}"
            )
        transitions.add((source, event, target))

    return {
        "states": states,
        "events": events,
        "transitions": transitions,
        "initial_states": initial_states,
    }


def load_agent(path: Path) -> dict[str, Any]:
    """Load and validate an agent (events, alphabet, label function)."""

    with path.open("r", encoding="utf-8") as stream:
        raw = json.load(stream)

    required = {"events", "alphabet", "label_function"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"{path} is missing agent fields: {sorted(missing)}")

    events = {_freeze(event) for event in raw["events"]}
    alphabet = {_freeze(label) for label in raw["alphabet"]}
    label_function = {
        _freeze(event): _freeze(label)
        for event, label in raw["label_function"].items()
    }

    if set(label_function) != events:
        missing_labels = events - set(label_function)
        unknown_events = set(label_function) - events
        raise ValueError(
            f"{path}: label_function must define exactly the agent events; "
            f"missing={sorted(missing_labels, key=repr)}, "
            f"unknown={sorted(unknown_events, key=repr)}"
        )

    labels_outside_alphabet = set(label_function.values()) - alphabet
    if labels_outside_alphabet:
        raise ValueError(
            f"{path}: labels outside alphabet: "
            f"{sorted(labels_outside_alphabet, key=repr)}"
        )

    return {
        "name": raw.get("agent"),
        "events": events,
        "alphabet": alphabet,
        "label_function": label_function,
    }


def combine_fa_and_agent(
    automaton: dict[str, Any],
    agent: dict[str, Any],
) -> dict[str, Any]:
    """Return the LFSA representing the agent's view of the FA."""

    unknown_agent_events = agent["events"] - automaton["events"]
    if unknown_agent_events:
        raise ValueError(
            "agent contains events outside the FA: "
            f"{sorted(unknown_agent_events, key=repr)}"
        )

    event_labels = {
        event: agent["label_function"].get(event)
        for event in automaton["events"]
    }

    return {
        "states": automaton["states"],
        "event_labels": event_labels,
        "transitions": automaton["transitions"],
        "initial_states": automaton["initial_states"],
        "observable_labels": agent["alphabet"],
    }


def _is_plain_fa(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
        return (
            data.get("automaton_type") == "FSA"
            or (
                isinstance(data.get("events"), list)
                and all(
                    not isinstance(event, dict)
                    for event in data["events"]
                )
            )
        )
    except (OSError, json.JSONDecodeError):
        return False


def select_file(title: str, files: list[Path]) -> Path:
    """Display a numbered file menu and return the selected path."""

    if not files:
        raise FileNotFoundError(f"No files are available for {title}")

    print(f"\nSelect {title}:")
    for number, path in enumerate(files, start=1):
        print(f"  {number}. {path.relative_to(PROJECT_ROOT)}")

    while True:
        answer = input(f"Enter a number from 1 to {len(files)}: ").strip()
        try:
            selected = int(answer)
        except ValueError:
            print("Please enter a number.")
            continue

        if 1 <= selected <= len(files):
            selected_path = files[selected - 1]
            print(
                f"Selected: {selected_path.relative_to(PROJECT_ROOT)}",
                flush=True,
            )
            return selected_path
        print("The selected number is outside the available range.")


def choose_files_interactively() -> tuple[Path, Path, Path]:
    """Ask the user to select the FA, agent, and result name."""

    fa_files = sorted(
        (
            path
            for path in DATA_DIRECTORY.rglob("*.json")
            if _is_plain_fa(path)
        ),
        key=lambda path: str(path.relative_to(PROJECT_ROOT)),
    )
    agent_files = sorted(
        AGENT_DIRECTORY.glob("*.json"),
        key=lambda path: path.name,
    )

    fa_path = select_file("a finite-state automaton", fa_files)
    agent_path = select_file("an agent", agent_files)

    RESULT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    while True:
        result_name = input(
            "\nName the LFSA result [press Enter for agent_view]: "
        ).strip()
        result_name = result_name or "agent_view"

        if Path(result_name).name != result_name:
            print("Please enter a file name only, without a folder path.")
            continue

        if result_name.lower().endswith(".json"):
            result_name = result_name[:-5]
        if not result_name:
            print("The result name must not be empty.")
            continue

        output_path = RESULT_DIRECTORY / f"{result_name}.json"
        break

    return fa_path, agent_path, output_path


def main() -> None:
    # Ensure that prompts and progress messages appear immediately in IDE
    # terminals that would otherwise buffer standard output.
    try:
        import sys

        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, OSError):
        pass

    parser = argparse.ArgumentParser(
        description="Combine an FA and an agent to produce an LFSA."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        metavar="JSON",
        help="FA.json AGENT.json OUTPUT.json",
    )
    arguments = parser.parse_args()

    if not arguments.paths:
        fa_path, agent_path, output_path = choose_files_interactively()
    elif len(arguments.paths) == 3:
        fa_path, agent_path, output_path = arguments.paths
    else:
        parser.error("provide either no paths or exactly FA AGENT OUTPUT")

    automaton = load_fa(fa_path)
    agent = load_agent(agent_path)
    lfsa = combine_fa_and_agent(automaton, agent)
    save_lfsa(lfsa, output_path)

    print(f"\nLFSA written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
