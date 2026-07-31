"""Concurrent composition of two LFSAs stored as JSON.

When this file is run directly without arguments, it interactively asks
the user to select the left input, right input, and output JSON files.

Optional command-line use:
    python src/CC.py LEFT.json RIGHT.json OUTPUT.json
"""

from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIRECTORY = PROJECT_ROOT / "data" / "models"
RESULT_DIRECTORY = PROJECT_ROOT / "data" / "results"


def _freeze(value: Any) -> Any:
    """Convert JSON arrays to tuples so they can be used in sets."""

    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _json_value(value: Any) -> Any:
    """Convert internal tuples back to JSON arrays."""

    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _sort_key(value: Any) -> str:
    return json.dumps(_json_value(value), ensure_ascii=False, sort_keys=True)


def load_lfsa(path: Path) -> dict[str, Any]:
    """Load and validate one LFSA JSON file."""

    with path.open("r", encoding="utf-8") as stream:
        raw = json.load(stream)

    required = {
        "states",
        "events",
        "transitions",
        "initial_states",
        "observable_labels",
    }
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"{path} is missing fields: {sorted(missing)}")

    states = {_freeze(state) for state in raw["states"]}
    initial_states = {_freeze(state) for state in raw["initial_states"]}
    observable_labels = {_freeze(label) for label in raw["observable_labels"]}

    if not states:
        raise ValueError(f"{path}: states must not be empty")
    if not initial_states:
        raise ValueError(f"{path}: initial_states must not be empty")
    if not initial_states <= states:
        raise ValueError(f"{path}: initial_states contains an unknown state")

    event_labels: dict[Any, Any] = {}
    for entry in raw["events"]:
        event = _freeze(entry["event"])
        label = _freeze(entry["label"])
        if event in event_labels:
            raise ValueError(f"{path}: duplicate event {event!r}")
        if label is not None and label not in observable_labels:
            raise ValueError(
                f"{path}: event {event!r} has label outside observable_labels"
            )
        event_labels[event] = label

    transitions: set[tuple[Any, Any, Any]] = set()
    for entry in raw["transitions"]:
        source = _freeze(entry["source"])
        event = _freeze(entry["event"])
        target = _freeze(entry["target"])
        if source not in states or target not in states:
            raise ValueError(f"{path}: transition contains an unknown state")
        if event not in event_labels:
            raise ValueError(f"{path}: transition contains unknown event {event!r}")
        transitions.add((source, event, target))

    return {
        "states": states,
        "event_labels": event_labels,
        "transitions": transitions,
        "initial_states": initial_states,
        "observable_labels": observable_labels,
    }


def concurrent_composition(
    left: dict[str, Any], right: dict[str, Any]
) -> dict[str, Any]:
    """Construct CCA(left, right) according to Definition 2."""

    if left["observable_labels"] != right["observable_labels"]:
        raise ValueError(
            "The two LFSAs must have the same observable_labels alphabet"
        )

    states = set(product(left["states"], right["states"]))
    initial_states = set(
        product(left["initial_states"], right["initial_states"])
    )

    left_labels = left["event_labels"]
    right_labels = right["event_labels"]
    left_observable = {
        event: label for event, label in left_labels.items() if label is not None
    }
    right_observable = {
        event: label for event, label in right_labels.items() if label is not None
    }
    left_unobservable = {
        event for event, label in left_labels.items() if label is None
    }
    right_unobservable = {
        event for event, label in right_labels.items() if label is None
    }

    event_labels: dict[tuple[Any, Any], Any] = {}

    for left_event, left_label in left_observable.items():
        for right_event, right_label in right_observable.items():
            if left_label == right_label:
                event_labels[(left_event, right_event)] = left_label

    for event in left_unobservable:
        event_labels[(event, None)] = None
    for event in right_unobservable:
        event_labels[(None, event)] = None

    left_outgoing: dict[Any, list[tuple[Any, Any]]] = {
        state: [] for state in left["states"]
    }
    right_outgoing: dict[Any, list[tuple[Any, Any]]] = {
        state: [] for state in right["states"]
    }

    for source, event, target in left["transitions"]:
        left_outgoing[source].append((event, target))
    for source, event, target in right["transitions"]:
        right_outgoing[source].append((event, target))

    transitions: set[tuple[Any, Any, Any]] = set()

    for left_state, right_state in states:
        # Observable transitions synchronize when their labels are equal.
        for left_event, left_target in left_outgoing[left_state]:
            left_label = left_labels[left_event]
            if left_label is None:
                continue
            for right_event, right_target in right_outgoing[right_state]:
                if right_labels[right_event] == left_label:
                    transitions.add(
                        (
                            (left_state, right_state),
                            (left_event, right_event),
                            (left_target, right_target),
                        )
                    )

        # An unobservable transition of the left LFSA moves only the left side.
        for left_event, left_target in left_outgoing[left_state]:
            if left_event in left_unobservable:
                transitions.add(
                    (
                        (left_state, right_state),
                        (left_event, None),
                        (left_target, right_state),
                    )
                )

        # An unobservable transition of the right LFSA moves only the right side.
        for right_event, right_target in right_outgoing[right_state]:
            if right_event in right_unobservable:
                transitions.add(
                    (
                        (left_state, right_state),
                        (None, right_event),
                        (left_state, right_target),
                    )
                )

    return {
        "states": states,
        "event_labels": event_labels,
        "transitions": transitions,
        "initial_states": initial_states,
        "observable_labels": left["observable_labels"],
    }


