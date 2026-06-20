import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.graph.music_graph import run_generation_workflow


def evaluate(test_cases_path: str = "src/eval/test_cases.json") -> list[dict]:
    test_cases = json.loads(Path(test_cases_path).read_text(encoding="utf-8"))
    results: list[dict] = []

    for test_case in test_cases:
        state = run_generation_workflow(
            test_case["user_requirement"],
            generator_backend=test_case.get("generator_backend", "mock"),
        )
        missing_fields = [
            field
            for field in test_case["expected_fields"]
            if not state.get(field)
        ]
        results.append(
            {
                "id": test_case["id"],
                "passed": not missing_fields,
                "missing_fields": missing_fields,
                "history_id": state.get("history_id"),
            }
        )

    return results


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
