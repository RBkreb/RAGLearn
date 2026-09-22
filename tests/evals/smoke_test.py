"""
Smoke test: run a single QA through the chain then evaluate with DeepEval metrics.

Usage:
    venv/Scripts/python tests/evals/smoke_test.py
"""

import os
import sys
import warnings


def main() -> None:
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", message=".*generation_config.*", category=FutureWarning)
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

    # Ensure cwd is project root so relative data paths resolve.
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(project_root)
    sys.path.insert(0, project_root)
    sys.path.insert(0, os.path.join(project_root, "tests", "evals"))

    from deepeval.dataset import EvaluationDataset
    from deepeval.test_case import LLMTestCase

    from metrics import SINGLE_TURN_NO_TRACING_METRICS
    from src.chain import chain_pipeline

    # ── Load one golden ──
    dataset = EvaluationDataset()
    dataset.add_goldens_from_json_file(file_path="eval_results/.dataset.json")
    golden = dataset.goldens[2]

    # ── Run the chain ──
    print("Running chain...", flush=True)
    chain = chain_pipeline()
    actual_output, retrieval_context = chain.execute(golden.input)

    print(f"Q: {golden.input}")
    print(f"Expected: {golden.expected_output}")
    print(f"Actual:   {actual_output}")
    print(f"Contexts: {len(retrieval_context)} chunks")
    print()

    # ── Evaluate ──
    tc = LLMTestCase(
        input=golden.input,
        actual_output=actual_output,
        expected_output=golden.expected_output,
        retrieval_context=[ctx[:300] for ctx in retrieval_context],
    )

    for m in SINGLE_TURN_NO_TRACING_METRICS:
        name = m.__class__.__name__
        print(f"Measuring {name}...", flush=True)
        m.measure(tc)
        print(f"  {name}: {m.score:.2f}  ->  {m.reason[:100]}")
        print()


if __name__ == "__main__":
    main()
