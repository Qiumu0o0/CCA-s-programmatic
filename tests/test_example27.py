import json
from pathlib import Path

from src.CC import save_lfsa
from src.fa_agent_to_lfsa import load_agent, load_fa
from src.order2_observer import build_order2_observer


ROOT = Path(__file__).resolve().parents[1]


def test_example27_matches_expected_output(tmp_path: Path) -> None:
    automaton = load_fa(ROOT / "data/models/Example27_G.json")
    agent1 = load_agent(ROOT / "data/agents/Example27_A1.json")
    agent2 = load_agent(ROOT / "data/agents/Example27_A2.json")

    stages = build_order2_observer(automaton, agent1, agent2)
    actual_path = tmp_path / "order2_observer.json"
    save_lfsa(stages["order2_observer"], actual_path)

    expected_path = ROOT / "data/results/Example27_order2_observer.json"
    with actual_path.open(encoding="utf-8") as stream:
        actual = json.load(stream)
    with expected_path.open(encoding="utf-8") as stream:
        expected = json.load(stream)

    assert actual == expected
