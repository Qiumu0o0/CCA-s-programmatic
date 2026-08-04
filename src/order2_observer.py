"""Build an order-2 observer from one FSA and two agents.

The complete pipeline is executed in memory:

    G + A1 -> G_A1 -> Obs_A1 -> CC_A(G_A1, Obs_A1)
           -> project original events and relabel for A2
           -> Obs_(A1 <- A2)(G)

Command-line use:

    python src/order2_observer.py G.json A1.json A2.json OUTPUT.json

Use ``--intermediates-dir`` to save every stage for inspection.
Run the script without arguments to select the inputs graphically.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from .CC import concurrent_composition, save_lfsa
    from .fa_agent_to_lfsa import (
        combine_fa_and_agent,
        load_agent,
        load_fa,
    )
    from .observer import construct_observer
    from .relabel_composition import relabel_for_agent
except ImportError:
    from CC import concurrent_composition, save_lfsa  # type: ignore[no-redef]
    from fa_agent_to_lfsa import (  # type: ignore[no-redef]
        combine_fa_and_agent,
        load_agent,
        load_fa,
    )
    from observer import construct_observer  # type: ignore[no-redef]
    from relabel_composition import relabel_for_agent  # type: ignore[no-redef]


Automaton = dict[str, Any]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_ROOT / "data"
MODEL_DIRECTORY = DATA_DIRECTORY / "models"
AGENT_DIRECTORY = DATA_DIRECTORY / "agents"
RESULT_DIRECTORY = DATA_DIRECTORY / "results"


def choose_files_graphically() -> tuple[Path, Path, Path, Path, Path | None]:
    """Ask for FSA, Agent 1, Agent 2, and output paths using a GUI."""

    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except ImportError as error:
        raise RuntimeError(
            "Tkinter is required for graphical mode. Use the four command-line "
            "paths instead."
        ) from error

    root = tk.Tk()
    root.withdraw()
    root.update()

    try:
        messagebox.showinfo(
            "Order-2 Observer",
            "请依次导入以下三个 JSON 文件：\n\n"
            "1. FSA\n"
            "2. Agent 1\n"
            "3. Agent 2",
            parent=root,
        )

        selections: list[Path] = []
        prompts = (
            ("步骤 1/3：请选择 FSA JSON 文件", "FSA", MODEL_DIRECTORY),
            ("步骤 2/3：请选择 Agent 1 JSON 文件", "Agent 1", AGENT_DIRECTORY),
            ("步骤 3/3：请选择 Agent 2 JSON 文件", "Agent 2", AGENT_DIRECTORY),
        )
        for title, label, initial_directory in prompts:
            selected = filedialog.askopenfilename(
                title=title,
                initialdir=initial_directory,
                filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
                parent=root,
            )
            if not selected:
                raise SystemExit(f"已取消：未选择 {label} 文件。")
            selections.append(Path(selected))

        output = filedialog.asksaveasfilename(
            title="请选择最终 Order-2 Observer 的保存位置",
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
            initialfile="order2_observer.json",
            initialdir=RESULT_DIRECTORY,
            parent=root,
        )
        if not output:
            raise SystemExit("已取消：未选择结果保存位置。")

        intermediates_directory: Path | None = None
        if messagebox.askyesno(
            "保存中间结果",
            "是否保存 Pipeline 每一步的中间 JSON 文件？",
            parent=root,
        ):
            selected_directory = filedialog.askdirectory(
                title="请选择中间结果的保存文件夹",
                initialdir=RESULT_DIRECTORY,
                parent=root,
            )
            if not selected_directory:
                raise SystemExit("已取消：未选择中间结果文件夹。")
            intermediates_directory = Path(selected_directory)

        return (
            selections[0],
            selections[1],
            selections[2],
            Path(output),
            intermediates_directory,
        )
    finally:
        root.destroy()


def build_order2_observer(
    automaton: Automaton,
    agent1: Automaton,
    agent2: Automaton,
) -> dict[str, Automaton]:
    """Run the full two-agent pipeline and return all of its stages."""

    agent1_lfsa = combine_fa_and_agent(automaton, agent1)
    agent1_observer = construct_observer(agent1_lfsa)
    composition = concurrent_composition(agent1_lfsa, agent1_observer)

    # A2 labels the original events of G.  In each composition event
    # (e, a), e is the original event and a is A1's observer symbol.
    agent2_view_of_g = combine_fa_and_agent(automaton, agent2)
    agent2_labeled_composition = relabel_for_agent(
        composition,
        agent2_view_of_g,
    )
    order2_observer = construct_observer(agent2_labeled_composition)

    return {
        "agent1_lfsa": agent1_lfsa,
        "agent1_observer": agent1_observer,
        "composition": composition,
        "agent2_labeled_composition": agent2_labeled_composition,
        "order2_observer": order2_observer,
    }


def save_intermediates(stages: dict[str, Automaton], directory: Path) -> None:
    """Save the inspectable stages without duplicating the final output."""

    names = {
        "agent1_lfsa": "01_agent1_lfsa.json",
        "agent1_observer": "02_agent1_observer.json",
        "composition": "03_composition.json",
        "agent2_labeled_composition": "04_agent2_labeled_composition.json",
    }
    for stage, filename in names.items():
        save_lfsa(stages[stage], directory / filename)


def _counts(automaton: Automaton) -> str:
    return (
        f"states={len(automaton['states'])}, "
        f"events={len(automaton['event_labels'])}, "
        f"transitions={len(automaton['transitions'])}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an order-2 observer from an FSA and two agents."
    )
    parser.add_argument("fa", nargs="?", type=Path, help="input FSA JSON")
    parser.add_argument("agent1", nargs="?", type=Path, help="first-agent JSON")
    parser.add_argument("agent2", nargs="?", type=Path, help="second-agent JSON")
    parser.add_argument("output", nargs="?", type=Path, help="final observer JSON")
    parser.add_argument(
        "--intermediates-dir",
        type=Path,
        help="optional directory in which every intermediate LFSA is saved",
    )
    arguments = parser.parse_args()

    paths = (arguments.fa, arguments.agent1, arguments.agent2, arguments.output)
    if all(path is None for path in paths):
        fa_path, agent1_path, agent2_path, output_path, gui_intermediates = (
            choose_files_graphically()
        )
        intermediates_directory = gui_intermediates
    elif all(path is not None for path in paths):
        fa_path, agent1_path, agent2_path, output_path = paths
        intermediates_directory = arguments.intermediates_dir
    else:
        parser.error(
            "provide either no paths for graphical mode or all four paths: "
            "FA AGENT1 AGENT2 OUTPUT"
        )

    # The all-or-none checks above narrow these values to Path instances.
    assert fa_path is not None
    assert agent1_path is not None
    assert agent2_path is not None
    assert output_path is not None

    automaton = load_fa(fa_path)
    agent1 = load_agent(agent1_path)
    agent2 = load_agent(agent2_path)
    stages = build_order2_observer(automaton, agent1, agent2)

    save_lfsa(stages["order2_observer"], output_path)
    if intermediates_directory is not None:
        save_intermediates(stages, intermediates_directory)

    print("Order-2 observer pipeline completed:")
    for name, stage in stages.items():
        print(f"  {name}: {_counts(stage)}")
    print(f"Final observer written to: {output_path.resolve()}")
    if intermediates_directory is not None:
        print(
            "Intermediate stages written to: "
            f"{intermediates_directory.resolve()}"
        )

    if all(path is None for path in paths):
        from tkinter import messagebox

        messagebox.showinfo(
            "Order-2 Observer",
            "Pipeline 运行完成。\n\n"
            f"最终结果已保存至：\n{output_path.resolve()}",
        )


if __name__ == "__main__":
    main()
