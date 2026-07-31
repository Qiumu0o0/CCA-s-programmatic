"""Remove the alphabet and labeling function from an LFSA.

The general conversion is:

    (Q, E, delta, Q0, Sigma, ell) -> (Q, E, delta, Q0)

Events and transitions are preserved exactly. In particular, if the input
is a concurrent composition whose events are pairs, those paired events
remain paired in the resulting FA.

Optional command-line use:
    python src/lfsa_to_fa.py LFSA.json OUTPUT_FA.json
    python src/lfsa_to_fa.py --project-left CC.json OUTPUT_FA.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .CC import PROJECT_ROOT, RESULT_DIRECTORY, load_lfsa
except ImportError:
    from CC import (  # type: ignore[no-redef]
        PROJECT_ROOT,
        RESULT_DIRECTORY,
        load_lfsa,
    )


DATA_DIRECTORY = PROJECT_ROOT / "data"


def remove_labels(automaton: dict[str, Any]) -> dict[str, Any]:
    """Return the underlying FA without changing its events."""

    return {
        "states": automaton["states"],
        "events": set(automaton["event_labels"]),
        "transitions": automaton["transitions"],
        "initial_states": automaton["initial_states"],
    }


def project_left_events(automaton: dict[str, Any]) -> dict[str, Any]:
    """Remove labels and replace every paired event (e1, e2) with e1."""

    projected_events: set[Any] = set()
    projected_transitions: set[tuple[Any, Any, Any]] = set()

    for source, paired_event, target in automaton["transitions"]:
        if not isinstance(paired_event, tuple) or len(paired_event) != 2:
            raise ValueError(
                f"event is not a pair and cannot be projected: {paired_event!r}"
            )

        left_event = paired_event[0]
        if left_event is None:
            raise ValueError(
                "cannot project an event with an empty left component"
            )

        projected_events.add(left_event)
        projected_transitions.add((source, left_event, target))

    return {
        "states": automaton["states"],
        "events": projected_events,
        "transitions": projected_transitions,
        "initial_states": automaton["initial_states"],
    }


def _json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _sort_key(value: Any) -> str:
    return json.dumps(_json_value(value), ensure_ascii=False, sort_keys=True)


def save_fa(automaton: dict[str, Any], path: Path) -> None:
    """Save a plain FA without an alphabet or labeling function."""

    data = {
        "automaton_type": "FSA",
        "states": [
            _json_value(state)
            for state in sorted(automaton["states"], key=_sort_key)
        ],
        "events": [
            _json_value(event)
            for event in sorted(automaton["events"], key=_sort_key)
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
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def _is_lfsa_file(path: Path) -> bool:
    """Return whether a JSON file uses the LFSA event-label structure."""

    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, json.JSONDecodeError):
        return False

    required = {
        "states",
        "events",
        "transitions",
        "initial_states",
        "observable_labels",
    }
    events = data.get("events")
    return (
        required <= data.keys()
        and isinstance(events, list)
        and all(
            isinstance(entry, dict)
            and "event" in entry
            and "label" in entry
            for entry in events
        )
    )


def _has_paired_events(path: Path) -> bool:
    """Return whether every event in an LFSA JSON file is a pair."""

    with path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    events = data["events"]
    return bool(events) and all(
        isinstance(entry["event"], list) and len(entry["event"]) == 2
        for entry in events
    )


def choose_files_interactively() -> tuple[Path, Path, bool]:
    """Ask the user to select an LFSA and name the resulting FA."""

    lfsa_files = sorted(
        (
            path
            for path in DATA_DIRECTORY.rglob("*.json")
            if _is_lfsa_file(path)
        ),
        key=lambda path: str(path.relative_to(PROJECT_ROOT)),
    )
    if not lfsa_files:
        raise FileNotFoundError("No LFSA JSON files were found under data")

    print("\nSelect a labeled finite-state automaton:")
    for number, path in enumerate(lfsa_files, start=1):
        print(f"  {number}. {path.relative_to(PROJECT_ROOT)}")

    while True:
        answer = input(f"Enter a number from 1 to {len(lfsa_files)}: ").strip()
        try:
            selected = int(answer)
        except ValueError:
            print("Please enter a number.")
            continue

        if 1 <= selected <= len(lfsa_files):
            input_path = lfsa_files[selected - 1]
            print(
                f"Selected: {input_path.relative_to(PROJECT_ROOT)}",
                flush=True,
            )
            break
        print("The selected number is outside the available range.")

    project_left = False
    if _has_paired_events(input_path):
        while True:
            answer = input(
                "\nThe selected LFSA has paired events. "
                "Project (e1, e2) to e1? [y/N]: "
            ).strip().lower()
            if answer in {"", "n", "no"}:
                break
            if answer in {"y", "yes"}:
                project_left = True
                break
            print("Please enter y or n.")

    RESULT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    while True:
        result_name = input(
            "\nName the FA result [press Enter for underlying_fa]: "
        ).strip()
        result_name = result_name or "underlying_fa"

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

    return input_path, output_path, project_left


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove labels from an LFSA to obtain its underlying FA."
    )
    parser.add_argument(
        "--project-left",
        action="store_true",
        help="replace each paired event (e1, e2) with its left event e1",
    )
    parser.add_argument("paths", nargs="*", type=Path, metavar="JSON")
    arguments = parser.parse_args()

    if not arguments.paths:
        input_path, output_path, project_left = choose_files_interactively()
    elif len(arguments.paths) == 2:
        input_path, output_path = arguments.paths
        project_left = arguments.project_left
    else:
        parser.error("provide either no paths or exactly LFSA OUTPUT_FA")

    lfsa = load_lfsa(input_path)
    automaton = (
        project_left_events(lfsa)
        if project_left
        else remove_labels(lfsa)
    )
    save_fa(automaton, output_path)

    operation = "Projected FA" if project_left else "Underlying FA"
    print(f"\n{operation} written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
