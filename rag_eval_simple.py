"""
ragas evaluation: 200 QA pairs from English dataset, with new RFF rerank.
"""
import json, time, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'E:\Uagent')

from src.chain import chain_pipeline
from src.config import LlmConfig

N_SAMPLE = 100
K_RETRIEVAL = 4

# ── Load QA pairs ──
print(f"Loading qa_pairs.jsonl ...")
qa_pairs = []
with open(r'E:\Uagent\ref\qa_pairs.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= N_SAMPLE:
            break
        qa_pairs.append(json.loads(line.strip()))

print(f"Loaded {len(qa_pairs)} QA pairs")

# ── Init chain ──
print("Init chain_pipeline ...")
chain = chain_pipeline()

# ── Run ──
print(f"\nRunning {len(qa_pairs)} QA evaluations (k={K_RETRIEVAL})...")
results = []
t_start = time.time()

for i, qa in enumerate(qa_pairs):
    question = qa["question"]
    reference = qa["answer"]
    
    t_q = time.time()
    try:
        answer, contexts = chain.execute(question, k=K_RETRIEVAL)

        t_elapsed = time.time() - t_q
        
        # Check if answer contains reference
        ref_lower = reference.strip().lower()
        ans_lower = answer.answer.lower()
        exact_match = ref_lower in ans_lower
        
        results.append({
            "question": question, "reference": reference,
            "answer": answer.answer, "contexts": contexts,
            "time_s": round(t_elapsed, 1), "exact_match": exact_match
        })
        
        emoji = "✓" if exact_match else "✗"
        #if (i+1) % 20 == 0 or i < 3:
        print(f"  [{i+1}/{len(qa_pairs)}] {emoji} {t_elapsed:.1f}s | Q: {question[:50]}...")
        
    except Exception as e:
        results.append({"question": question, "reference": reference, "error": str(e)})
        print(f"  [{i+1}] FAILED: {e}")

t_chain = time.time() - t_start

# ── Summary ──
ok = [r for r in results if "error" not in r]
em_hits = sum(1 for r in ok if r["exact_match"])
print(f"\n{'='*50}")
print(f"  Total: {len(results)}")
print(f"  Success: {len(ok)}")
print(f"  Exact Match: {em_hits}/{len(ok)} ({em_hits/len(ok)*100:.1f}%)" if ok else "  N/A")
print(f"  Chain time: {t_chain:.0f}s ({t_chain/len(ok):.0f}s/QA)" if ok else f"  Chain time: {t_chain:.0f}s")

# ── Save ──
os.makedirs(r'E:\Uagent\eval_results', exist_ok=True)
output = {
    "config": {"n_sample": N_SAMPLE, "k_retrieval": K_RETRIEVAL, "llm": LlmConfig.model_name},
    "summary": {"total": len(results), "success": len(ok), "exact_match": em_hits, "time_s": t_chain},
    "results": results,
}
out_path = rf'E:\Uagent\eval_results\eval_{N_SAMPLE}_ce.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"Saved {out_path}")
