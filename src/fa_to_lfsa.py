"""Convert a finite-state automaton into a fully observable LFSA.

Every FA event becomes its own observable label:

    Sigma = E
    ell(e) = e

Interactive use:
    Click the IDE Run button and follow the terminal prompts.

Optional command-line use:
    python src/fa_to_lfsa.py FA.json OUTPUT.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from .CC import PROJECT_ROOT, RESULT_DIRECTORY, save_lfsa
    from .fa_agent_to_lfsa import MODEL_DIRECTORY, _is_plain_fa, load_fa
except ImportError:
    from CC import (  # type: ignore[no-redef]
        PROJECT_ROOT,
        RESULT_DIRECTORY,
        save_lfsa,
    )
    from fa_agent_to_lfsa import (  # type: ignore[no-redef]
        MODEL_DIRECTORY,
        _is_plain_fa,
        load_fa,
    )


def convert_fa_to_lfsa(automaton: dict[str, Any]) -> dict[str, Any]:
    """Add the identity labeling function ell(e) = e to an FA."""

    events = automaton["events"]
    return {
        "states": automaton["states"],
        "event_labels": {event: event for event in events},
        "transitions": automaton["transitions"],
        "initial_states": automaton["initial_states"],
        "observable_labels": set(events),
    }


def choose_files_interactively() -> tuple[Path, Path]:
    """Ask the user to select an FA and name the LFSA result."""

    fa_files = sorted(
        (
            path
            for path in MODEL_DIRECTORY.glob("*.json")
            if _is_plain_fa(path)
        ),
        key=lambda path: path.name,
    )
    if not fa_files:
        raise FileNotFoundError(
            f"No plain FA JSON files were found in {MODEL_DIRECTORY}"
        )

    print("\nSelect a finite-state automaton:")
    for number, path in enumerate(fa_files, start=1):
        print(f"  {number}. {path.relative_to(PROJECT_ROOT)}")

    while True:
        answer = input(f"Enter a number from 1 to {len(fa_files)}: ").strip()
        try:
            selected = int(answer)
        except ValueError:
            print("Please enter a number.")
            continue

        if 1 <= selected <= len(fa_files):
            fa_path = fa_files[selected - 1]
            print(
                f"Selected: {fa_path.relative_to(PROJECT_ROOT)}",
                flush=True,
            )
            break
        print("The selected number is outside the available range.")

    RESULT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    while True:
        result_name = input(
            "\nName the LFSA result [press Enter for identity_lfsa]: "
        ).strip()
        result_name = result_name or "identity_lfsa"

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

    return fa_path, output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert an FA to an LFSA using ell(e) = e."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        metavar="JSON",
        help="FA.json OUTPUT.json",
    )
    arguments = parser.parse_args()

    if not arguments.paths:
        fa_path, output_path = choose_files_interactively()
    elif len(arguments.paths) == 2:
        fa_path, output_path = arguments.paths
    else:
        parser.error("provide either no paths or exactly FA OUTPUT")

    automaton = load_fa(fa_path)
    lfsa = convert_fa_to_lfsa(automaton)
    save_lfsa(lfsa, output_path)

    print(f"\nIdentity-labeled LFSA written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
