"""Extract context and QA datasets from SQuAD v2.0 JSON."""

import json

INPUT = "inputs/train-v2.0.json"
OUT_CONTEXT = "inputs/contexts.jsonl"
OUT_QA = "inputs/qa_pairs.jsonl"

with open(INPUT, "r", encoding="utf-8") as f:
    raw = json.load(f)

seen = set()
ctx_count = 0
qa_count = 0
ch_count =0
with open(OUT_CONTEXT, "w", encoding="utf-8") as fc, \
     open(OUT_QA, "w", encoding="utf-8") as fq:

    for article in raw["data"]:
        title = article["title"]
        for para in article["paragraphs"]:
            ctx = para["context"]

            # 去重后写入原文数据集
            if ctx not in seen:
                seen.add(ctx)
                fc.write(json.dumps({
                    "doc_id": ctx_count,
                    "title": title,
                    "context": ctx,
                }, ensure_ascii=False) + "\n")
                ctx_count += 1
                ch_count += len(ctx)

            # QA 数据集
            for qa in para["qas"]:
                answer = "No answer" if qa["is_impossible"] else qa["answers"][0]["text"]
                fq.write(json.dumps({
                    "question": qa["question"],
                    "answer": answer,
                }, ensure_ascii=False) + "\n")
                qa_count += 1

print(f"原文数据集: {ctx_count} 条 → {OUT_CONTEXT}")
print(f"QA数据集: {qa_count} 条 → {OUT_QA}")
print(f"其中无答案问题: {sum(1 for qa in raw['data'] for p in qa['paragraphs'] for q in p['qas'] if q['is_impossible'])} 条")
print(f"总字数：{ch_count}")
