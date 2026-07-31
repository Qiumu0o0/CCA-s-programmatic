"""Construct the observer of an LFSA stored as JSON.

The implementation follows Definition 3 in Zhang (2023):

* observer states are subsets of the original state set;
* the initial observer state is the unobservable reach of the original
  initial states;
* a transition under label ``a`` first takes an observable transition
  labeled ``a`` and then takes any number of unobservable transitions.

Run this file with an IDE's "Run Python File" button for interactive use.
Optional command-line use:

    python src/observer.py INPUT.json OUTPUT.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

try:
    from .CC import (
        MODEL_DIRECTORY,
        PROJECT_ROOT,
        RESULT_DIRECTORY,
        load_lfsa,
        save_lfsa,
    )
except ImportError:
    # Supports running this file directly instead of as a package module.
    from CC import (  # type: ignore[no-redef]
        MODEL_DIRECTORY,
        PROJECT_ROOT,
        RESULT_DIRECTORY,
        load_lfsa,
        save_lfsa,
    )


def construct_observer(automaton: dict[str, Any]) -> dict[str, Any]:
    """Construct the nonempty reachable part of the deterministic observer."""

    states = automaton["states"]
    event_labels = automaton["event_labels"]
    transitions = automaton["transitions"]

    outgoing: dict[Any, list[tuple[Any, Any]]] = {
        state: [] for state in states
    }
    for source, event, target in transitions:
        outgoing[source].append((event, target))

    unobservable_events = {
        event for event, label in event_labels.items() if label is None
    }
    observable_labels = {
        label for label in event_labels.values() if label is not None
    }

    def unobservable_reach(start_states: Iterable[Any]) -> tuple[Any, ...]:
        reached = set(start_states)
        pending = list(reached)

        while pending:
            state = pending.pop()
            for event, target in outgoing[state]:
                if event in unobservable_events and target not in reached:
                    reached.add(target)
                    pending.append(target)

        return tuple(sorted(reached, key=repr))

    initial_state = unobservable_reach(automaton["initial_states"])
    observer_states = {initial_state}
    observer_transitions: set[tuple[Any, Any, Any]] = set()
    pending = [initial_state]

    while pending:
        observer_state = pending.pop()
        for label in observable_labels:
            reached_after_label: set[Any] = set()

            for state in observer_state:
                for event, target in outgoing[state]:
                    if event_labels[event] == label:
                        reached_after_label.add(target)

            target_state = unobservable_reach(reached_after_label)
            if not target_state:
                continue

            observer_transitions.add(
                (observer_state, label, target_state)
            )
            if target_state not in observer_states:
                observer_states.add(target_state)
                pending.append(target_state)

    # Observer transition symbols are observable labels themselves.
    observer_event_labels = {
        label: label for label in observable_labels
    }

    return {
        "states": observer_states,
        "event_labels": observer_event_labels,
        "transitions": observer_transitions,
        "initial_states": {initial_state},
        "observable_labels": observable_labels,
    }


def available_lfsa_files() -> list[Path]:
    """List source models and previously generated automata."""

    return sorted(
        [
            *MODEL_DIRECTORY.glob("*.json"),
            *RESULT_DIRECTORY.glob("*.json"),
        ],
        key=lambda path: str(path.relative_to(PROJECT_ROOT)),
    )


def choose_files_interactively() -> tuple[Path, Path]:
    """Ask the user to choose an LFSA and name the observer result."""

    files = available_lfsa_files()
    if not files:
        raise FileNotFoundError(
            "No LFSA JSON files were found under data/models or data/results"
        )

    print("\nSelect the LFSA whose observer will be constructed:")
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
            input_path = files[selected - 1]
            break
        print("The selected number is outside the available range.")

    RESULT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    while True:
        result_name = input(
            "\nName the observer result [press Enter for observer]: "
        ).strip()
        result_name = result_name or "observer"

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

    return input_path, output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construct the observer of an LFSA JSON file."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        metavar="JSON",
        help="INPUT.json OUTPUT.json",
    )
    arguments = parser.parse_args()

    if not arguments.paths:
        input_path, output_path = choose_files_interactively()
    elif len(arguments.paths) == 2:
        input_path, output_path = arguments.paths
    else:
        parser.error("provide either no paths or exactly INPUT OUTPUT")

    automaton = load_lfsa(input_path)
    observer = construct_observer(automaton)
    save_lfsa(observer, output_path)

    print(f"\nObserver written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
