import json, time, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'E:\Uagent')

from src.chain import chain_pipeline

N_SAMPLE = 140          #QA数
K_RETRIEVAL = 3         #检索K
THESHOLD = 0.8          #最大相似度阈值
GAP_THRESHOLD=0.3       #最大相似度-平均相似度 差阈值
MAX_RETRY=3             #最大重试
EMBED_WEIGHT=0.5        #向量检索在RRF排序中的权重

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
goldens =[]
oks=0
t_start = time.time()

for i, qa in enumerate(qa_pairs):
    question = qa["question"]
    reference = qa["answer"]
    
    t_q = time.time()
    #try:
    answer, contexts = chain.execute(question, k=K_RETRIEVAL,threshold=THESHOLD,gap_threshold=GAP_THRESHOLD,max_retry=MAX_RETRY,weight=EMBED_WEIGHT)
    t_elapsed = time.time() - t_q
    
    # Check if answer contains reference
    ref_lower = reference.strip().lower()
    ans_lower = answer.lower()
    exact_match = ref_lower in ans_lower
    goldens.append(
        {
            "input":question,
            "actual_output":answer,
            "expected_output":reference,
            "retrieval_context":contexts
        }
    )

    if exact_match:
        oks+=1
        emoji="✓"
    else:
        emoji="✗"
    print(f"  [{i+1}/{len(qa_pairs)}] {emoji} {t_elapsed:.1f}s | Q: {question[:50]}...")
        
    #except Exception as e:
        #print(f"  [{i+1}] FAILED: {e}")

t_chain = time.time() - t_start

# ── Summary ──

print(f"\n{'='*50}")
print(f"  Total: {len(goldens)}")
print(f"  Success: {oks}")
print(f"  Exact Match: {oks}/{len(goldens)} ({oks/len(goldens)*100:.1f}%)" if oks else "  N/A")
print(f"  Chain time: {t_chain:.0f}s")

# ── Save ──
os.makedirs(r'./eval_results', exist_ok=True)
golden_path=rf'./eval_results/.dataset.json'
with open(golden_path,'w',encoding="utf-8") as f:
    json.dump(goldens,f,ensure_ascii=False,indent=2)