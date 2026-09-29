"""Run the 20 Phase 1 test requests against your local Ollama model.

Run from the backend folder:
    python scripts/nl_eval.py                         # default model (OLLAMA_MODEL or qwen2.5:32b)
    python scripts/nl_eval.py --model qwen2.5:14b     # compare another model
    python scripts/nl_eval.py --only en01 fr05 -v     # re-run specific cases, show parsed JSON
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import date, datetime
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # make "app" importable

from app.nl_search.evaluate import compare
from app.nl_search.parser import OLLAMA_MODEL, OLLAMA_URL, OllamaClient, ParseError, parse_request

CASES = Path(__file__).resolve().parents[1] / "tests" / "nl_search" / "cases.yaml"
RESULTS = Path(__file__).resolve().parents[1] / "nl_eval_results"
PASS_MARK = 18


def check_ollama(url: str, model: str) -> None:
    try:
        tags = httpx.get(f"{url}/api/tags", timeout=5).json()
    except httpx.HTTPError as exc:
        sys.exit(f"Cannot reach Ollama at {url} ({exc}). Is 'ollama serve' running?")
    names = {m["name"] for m in tags.get("models", [])}
    if model not in names and f"{model}:latest" not in names:
        sys.exit(f"Model '{model}' not found. Run: ollama pull {model}\nInstalled: {sorted(names)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=OLLAMA_MODEL)
    ap.add_argument("--url", default=OLLAMA_URL)
    ap.add_argument("--only", nargs="*", help="case ids to run")
    ap.add_argument("-v", "--verbose", action="store_true", help="print parsed JSON for every case")
    args = ap.parse_args()

    suite = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    today = date.fromisoformat(suite["today"])
    cases = [c for c in suite["cases"] if not args.only or c["id"] in args.only]

    check_ollama(args.url, args.model)
    client = OllamaClient(model=args.model, url=args.url)
    print(f"Model: {args.model}   Cases: {len(cases)}   Fixed 'today': {today}\n")

    rows, passed, times = [], 0, []
    for case in cases:
        try:
            result = parse_request(case["text"], client=client, today=today,
                                   home_location=suite["home_location"])
            errors = compare(result.request, case["expect"])
            times.append(result.seconds)
            parsed = json.loads(result.request.model_dump_json(exclude_none=True))
            attempts, secs = result.attempts, result.seconds
        except ParseError as exc:
            errors, parsed, attempts, secs = [str(exc)], None, 2, 0.0

        ok = not errors
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {case['id']}  {secs:5.1f}s  tries={attempts}  {case['text'][:60]}")
        for err in errors:
            print(f"        - {err}")
        if args.verbose and parsed:
            print("        " + json.dumps(parsed, ensure_ascii=False))
        rows.append({"id": case["id"], "pass": ok, "errors": errors, "seconds": round(secs, 2),
                     "attempts": attempts, "parsed": parsed})

    total = len(cases)
    median = statistics.median(times) if times else 0
    print(f"\nScore: {passed}/{total}   Median time: {median:.1f}s")
    if total == 20:
        print("RESULT: PASS - Phase 1 done" if passed >= PASS_MARK
              else f"RESULT: below target ({PASS_MARK}/20) - review the failures above")

    RESULTS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = RESULTS / f"eval-{args.model.replace(':', '_').replace('/', '_')}-{stamp}.json"
    out.write_text(json.dumps({"model": args.model, "score": passed, "total": total,
                               "median_seconds": median, "cases": rows},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
