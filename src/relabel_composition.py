"""Project a composition onto its left events and apply another agent's labels.

This implements the step shown on slide 35:

    (e1, e2) -> e1, then ell1 -> ell2

Optional command-line use:
    python src/relabel_composition.py COMPOSITION.json AGENT_VIEW.json OUTPUT.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from .CC import load_lfsa, save_lfsa
except ImportError:
    from CC import load_lfsa, save_lfsa  # type: ignore[no-redef]


def relabel_for_agent(
    composition: dict[str, Any],
    agent_view: dict[str, Any],
) -> dict[str, Any]:
    """Project paired events to the left event and apply agent_view labels."""

    projected_transitions: set[tuple[Any, Any, Any]] = set()
    used_events: set[Any] = set()

    for source, paired_event, target in composition["transitions"]:
        if not isinstance(paired_event, tuple) or len(paired_event) != 2:
            raise ValueError(
                f"composition event is not a pair: {paired_event!r}"
            )

        left_event = paired_event[0]
        if left_event is None:
            raise ValueError(
                "cannot project an event whose left component is empty"
            )
        if left_event not in agent_view["event_labels"]:
            raise ValueError(
                f"agent view has no label for left event {left_event!r}"
            )

        used_events.add(left_event)
        projected_transitions.add((source, left_event, target))

    return {
        "states": composition["states"],
        "event_labels": {
            event: agent_view["event_labels"][event]
            for event in used_events
        },
        "transitions": projected_transitions,
        "initial_states": composition["initial_states"],
        "observable_labels": agent_view["observable_labels"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Project a composition and apply another agent's labels."
    )
    parser.add_argument("composition", type=Path)
    parser.add_argument("agent_view", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()

    composition = load_lfsa(arguments.composition)
    agent_view = load_lfsa(arguments.agent_view)
    result = relabel_for_agent(composition, agent_view)
    save_lfsa(result, arguments.output)

    print(f"Relabeled composition written to: {arguments.output.resolve()}")


if __name__ == "__main__":
    main()