def save_lfsa(automaton: dict[str, Any], path: Path) -> None:
    """Write a concurrent-composition LFSA to JSON."""

    data = {
        "states": [
            _json_value(state)
            for state in sorted(automaton["states"], key=_sort_key)
        ],
        "events": [
            {
                "event": _json_value(event),
                "label": _json_value(automaton["event_labels"][event]),
            }
            for event in sorted(automaton["event_labels"], key=_sort_key)
        ],
        "transitions": [
            {
                "source": _json_value(source),
                "event": _json_value(event),
                "target": _json_value(target),
            }
            for source, event, target in sorted(
                automaton["transitions"], key=_sort_key
            )
        ],
        "initial_states": [
            _json_value(state)
            for state in sorted(automaton["initial_states"], key=_sort_key)
        ],
        "observable_labels": [
            _json_value(label)
            for label in sorted(automaton["observable_labels"], key=_sort_key)
        ],
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def select_input_file(side: str, available_files: list[Path]) -> Path:
    """Ask the user to select one LFSA JSON file."""

    print(f"\nSelect the {side} LFSA:")
    for number, path in enumerate(available_files, start=1):
        print(f"  {number}. {path.relative_to(PROJECT_ROOT)}")

    while True:
        answer = input(f"Enter a number from 1 to {len(available_files)}: ").strip()
        try:
            selected = int(answer)
        except ValueError:
            print("Please enter a number.")
            continue

        if 1 <= selected <= len(available_files):
            return available_files[selected - 1]
        print("The selected number is outside the available range.")


def choose_files_interactively() -> tuple[Path, Path, Path]:
    """Choose two model files and a destination when run by an IDE button."""

    available_files = sorted(
        [
            *MODEL_DIRECTORY.glob("*.json"),
            *RESULT_DIRECTORY.glob("*.json"),
        ],
        key=lambda path: str(path.relative_to(PROJECT_ROOT)),
    )
    if not available_files:
        raise FileNotFoundError(
            "No LFSA JSON files were found under data/models or data/results"
        )

    left = select_input_file("left", available_files)
    right = select_input_file("right", available_files)

    RESULT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    while True:
        result_name = input(
            "\nName the concurrent-composition result "
            "[press Enter for CCA]: "
        ).strip()
        result_name = result_name or "CCA"

        if Path(result_name).name != result_name:
            print("Please enter a file name only, without a folder path.")
            continue

        if result_name.lower().endswith(".json"):
            result_name = result_name[:-5]
        if not result_name:
            print("The result name must not be empty.")
            continue

        output = RESULT_DIRECTORY / f"{result_name}.json"
        break

    return left, right, output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construct the concurrent composition of two LFSA JSON files."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        metavar="JSON",
        help="LEFT.json RIGHT.json OUTPUT.json",
    )
    arguments = parser.parse_args()

    if not arguments.paths:
        left_path, right_path, output_path = choose_files_interactively()
    elif len(arguments.paths) == 3:
        left_path, right_path, output_path = arguments.paths
    else:
        parser.error("provide either no paths or exactly LEFT RIGHT OUTPUT")

    left = load_lfsa(left_path)
    right = load_lfsa(right_path)
    result = concurrent_composition(left, right)
    save_lfsa(result, output_path)

    print(f"\nConcurrent composition written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
