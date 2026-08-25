# Bible Commentary Translator — Project Plan

**Status date:** 2026-08-11
**Revision 3.** Updated after your feedback on revision 2. Four changes: the fidelity target is now stated correctly (§2.3), the headline metric is now **post-editing effort** rather than accuracy (§6), multi-quote blocks are specified as their own workstream with measurements (§5.7), and the phases are resequenced accordingly (§10).
**Scope:** plan only. No code has been written or changed.

---

## 0. Correction to revision 1

Revision 1 said the runtime pipeline "does not exist." That was wrong — it was based on the four notebooks then in the folder. `Agent in the Notebook.ipynb` **is** the runtime pipeline, it is complete, and it works. It ran Hebrews 12:1–13 end to end: 101 commentary blocks scraped, translated, and streamed into a styled Google Doc, finishing cleanly.

Two claims from revision 1 that I withdraw:

- ~~"No string-matching code exists."~~ It exists, in `run_live_production_pipeline`, and it searches **every verse in the block's range** — not just the first. Better than the training-data path.
- ~~"There is no serving layer."~~ There is one, and it's a smarter choice than the Telegram bot I proposed: it writes directly into Google Docs with your existing typography (H3 red 20pt, H4 blue 18pt, body 16pt, list-depth indentation). That matches how your family already reads these. See §7.

One claim from revision 1 that **survives and is now confirmed against runtime code**: there is no sequential dependency between blocks. See §3.

---

## 1. What exists

| File | Role |
|---|---|
| `Agent in the Notebook.ipynb` | **The product.** Scrape → match → extract → translate → styled Google Doc. |
| `Data Curation.ipynb` | Training-data builder. 39 Google Docs → 1,117 Task-1 + 2,664 Task-2 records. |
| `LoRA Fine-tuning Qwen3_5_(4B).ipynb` | Stage-2 fine-tune (starts from the stage-1 merged model on HF). |
| `COMET-22` / `COMET-Kiwi` analysis notebooks | Benchmark of general EN→VI on PhoMT, 6 systems. |
| `outputs_*.csv` / `results_*.csv` / `outliers_*.csv` | Raw translations, COMET-scored results, IQR outliers. |

### 1.1 The runtime pipeline, precisely

`run_live_production_pipeline(commentary_blocks, bible_cache, target_doc_id, tokenizer, model)`:

1. `dynamic_bible_pipeline(book, chapter, start, end)` — scrapes Enduring Word, discovers the verse bounds the commentary *actually* touches, then fetches VI1934 + NKJV for exactly that range. This boundary-expansion step is a genuinely good piece of design; keep it.
2. Per block, if `bold_quote` is non-empty: **Python exact lookup** — case-insensitive substring search of the English quote across every verse `v_start..v_end` in the cache.
3. **Prompt 1** (`get_extracted_quote`) — EN verse + VI verse + EN quote → the Vietnamese phrase. Greedy, `max_new_tokens=64`.
4. **Prompt 2** (`translate_commentary_with_quote`) — commentary text + `CRITICAL: You must use the exact phrase '{vi}' for '{en}'`. Greedy, `repetition_penalty=1.15`, `max_new_tokens = max(0.5 × input_tokens, 128)`.
5. `append_styled_document_block` — pushes into Google Docs with per-block-type styling.

Model: `phuclhp1922/bct_qwen3.5_0.8B_translation_merged_16bit` — correctly the **stage-2** model.

---

## 2. Measured results

### 2.1 General translation (PhoMT, your two analysis notebooks)

**COMET-22, reference-based, n = 19,151:**

| Model | COMET-22 |
|---|---|
| Llama3.2-1B-IT | 0.732 |
| Qwen3.5-0.8B (base) | 0.793 |
| **Qwen3.5-0.8B + LoRA (yours)** | **0.826** |
| Qwen3.5-2B | 0.839 |
| TranslateGemma-4B-IT | 0.853 |
| VinAI Translate | 0.867 |

**COMET-Kiwi, reference-free, n = 19,131 (after Vietnamese language-ID filter):**

| Model | COMET-Kiwi |
|---|---|
| Llama3.2-1B-IT | 0.686 |
| Qwen3.5-0.8B (base) | 0.767 |
| **Qwen3.5-0.8B + LoRA (yours)** | **0.805** |
| *PhoMT human reference* | *0.809* |
| Qwen3.5-2B | 0.820 |
| TranslateGemma-4B-IT | 0.830 |
| VinAI Translate | 0.835 |

**+0.038 COMET-Kiwi from LoRA on a 0.8B model, landing within 0.004 of the human reference.** Earned, and defensible.

### 2.2 NEW — Scripture fidelity, measured from your Hebrews 12 run

I extracted all 42 quote-extractions printed by your live run and checked each against the actual VI1934 text of Hebrews 12 fetched from httlvn.

> **39 / 42 extracted quotes (92.9%) are verbatim VI1934.**

The 3 failures, with the true text:

| Model output | Actual VI1934 | Failure |
|---|---|---|
| "mấy người chứng kiến" | "**nhiều** người chứng kiến" | word substitution |
| "chịu thập tự giá" | "chịu **lấy** thập tự giá" | dropped word |
| "Nếu anh em không chịu sửa phạt, thì anh em **vô nghĩa** và không phải con" | "…thì anh em là **con ngoại tình**, chớ không phải con **thật**" | free paraphrase; theologically wrong ("illegitimate child" → "meaningless") |

Caveats: n = 42 from a single passage, and this measures *extraction* output, not what actually landed in the final Google Doc. It is an indication, not a benchmark — §6 is how it becomes one. But **it is the first task-level number this project has**, and 92.9% is a good place to be starting from.

Note also: **42 of 101 blocks (41.6%) carry a bold quote** — almost exactly the 1,117/2,664 (41.9%) ratio in your training data. Consistent, which is a good sign that the scraper behaves the same at train and inference time.

### 2.3 What "correct" means here — corrected after discussion

Revision 2 framed the third failure above as *theologically wrong*. That framing was imprecise, and the distinction matters enough to state as a project axiom:

> **VI1934 is the ground truth, not semantic accuracy.** The mainstream Vietnamese Protestant church reads the 1926/1934 translation. Where that century-old text renders the Greek or the English oddly, the odd rendering **is** the correct output. The pipeline's job is fidelity to VI1934, never improvement on it.

So there are two different things, and only one of them is a defect:

| | Situation | Verdict |
|---|---|---|
| **A** | VI1934's wording diverges from the English commentary's sense | **Accept.** Not a bug. Out of scope permanently. |
| **B** | Model emits text that is not in VI1934 at all | **Defect.** Always. |

All three failures in §2.2 are type **B** — "mấy" for "nhiều", a dropped "lấy", and a paraphrase replacing "con ngoại tình". None are the 1934 translators' doing.

**This simplifies the design considerably**, and it is good news:

- The validity check in §4.2 is exactly the right check, because the only question ever asked is *"is this string literally present in the verse?"* — never *"is this a good translation?"* That is a `str.__contains__`, not a judgement call. No semantic scoring, no LLM-as-judge, no ambiguity.
- Type-A cases can never be "fixed" by a better model, so no effort should ever go to them.
- It makes abstention safe. When the check fails, the honest fallback is to leave the phrase untranslated and flag it — a human decides. A pipeline that silently paraphrases scripture is worse than one that admits it could not find the phrase.

Worth saying plainly in the README: *"The system is constrained to reproduce VI1934 verbatim; it does not paraphrase or modernise scripture."* That is a design position, and it reads as domain understanding rather than a limitation.

---

## 3. The batching question, answered against the runtime code

You asked whether extraction could be batched even though smoothing stays sequential.

**Extraction is embarrassingly parallel — confirmed.** `get_extracted_quote` takes only `(english_verse, vietnamese_verse, english_quote)`, all derived from the verse cache and the current block. Nothing depends on any previous block's output.

**Smoothing is *also* stateless — confirmed.** `translate_commentary_with_quote` receives only the current block's text and its own quote pair. No previous paragraph, no running glossary, no document context. **The sequential dependency you described is a design intention, not a property of the system as built.** Today every block is independent, so the whole document is batchable.

You already did the hard prerequisite: `tokenizer.padding_side = "left"` is set in `load_translation_engine`. The groundwork is there and unused.

Current cost for Hebrews 12: **143 sequential `model.generate` calls** (42 extraction + 101 smoothing), batch size 1 throughout. Batching extraction into 2–3 padded batches and smoothing into ~8 is a large, low-risk win on a 0.8B model.

If you want real coherence later, build it deliberately: batch **within** a `scripture_anchor` section, run sequentially **across** sections, and thread a committed-terminology glossary through. You get most of the speed and most of the consistency — and, importantly, you can then *measure* the difference (§6.6), which is what makes it a CV story rather than a design opinion.

---

## 4. Defects found in the runtime pipeline

Severity-ordered. These are specific to `Agent in the Notebook.ipynb`.

### 4.1 The silent fallback structurally invites hallucination — CRITICAL

```python
if not english_verse_line and v_start in bible_cache:
    english_verse_line   = bible_cache[v_start]["eng"]
    vietnamese_verse_line = bible_cache[v_start]["vie"]
```

When the exact lookup finds nothing, this hands the model **verse `v_start` — a verse just proven not to contain the quote** — and asks it to "extract the corresponding Vietnamese phrase." There is no corresponding phrase. The model's only options are to invent one or to return something unrelated. Nothing is logged, so a fabricated quote is indistinguishable from a real one downstream.

This is almost certainly the mechanism behind the "vô nghĩa" failure in §2.2, and it is exactly where the semantic-retrieval upgrade belongs. **This single finding converts retrieval from "a nice idea" into "fixes a located defect," which is a far stronger CV narrative.**

**Fix now (before any retrieval work):** log every fallback, and count them. That number is your motivation and your baseline.

### 4.2 No validation that the extracted quote exists in the verse — CRITICAL, trivial to fix

`get_extracted_quote` returns whatever the model emits. Nothing checks it against `vietnamese_verse_line`.

```python
if extracted and extracted not in vietnamese_verse_line:
    extracted = ""   # abstain rather than inject a fabricated quote
```

**All three failures in §2.2 would have been caught by this check** — it would have raised verbatim-quote rate from 92.9% to effectively 100%, trading 3 injected-but-wrong quotes for 3 abstentions. Highest value-to-effort item in this entire document. Two lines.

### 4.3 Nothing verifies the quote survived into the final translation — CRITICAL

Prompt 2 says `CRITICAL: You must use the exact phrase '{clean_vi}'`. No code ever checks whether it did. The entire thesis of this project is verbatim Vietnamese scripture, and it is currently unmeasured at the output.

```python
quote_honored = bool(clean_vi) and clean_vi in translated_commentary
```

This gives you your headline metric *and* a retry trigger, for free, in three lines.

### 4.4 `max_new_tokens` will truncate long blocks — HIGH

```python
dynamic_headroom = max(int(input_token_count * 0.5), 128)
```

Input includes system prompt + instruction + quote instruction (~110 tokens of overhead) plus the commentary. For a short block that's generous; for a 400-token commentary paragraph the budget is ~255 tokens for output that needs ~400+. Vietnamese is not shorter than English under a Qwen tokenizer. **Longer blocks are silently truncated mid-sentence.** Check the tail of the blocks in your Hebrews 12 doc — I expect visible cut-offs. Use `~2.0 ×` plus a floor, or generate to EOS with a hard ceiling.

### 4.5 `repetition_penalty=1.15` works against the project's own goal — MEDIUM-HIGH

You are explicitly instructing the model to reproduce an exact scripture phrase, then penalising it for repeating tokens. When the commentary discusses the phrase it just quoted (which is what commentary *does*), the penalty pushes against verbatim reuse. Also an odd pairing with `do_sample=False`. Ablate it: run with and without, compare §4.3's quote-honored rate.

### 4.6 Google Docs writes are O(n²) — MEDIUM-HIGH

`append_styled_document_block` calls `documents().get()` — **fetching the entire document** — on every block, purely to read `content[-1].endIndex`. As the doc grows, each fetch gets bigger. 101 blocks = 202 API round-trips, with the payload growing linearly, inside the generation loop.

Fix — **agreed as work, and there are two options that are not equivalent:**

| Option | Round-trips | Trade-off |
|---|---|---|
| **Track the index locally** — one `documents().get()` at the start, then add the length of every string you insert | 101 (one `batchUpdate` per block) | **Recommended.** Output still streams into the doc block by block, so you can watch it work and a crash keeps everything written so far. |
| **One `batchUpdate` at the end** | 2 | Fewest calls, but nothing appears until the run finishes, and a failure at block 87 leaves an empty document. Also risks the 500-request-per-`batchUpdate` cap once you exceed ~250 blocks. |

Take the first. It removes ~100 full-document fetches and the linearly growing payload, keeps the streaming behaviour, and composes with the checkpointing in §4.7 — whereas deferring everything to the end actively fights it. Insert lengths are exactly known (you build the strings), so the local index is deterministic; assert it against a single `get()` at the end of the run as a cheap correctness check.

This also closes an index-drift race: between `get` and `insert` the document is assumed unchanged, which stops being true the moment anyone opens it while the pipeline runs.

### 4.7 No checkpointing or error handling — MEDIUM

101 blocks, one long run, no try/except and no resume. A network blip, a Colab disconnect, or a Docs quota error at block 87 loses everything. For something family members depend on, add per-block error capture and a resume-from-block-N.

### 4.8 Extraction `max_new_tokens=64` — MEDIUM

Some Enduring Word bold quotes are a full clause. Block 64's extraction was already 94 characters. 64 tokens is tight for Vietnamese; raise it and let EOS stop generation.

### 4.9 Model-name footgun — LOW but nasty

- stage 1: `phuclhp1922/qwen3.5_0.8B_translation_merged_16bit`
- stage 2: `phuclhp1922/bct_qwen3.5_0.8B_translation_merged_16bit`

They differ by the prefix `bct_`. The notebook currently uses the right one. But a single typo silently benchmarks the wrong model and you would never notice. Rename to `…-stage1-general` / `…-stage2-commentary`.

### 4.10 Unpinned bleeding-edge dependency — LOW, blocks reproducibility

`!pip install git+https://github.com/huggingface/transformers.git` plus the new-style `dtype=` kwarg. This notebook will break at an unknown future date. Pin an exact version before this becomes a repo.

---

## 5. Defects in the training-data builder

Still valid from revision 1 — these affect the **model**, not the pipeline, and matter whenever you retrain.

**5.1 — Positional `zip` alignment is unverified (HIGH).** `zip(parsed_english_blocks, meaningful_vi_paragraphs)` pairs by index; the health check compares only **counts**. "39/39 perfect" means 39 documents had matching counts, not that block *i* corresponds to paragraph *i*. One stray paragraph shifts an entire document and still passes. Fix: score each pair with COMET-Kiwi or a multilingual embedding, flag documents whose diagonal isn't the best assignment.

**5.2 — First-quote regex may mislabel (HIGH).** `quotes_found[0]` takes the first `“…”` in the Vietnamese paragraph and assumes it maps to the English `bold_quote`. Misses straight quotes and `«…»`. Also discards every quote after the first — see **§5.7**, which measures how much that costs. Fix: pick the candidate most similar to `vietnamese_verse_line`, which is already in scope.

**5.3 — Training data uses only the first verse (MEDIUM-HIGH).** `bible_cache.get(v_start)` — for a block anchored to 3–12 with a quote from verse 9, the model was trained to extract a phrase absent from its input, i.e. **trained to hallucinate**. The runtime pipeline searches the whole range (§1.1); the training data does not. Aligning them should improve §2.2 directly. Note the interaction with §4.1: the model was *taught* that the answer might not be in the verse it was given.

**5.4 — `VI_TO_EN_BOOKS` is New Testament + Isaiah only (MEDIUM).** Old Testament study guides fail `parse_reference_from_header` and are dropped **silently**. Completing the map may recover training data you already own. 10 minutes.

**5.5 — No caching, no rate limiting (MEDIUM).** Every run re-scrapes both sites. Slow, fragile, impolite, and it means an outage at httlvn takes your product down. Cache VI1934 + NKJV for all 66 books into one SQLite file (~31k verses, a few MB) and never fetch scripture at request time again. This is also the prerequisite for retrieval (§8).

**5.6 — Task-1 covers 41.9% of blocks.** Consistent with runtime (41.6%), so probably genuine quote-free blocks rather than a bug. Worth one confirming check.

### 5.7 — One quote per block, when half of them have more — HIGH, and the largest automation win on the table

You raised this, and it is the highest-value item in this plan that is not already a two-line fix. I measured it.

**The cause is two characters.** In the block parser — duplicated verbatim in *both* notebooks — the English side is:

```python
bold_tag   = element.find("strong")                              # <- find, not find_all
bold_quote = bold_tag.get_text().strip() if bold_tag else ""     # <- a str, not a list
```

`find` returns the first match only. Everything downstream — the `block["bold_quote"]` key, the Task-1 record, the `CRITICAL: You must use the exact phrase…` instruction — is typed as a single string because of this one call. The Vietnamese side is *already* multi-quote capable and throws the result away:

```python
quotes_found = re.findall(r'“([^”]+)”', vi_text_clean)           # finds all of them
extracted_vi_quote = quotes_found[0]... if quotes_found else ""  # keeps one
```

#### 5.7.1 How much is being discarded — measured

I scraped 8 chapters spread across the canon (Hebrews 12, Romans 8, John 3, Psalm 23, Genesis 1, Matthew 5, 1 Corinthians 13, Ephesians 2) and counted `<strong>` spans per body paragraph, applying your parser's own filters.

**1,397 body paragraphs. 570 carry at least one bold span.**

| Bold spans in paragraph | Paragraphs | Share |
|---|---|---|
| 0 | 827 | 59.2% |
| 1 | 279 | 20.0% |
| 2 | 155 | 11.1% |
| 3 | 78 | 5.6% |
| 4 | 35 | 2.5% |
| 5 | 17 | 1.2% |
| 6+ | 6 | 0.4% |

> **Of the paragraphs that have a quote at all, 50.7% have more than one.** The parser sees roughly half the scripture anchors in the corpus. Your instinct was right, and the effect is larger than "many blocks."

Two useful secondary findings:

- **Fragmentation is a non-issue.** Only 2 of 1,397 paragraphs had adjacent `<strong>` spans that were really one quote split by inline markup. So `find_all` is safe — each span is a genuinely distinct quotation, not a piece of one. No merging heuristic needed.
- **The rate is stable across genres** — Genesis 1 narrative, Psalm 23 poetry, and 1 Corinthians 13 epistle all show it. This is how Enduring Word is written, not a quirk of Hebrews.

#### 5.7.2 The spans are not N independent quotes — this is the design insight

I classified all 540 non-first spans in the multi-quote paragraphs by their relation to the paragraph's opening anchor:

| Relation to anchor span | Count | Share |
|---|---|---|
| **Substring of the anchor** | 286 | 53.0% |
| **Disjoint from the anchor** | 192 | 35.6% |
| Partial word overlap | 52 | 9.6% |
| Superset of the anchor | 10 | 1.9% |

The dominant pattern is: the paragraph opens with the full anchor phrase, then re-quotes *sub-phrases of it* while discussing them. From Hebrews 12:

```
b. Let us lay aside every weight, and the sin: Sin can hold us back.
   But there are also things that may not be sin (every weight) but are merely hindrances…
       ^ anchor = "Let us lay aside every weight, and the sin"
       ^ span 2 = "every weight"  — a substring of the anchor
```

This splits the problem into three tiers with very different costs:

| Tier | What it is | ~Share | How to resolve |
|---|---|---|---|
| **1** | The opening anchor | — | Exactly what works today. Unchanged. |
| **2** | Sub-phrase of the anchor | ~53% | **Free-ish.** The Vietnamese is a *substring of the already-extracted Vietnamese phrase*. No new verse lookup, no new context — one short constrained call, or word-level alignment. |
| **3** | Disjoint from the anchor | ~36% | The expensive tier. Either another phrase from the same verse range, or **a cross-reference to another book entirely** — which is precisely the limitation you already identified. |

**Two consequences worth noticing.**

First, this is *not* 2.5× the inference cost. Tier 2 is more than half the work and is a cheap constrained call against a string you already hold — you can even try `str.find` on the Vietnamese phrase before invoking the model at all.

Second, and more useful for the project's story: **tier 3 is the retrieval case, and it now has a measured size.** §8 stops being "an upgrade I read about" and becomes "≈36% of the quotes I currently discard cannot be resolved from the passage's own verses." That is a much stronger motivation, and it is the same defect as §4.1 seen from the data side.

#### 5.7.3 What has to change

The parser change is small; the **type change is what propagates**, so do it deliberately:

1. **Parser** (`src/bct/sources/enduring_word.py` once §7 exists — today, duplicated in two notebooks): `find_all("strong")`, emit `block["bold_quotes"]: list[str]`. Keep `bold_quote` as a property returning `[0]` during migration so nothing breaks mid-change.
2. **Dedupe and sort.** Drop exact repeats (the Hebrews 12 example has "witnesses" three times), then process longest-first so the anchor resolves before its own sub-phrases.
3. **Tier-2 shortcut.** If span *k* is a substring of the anchor, try to resolve it inside the anchor's already-extracted Vietnamese phrase before calling the model.
4. **Extraction, batched.** Tier-3 spans are independent given the verse — this is §3's batching, and multi-quote is what makes batching actually pay off.
5. **Prompt 2 takes a list.** Today: `CRITICAL: You must use the exact phrase '{vi}' for '{en}'.` With N constraints this becomes a numbered list, and **you should expect degradation** — a 0.8B model holding 5 simultaneous lexical constraints is a real ask. Measure it (§6) rather than assuming. If it degrades, the fallback is deterministic: translate with the anchor constrained only, then **post-hoc string-substitute** the remaining verified phrases. Less elegant, but the substitution is exact by construction, which is the whole point of §2.3.
6. **Curator pairing.** With `n_en` English spans and `n_vi` Vietnamese `“…”` spans per aligned paragraph, `n_en == n_vi` lets you pair positionally with real confidence — order is preserved within a paragraph. When they disagree, skip the block and log it. **This is strictly better supervision than today's blind `[0]`**, and it doubles as an alignment check on §5.1.
7. **First thing to run:** the `n_en` vs `n_vi` histogram over your 39 existing study guides. It costs one loop, needs no model, and tells you how much *already-owned* training data this unlocks. Do it before building anything.

#### 5.7.4 Why this is worth your time

It is the only item here that directly reduces your manual workload rather than measuring it. Every discarded span is a phrase you currently retype by hand. And it compounds correctly with the rest of the plan: it enlarges the training set (§5), it gives batching something to do (§3), it sizes the retrieval work (§8), and it is measured by the edit-distance metric in §6 — which will show it as a drop in characters typed, not an abstract accuracy delta.

---

## 6. Evaluation — rebuilt around post-editing effort

Your rigor is on the wrong benchmark. PhoMT measures general EN→VI. Nobody will doubt you can run COMET; they will ask **"did the domain fine-tune help on the domain?"** §2.2 is a first data point (n=42, one passage, extraction only). Turn it into a benchmark.

You proposed measuring **how many characters you have to change to get the output you want.** That is the right instinct, and it is a better headline metric than anything I proposed in revision 2. It gets promoted to §6.1.

### 6.1 Headline metric — post-editing effort ★

The metric you described already exists and has a name: **HTER — Human-targeted Translation Edit Rate.** It is the standard industry measure of post-editing effort, and it is what translation companies actually buy on. Using it by name is worth something on a CV; inventing a synonym is not.

Definition, at character level (right choice for Vietnamese — diacritic and function-word fixes are sub-word edits that a word-level metric rounds away):

```
edit_rate(block) = levenshtein(model_output, target) / len(target)
```

`rapidfuzz.distance.Levenshtein` for speed; `difflib` if you want zero dependencies. Segment at **block** level, since that is your unit of production.

**Nothing here is measured by hand.** HTER is *defined* as an automatic edit distance — no keystroke logging, no timing, no stopwatch. It compares two finished strings, so it is indifferent to the fact that you edit across many days in short sittings. There are two variants depending on what `target` is, and you want both:

| `target` | Name | What it measures | Manual work |
|---|---|---|---|
| `A_test`'s human Vietnamese | **TER** | Distance from an independent human translation | None |
| Your edit of *that same output* | **HTER** | Your actual workload | None — but requires keeping the raw draft |

**TER on `A_test` is the model-comparison metric.** Fully automatic, repeatable, runnable a hundred times against any model. This is what ranks 0.8B against 2B. Its one distortion: it counts *acceptable rewording* as work — the model writes "ngăn trở", the reference says "kìm hãm", both are fine but the metric charges you. So it **overstates real effort**. Harmless for ranking, since the same inflation applies to every model on the same set; it matters only if you quote the absolute number as your workload claim.

**HTER on `(raw draft, your final version)` is the workload metric** — the honest source for "cut my post-editing effort by X%". It needs one thing the pipeline does not currently do: **preserve the raw model output before you edit it.** Today the pipeline writes into a Doc and you edit that Doc in place, so the draft is destroyed and the measurement is unrecoverable. Fix in Phase 1 by dumping raw output to a `.jsonl` alongside the Doc. Also worth checking: the pipeline-written state is the **first revision** of every Doc it created, so Google Docs revision history may let you recover drafts for chapters you have already edited — a retroactive effort dataset for the cost of ten minutes' checking.

Report four numbers:

| Number | Why it earns its place |
|---|---|
| **Median char-HTER per block** | The core figure. Median, not mean — a handful of catastrophic blocks shouldn't set the headline. |
| **First-pass acceptance rate** — % blocks needing *zero* edits | The most legible number you will produce. "62% of paragraphs ship untouched" needs no explanation to anyone. |
| **Characters edited per chapter** | Converts directly to minutes. This is the business metric. |
| **Distribution, not just the average** | A model with median 0.05 and a 10% tail at 0.8 feels much worse to use than a uniform 0.15. Report p50/p90, and plot it. |

Why this beats accuracy metrics for you specifically:

- It measures the thing you actually care about — **your time** — and it is the only metric here that a non-technical reader immediately understands.
- It falls out of work you are doing anyway. Every post-edit you make is a labelled data point, at zero annotation cost.
- It gives the CV a causal sentence instead of a benchmark number: *"reduced post-editing effort per chapter from N characters to M — roughly X hours per week."* Far stronger than a COMET delta.
- It also grades the pipeline machinery, not just the model. Fix §4.1's silent fallback or ship §5.7's multi-quote handling and HTER drops, because you stop retyping phrases by hand. COMET would barely register either change.

Keep COMET as the *supporting* metric (§6.5). Lead with HTER.

### 6.2 The split — and the contamination trap ★ time-sensitive

You are right that you now have enough data to split properly. But your bootstrapping loop — v1 model → translate faster → more data → train v2 — has a well-known failure mode, and **the window to protect against it is open right now and closing.**

The loop is sound. It is called iterative post-editing, and it is how commercial MT systems are actually built. The problem is not the loop; it is what the loop does to your *test set*.

**Two separate properties are needed for an honest quality number, and they are easy to conflate:**

| | Property | Question it answers |
|---|---|---|
| **P1** | **Reference independence** — the Vietnamese was written by a human who never saw model output | "Is this target text a fair goal, or is it the model's own phrasing wearing a hat?" |
| **P2** | **Train/test separation** — the document was not in the training data | "Is the model recalling this, or translating it?" |

Where your 39 documents stand today: **they all have P1 permanently. None of them have P2.** `process_and_export_all_datasets` built `task2_translation.jsonl` from all 39 aligned files, and stage 2 trained on it — so every document you own is in v1's training set.

Two consequences, and neither is a disaster:

- **Any v1 score measured on these documents is optimistic.** Not worthless — quote-fidelity and fallback-rate diagnostics are still perfectly informative — but a COMET or HTER number from v1 on this data is not a held-out number, and should be labelled as such rather than quoted as a benchmark.
- **P2 is recoverable; P1 is not.** Tag the test documents now and *exclude them at the next retrain* — v2 then has both properties and gives you your first honest generational comparison. If you want an honest v1 baseline as well, re-run stage 2 without the test documents; that is a few GPU-hours, and it buys the "before" column of your headline table.

**Scaling to a larger base model (e.g. Qwen3.5-2B) — the equal-footing rule.** If you train the 2B on `A_train` only while the existing 0.8B was trained on all 39, the two models sit the same exam under different rules: the 0.8B has seen the answers. It will look better than it is, and the comparison you most want to make is the one that gets corrupted. **Retrain the 0.8B stage 2 on the same `A_train` split** so both are closed-book. Since a 2B run means redoing the pipeline anyway, do both under one split and one data build — it costs a few extra GPU-hours and turns "0.8B vs 2B" into a claim you can defend.

**What trains on what.** The restriction is on *grading*, not on learning:

| Set | Contents | Train on it | Grade with it |
|---|---|---|---|
| `A_test` | ~8 of the 39 hand-translated guides | **No — ever** | **Yes — always.** The permanent exam. |
| `A_val` | ~4 of the 39, for checkpoint selection | No | Validation only |
| `A_train` | The remaining ~27 | Yes | No |
| `B` | All future post-edited output | **Yes** | **No** |

`B` being unusable as a reference does **not** make it unusable as training data — post-edited output is exactly what iterative MT bootstrapping runs on, and it is the main reason to build v1 at all. Learn from `B`; never let `B` be the judge.

**The trap.** Once you translate with the model and post-edit the result, that document loses P1 — permanently, and silently. Two distinct effects:

1. **Anchoring.** Post-editors change far less than they would write from scratch — you fix what is wrong, you don't rewrite what is merely not-your-phrasing. So a model-derived reference is biased *toward the model*. Any successor model trained on the same style scores better against it than it deserves. Your numbers drift upward while nothing improves.
2. **Error ossification.** Mistakes you didn't consider worth fixing get trained in, then reproduced, then re-accepted. The loop launders them into ground truth.

**The mitigation costs almost nothing today and is impossible later:**

- [ ] **Freeze a clean test set now.** Your 39 study guides were translated by hand **before this model existed**, so they hold P1 and always will. Tag 6–8 of them `test`, write the manifest into the repo, and **never train on them, never post-edit them, never let the pipeline touch them.** More P1 documents remain *possible* later — but only by translating a chapter fully by hand, which is precisely the labour you are automating away, so in practice you will stop producing them. These 39 are the ones you already own for free. Do this in Phase 0, before anything else — it costs ten minutes.
- [ ] **Stamp provenance on every document from now on**: `human_from_scratch` | `post_edited_v1` | `post_edited_v2`. One field in the manifest. Reconstructing it later from memory is hopeless, and without it you can never explain which numbers are comparable.
- [ ] **Translate one chapter from scratch per model generation.** A small fresh unbiased slice keeps the clean set from going stale as your own style shifts.

**And keep the two uses of HTER separate**, because they contaminate differently:

| Use | Reference | Contaminated by the loop? |
|---|---|---|
| **HTER as effort** — "how much work did this save me?" | Your post-edit of *that same output* | **No.** It literally measures the keystrokes you typed. Always valid. |
| **HTER / COMET as quality** — "is v2 better than v1?" | An independent human translation | **Yes.** Needs the frozen clean set from above. |

Report both, label which is which. Being explicit about this distinction is exactly the kind of thing that reads as maturity in an interview — most candidates never notice it.

**Split shape.** Document level, not row level — blocks from one chapter share verses, so a row-level split leaks. Roughly 25 train / 6 val / 8 test out of 39. Spread the test set across Old Testament / New Testament / epistle / narrative rather than taking the last 8; with n=8 documents an unlucky draw is a real risk. ~8 documents × ~100 blocks ≈ 800 blocks is plenty for block-level metrics.

### 6.3 Quote extraction accuracy

Exact-match rate + character F1 against your gold phrases, reported separately for *exact-lookup hits* vs *§4.1 fallbacks*. The fallback slice is where retrieval will earn its keep. With §5.7 in place, break out tier 1 / tier 2 / tier 3 as well.

### 6.4 Scripture fidelity (the project's thesis)

Fraction of quoted scripture in the **final output** that is verbatim VI1934 — enabled by §4.3, and a pure string containment test per §2.3. Compare: Google Translate / VinAI · Qwen3.5-0.8B base · your stage-2 model without quote injection · your stage-2 model with the full pipeline. The last row should dominate, because a generic MT system *structurally cannot* do this. **That table is the most compelling thing you can put in the README.**

### 6.5 Commentary translation quality

COMET-22 (clean-set human translations as reference) + COMET-Kiwi, same model list. Reuse your existing tooling verbatim. Supporting evidence for §6.1, not the headline.

### 6.6 Terminology consistency

Within a document, does a repeated theological term get one Vietnamese rendering or several? This is what would justify the glossary/sequential design from §3 — and right now the answer is measurable and unknown.

### 6.7 Multi-quote regression check

When §5.7 lands, the specific risk is Prompt 2 degrading under N simultaneous constraints. Track per-constraint honor rate against N (1, 2, 3, 4+). If it falls off past N=2, take the deterministic post-hoc substitution path in §5.7.3 step 5. This is a small ablation and it decides a real design question.

---

## 7. Turning this into a git repository

You asked directly. Here is the assessment and the plan.

### 7.1 The strongest argument for extracting a package

`Agent in the Notebook.ipynb` cells 7, 9, 10, 12 are **byte-identical** to `Data Curation.ipynb` cells 5, 7, 8, 10 — about 11 KB of scraper code, copy-pasted across two notebooks. Fix a bug in one (say, §5.4's book map) and the other silently keeps the old behaviour. This will bite you, and it is the concrete reason to have a `src/` layer rather than an aesthetic preference.

### 7.2 Recommended layout — hybrid, not a rewrite

Do **not** delete the notebooks. Colab is your GPU, notebooks are your honest history, and the analysis notebooks *are* the deliverable for the benchmark work. Extract the shared code; let notebooks import it.

```
bible-commentary-translator/
├── README.md                  ← the CV artifact (§9)
├── PLAN.md
├── pyproject.toml
├── requirements.txt           ← PINNED (see §4.10)
├── .gitignore
├── .env.example
├── src/bct/
│   ├── sources/               ← enduring_word.py, httlvn.py, cache.py
│   ├── corpus/                ← build_bible_db.py, verse_store.py, build_index.py
│   ├── align/                 ← exact.py, retrieval.py, router.py
│   ├── pipeline/              ← extract.py, smooth.py, glossary.py, translate_doc.py
│   ├── output/                ← gdocs.py (styling engine, batched), markdown.py
│   ├── data/                  ← build_dataset.py, verify_alignment.py
│   ├── eval/                  ← quote_accuracy.py, fidelity.py, comet_runner.py
│   └── cli.py                 ← bct translate "Hebrews 12:1-13"
├── notebooks/                 ← the 5 existing ones, now thin: import bct, call it
├── data/                      ← gitignored; bible.sqlite is rebuildable
├── results/                   ← committed: COMET tables, fidelity tables, run logs
└── tests/
```

### 7.3 Concrete setup steps

1. **`git init` now**, before anything else. Commit the current state verbatim as the historical baseline. This folder is currently one accidental delete away from gone.

2. **Notebook output handling — do this deliberately.** Notebook JSON diffs are unreadable and your `.ipynb` files are 150 KB–950 KB largely because of embedded outputs.
   - Commit **one** snapshot *with* outputs first. Your outputs are evidence: the 101-block Hebrews 12 run, the COMET statistics, the alignment report. Losing them would be a real loss.
   - **Then** install `nbstripout` (`nbstripout --install`) so future commits strip outputs automatically.
   - Export anything you actually want to cite into `results/` as CSV/Markdown, so the evidence survives independently of notebook state.

3. **Big files.** The CSVs total ~50 MB and are regenerable. `.gitignore` them and document how to rebuild, or use Git LFS if you want them versioned. Do **not** commit them plainly — it permanently bloats every future clone.

4. **Privacy audit before the first push — do this one carefully.** Committed notebook outputs currently contain:
   - Your Drive folder ID `YOUR_DRIVE_FOLDER_ID` (hardcoded in `Data Curation.ipynb`)
   - A live Google Doc link `docs.google.com/document/d/YOUR_DOCUMENT_ID/edit` in the Agent notebook output
   - Vietnamese titles of your family's study guides ("LESSON 30", "LESSON 72", …)

   None are credentials, and the docs are presumably private. But a public repo publishes the identifiers, and anyone who later gains access can use them. Move IDs to `.env`, and scrub them from any outputs you commit. **If the repo will be public, do this before the first push** — `git filter-repo` afterwards is painful and mirrors keep the old objects.

5. **Decouple from Colab.** `from google.colab import auth` and `notebook_login()` are Colab-only. For a repo (and later a server) you need a **Google service account** JSON via `.env`, with the target Drive folder shared to the service account's email. `google.auth.default()` then works in both environments unchanged. This is the main portability blocker and it's maybe an hour of work.

6. **Build a commit history, don't squash.** A CV repo with one "initial commit" of finished code is much less persuasive than one where a reviewer can watch you find the fallback bug, measure it, add retrieval, and measure again. Commit the phases in §10 as you go, with messages that say what you learned.

7. **Licensing / attribution.** Enduring Word commentary and the VI1934 text are third-party content. Keep the existing `©1996 Enduring Word` attribution visible in output, add a README note on sources, and license only *your* code. Also settle whether the 39 family study guides are yours to publish (§11) — the dataset is a strong portfolio asset only if you hold the rights.

---

## 8. The retrieval upgrade

Now well-motivated by §4.1 rather than speculative. Sequence matters — **do not start this until §4.1's logging and §6 exist**, or you will have no way to show it helped.

- **Stage A — cache the Bible.** All 66 books, VI1934 + NKJV, into `bible.sqlite`. One polite afternoon of scraping. Everything downstream reads from here (§5.5).
- **Stage B — strengthen the exact pass.** Normalize case, whitespace, and quote glyphs; add a fuzzy tier (`difflib`/`rapidfuzz`) before giving up. **Log the miss rate** — that number is the entire justification for Stage C, and you want it measured, not assumed.
- **Stage C — semantic fallback over 31k verses.** Embed all VI1934 verses. Benchmark `intfloat/multilingual-e5-base`, `AITeamVN/Vietnamese_Embedding`, and LaBSE against your held-out quote pairs. At 31k × 768 fp32 that's ~95 MB (~24 MB int8). **Do not reach for FAISS** — a NumPy matrix and one `argmax` over 31k rows is single-digit milliseconds. Shipping a `.npy` keeps the whole thing deployable on a free tier, which is itself worth saying out loud.
- **Stage D — routing with abstention.** `exact → fuzzy(τ) → retrieval(τ) → abstain`. Abstention is the point (§4.2): when confidence is low, translate the quote normally rather than injecting the wrong verse. A system that knows when it doesn't know reads as markedly more mature.
- **Stage E — measure.** Re-run §6.3 and §6.4 with retrieval on and off. That is the "found a limitation and fixed it" arc, with numbers attached.

---

## 9. CV narrative to aim for

Bracketed values are the deliverables of §6 and §8. Everything unbracketed is already earned.

> **Bible Commentary Translator** — EN→VI domain-specialised translation system, deployed and in weekly use.
> - **Cut post-editing effort on a real translation workload by [X]% (character-level HTER [A] → [B]); [C]% of paragraphs now ship without edits**, measured on a document-level held-out set of human translations frozen before the model existed.
> - Curated a 2.6k-pair parallel corpus from 39 hand-translated study guides by scraping and structurally aligning English commentary against the Vietnamese Bible; added semantic alignment verification after finding that count-based checks miss index drift.
> - Two-stage LoRA adaptation of Qwen3.5-0.8B (general EN→VI, then commentary domain). **+0.038 COMET-Kiwi over base (0.767 → 0.805), matching the human reference translation (0.809) at a fifth of the parameters of the strongest baseline.** Benchmarked against 5 systems including VinAI Translate and TranslateGemma-4B on 19k PhoMT pairs.
> - Built a quote-grounding pipeline that locates scripture excerpts in the canonical Vietnamese Bible and constrains the model to reuse them verbatim — **92.9% verbatim fidelity**, versus [X]% for a generic MT baseline that cannot do this at all.
> - Diagnosed a silent fallback that fed the model verses provably not containing the target quote; added validation and abstention, then embedding retrieval over all 31k Vietnamese verses, recovering [W]% of previously-fabricated quotes.
> - Found the block parser was capturing one scripture anchor per paragraph when **50.7% of quoted paragraphs contain more than one**; redesigned extraction around anchor / sub-phrase / cross-reference tiers, recovering [V] quotes per chapter previously translated by hand.
> - Batched a per-block sequential pipeline into padded batches: [N]× faster per chapter. Output streams into styled Google Docs; [N] family members use it weekly.

---

## 10. Sequenced plan

Resequenced in revision 3. Two things moved: **freezing the clean test set is now the first task in the project** (§6.2 — the window closes the moment you translate with v1), and **multi-quote handling (§5.7) is promoted into its own phase** because you identified it as the biggest reduction in your own workload.

### Phase 0 — Repository foundation + freeze the clean set (0.5–1 day)
- [ ] **Tag 6–8 of the 39 study guides as `test` and write the manifest (§6.2). Do this before you translate anything else with the model.** Ten minutes, irreversible if skipped.
- [ ] Add a `provenance` field to the document manifest: `human_from_scratch` for all 39 existing docs.
- [ ] `git init`; commit current state (with outputs) as baseline.
- [ ] Privacy audit (§7.3.4) — **before any public push.**
- [ ] `.gitignore`, `nbstripout`, pin dependencies (§4.10).
- [ ] Move Drive folder ID and model IDs to `.env`.

### Phase 1 — Instrument what already works (1 day) ★★ do this first
Tiny diffs, immediate payoff. None of these require restructuring.
- [ ] Log every §4.1 fallback. **Count them on Hebrews 12.**
- [ ] Add the §4.2 extraction validity check (2 lines) — pure string containment per §2.3.
- [ ] Add the §4.3 quote-honored check (3 lines).
- [ ] Fix `max_new_tokens` (§4.4); inspect the existing doc for truncation.
- [ ] **Set up char-HTER now (§6.1), even at n=1.** Capture `(model_output, your_edit)` per block from the next chapter you do by hand. The metric is worthless retroactively and free going forward.
- [ ] **Milestone: you can state your scripture-fidelity rate, your fallback rate, and your baseline post-editing effort.**

### Phase 2 — Multi-quote (2–3 days) ★★ largest workload reduction
- [ ] **First, and before writing anything: the `n_en` vs `n_vi` histogram over the 39 study guides (§5.7.3 step 7).** One loop, no model. It sizes everything below.
- [ ] `find_all("strong")` → `block["bold_quotes"]: list[str]`; dedupe, sort longest-first (§5.7.3 steps 1–2).
- [ ] Tier-2 shortcut: resolve anchor-substring spans inside the already-extracted Vietnamese phrase before calling the model (§5.7.3 step 3).
- [ ] Prompt 2 takes N constraints; measure honor rate vs N (§6.7). Fall back to deterministic post-hoc substitution if it degrades.
- [ ] Curator: positional pairing when `n_en == n_vi`, skip and log otherwise (§5.7.3 step 6).
- [ ] **Milestone: char-HTER drops measurably, and you know how many quotes are tier 3 — i.e. how much Phase 5 is actually worth.**

### Phase 3 — Extract the package (2–3 days)
- [ ] Move the duplicated scrapers (§7.1) into `src/bct/sources/`; both notebooks import them. **Do this as part of Phase 2 if the multi-quote change forces you to edit the parser in two places — that duplication is exactly what will bite.**
- [ ] `build_bible_db.py` → `bible.sqlite`, all 66 books (§5.5).
- [ ] Complete `VI_TO_EN_BOOKS` (§5.4).
- [ ] Batch extraction and smoothing (§3) — `padding_side` is already set, and Phase 2 gives batching real work to do.
- [ ] Fix the Google Docs writes via local index tracking (§4.6).
- [ ] Service-account auth (§7.3.5); add checkpoint/resume (§4.7).
- [ ] `cli.py` — `bct translate "Hebrews 12:1-13"` runs outside Colab.

### Phase 4 — Full evaluation (2–3 days) ★★ highest CV value
- [ ] Split per §6.2; metrics §6.1 and §6.3–§6.7.
- [ ] Baseline comparison table (§6.4) — **the README centrepiece.**
- [ ] Ablate `repetition_penalty` (§4.5) against the fidelity metric.
- [ ] **Milestone: you can state, with a number, whether stage-2 fine-tuning helped on the actual task — and how many characters per chapter you no longer type.**

### Phase 5 — Retrieval (2–3 days)
- [ ] Stages A–E of §8. Re-run Phase 4 metrics with retrieval on/off.
- [ ] Scoped by Phase 2's tier-3 count — you will know its value before starting.
- [ ] **Milestone: the "found a limitation and fixed it" arc, quantified.**

### Phase 6 — Retraining with fixed data (2 days, optional)
- [ ] Fix §5.1–§5.3, rebuild the dataset **with multi-quote records from Phase 2**, re-run stage 2, re-measure with Phase 4.
- [ ] Train on `post_edited` documents; evaluate on the frozen clean set only (§6.2).
- [ ] Worth doing only *after* Phase 4 exists — otherwise you cannot tell whether it helped.

### Phase 7 — Deployment (1–2 days) — full detail in §12
- [ ] **Telegram bot on your own machine, long polling** (§12.2). No public URL, no tunnel. Real users, zero cost, one weekend.
- [ ] One-paragraph public demo on a free HF Space (§12.1) — the CV link.
- [ ] Log every request (reference, latency, fallback count, fidelity rate). That log is both your "N users" evidence and your production-error corpus.
- [ ] 👍/👎 per block feeds the next fine-tuning round. Say so in the README.
- [ ] Move the worker off your PC only if the always-on dependency becomes annoying (§12.3).

### Phase 8 — Presentation (1 day)
- [ ] README with §6 tables, architecture diagram, honest limitations.
- [ ] State the §2.3 design position explicitly: constrained to VI1934, does not paraphrase scripture.
- [ ] HF model card linking the methodology.

**Total: ~3–3.5 focused weeks.** The ordering logic: Phase 0 takes ten minutes and is the only step that becomes impossible later; Phase 1 is one day and produces the numbers that make everything after it interpretable; Phase 2 is where your own workload actually drops.

---

## 11. Open questions

1. **Is stage 1 reproducible?** That notebook still isn't here. Without it, "sequential domain adaptation" rests on an HF artifact you can't rebuild. Recover or re-run it.
2. **Will the repo be public?** Determines how urgent §7.3.4 is, and whether the study guides can ship as a dataset.
3. **Are the 39 study guides yours to publish?** A public dataset is a strong asset — only if you hold the rights.
4. **How many of the 39 documents are Old Testament?** Determines whether §5.4 recovers real training data.
5. **Did the Hebrews 12 output show truncation?** You can answer this by scrolling the generated doc — it directly confirms or clears §4.4.
6. **Runtime target after Colab** — free HF Space (cold starts), small VPS (~$5/mo, steady), or your machine with a tunnel? You already export GGUF `q8_0`, so llama.cpp on a small box is realistic. Changes the Phase 7 design.
7. **Coherence window** — is `scripture_anchor` the right glossary-reset boundary, or should it be per document? Needs one look at real output.
8. **Second annotator?** Even 50 blocks checked by a family member gives an inter-annotator agreement number, upgrading §6.4 from "my metric" to "a validated metric."
9. **How do you currently post-edit?** (new) Char-HTER needs the model output and your final version as two separate strings. If you edit the generated Google Doc in place, the pre-edit version is gone. Keeping a copy of the raw output — or using Docs revision history — is the difference between having the metric and not. Worth settling before the next chapter you translate.
10. **In the multi-quote Vietnamese paragraphs, do the `“…”` spans appear in the same order as the English bold spans?** (new) §5.7.3 step 6 assumes yes. Almost certainly true for sub-phrase re-quotes, less certain where Vietnamese word order diverges. The histogram in Phase 2 answers it cheaply, and it decides whether positional pairing is safe or needs a similarity fallback.
11. **How many of the 39 documents would survive as tier-3 evidence?** (new) I measured multi-quote rates on Enduring Word's English side only. The Vietnamese side of your own translations is the ground truth for whether you *already* translate those extra quotes by hand — which is the real measure of the workload §5.7 removes.
12. **Does your family use Telegram?** (new) Decides §12.2 vs the Google Form fallback. Do not pursue a Zalo Official Account for three users — the verification process costs more than the whole deployment.
13. **How long did Hebrews 12 actually take on Colab?** (new) Every runtime estimate in §12 scales from this one number, and you can read it off the run you already did.

---

## 12. Deployment

Yes, this is realistic — and easier than most ML projects, because of one property yours has: **the job is asynchronous and the output surface already exists.** Nobody waits for a response; they open a Google Doc later. You therefore need no low latency, no high uptime, and no UI beyond a text box. Most deployment pain comes from requirements you do not have.

### 12.1 Build two deployments, not one

They have opposite requirements, and trying to serve both from one process is what makes this hard.

| | **Family product** | **Public demo** |
|---|---|---|
| Users | 3 people you know | A recruiter, once, for 30 seconds |
| Input | `Hebrews 12:1-13` | One pasted paragraph |
| Runtime budget | 5–45 min is fine | Seconds |
| Output | A styled Google Doc | Text on screen, side by side |
| Uptime | "usually works" | Must work when clicked |
| Visibility | Private | Public |

A whole chapter cannot run inside a web request; a recruiter will not wait for a Google Doc. Build both on the same `src/` package — this is the concrete payoff of Phase 3.

**The demo is the easy half.** One paragraph = one extraction call + one smoothing call, a few seconds even on a free CPU tier. Show four panes: English input · the located VI1934 verse · the extracted phrase · the final Vietnamese with the scripture highlighted. That view *is* the project's thesis, and it is the link that goes on the CV.

### 12.2 Start here — Telegram bot on your own machine

Do this before evaluating any cloud platform.

**Telegram bots support long polling**: the bot connects *outward* to Telegram and asks for messages. No public URL, no ngrok, no port forwarding, no static IP, no firewall rules, no TLS certificate. It runs from a laptop behind home NAT. That removes most of what normally makes self-hosting tedious.

```
Family types in Telegram → bot on your PC picks it up → pipeline runs
    → writes the Google Doc → bot replies with the link
```

Cost zero; roughly 30 lines with `python-telegram-bot`; the only constraint is that your machine is awake. For three people doing a chapter or two a week that is genuinely sufficient, and it is a real deployment — your "N active users" metric starts the day this works.

**If the family does not use Telegram**, use a Google Form writing to a Sheet, with the worker polling the Sheet. No bot approval from anyone. Do not pursue a Zalo Official Account for three users.

### 12.3 Moving the worker off your PC, later

Timings are estimates — **measure your actual Colab runtime for Hebrews 12 first**; everything below scales from it. Verify current free-tier terms yourself, as they change often.

| Option | Cost | Chapter runtime | Catch |
|---|---|---|---|
| **Your PC + Telegram** | Free | Your hardware | Machine must be on |
| **Serverless GPU** (Modal, RunPod) | Per-second, scale-to-zero; likely cents/chapter | Minutes | Cold start pulls the weights — bake into image or cache volume |
| **GitHub Actions** | Free minutes | 30–60+ min, CPU only | Viable for async work; built-in secrets; unlimited minutes only on a public repo |
| **HF Space, free CPU** | Free | Slow; sleeps when idle | Right for §12.1's demo, wrong for chapters |
| **Small VPS** | ~$5/mo | Slow, CPU only | Always on, but you now operate a server |

Your `q8_0` GGUF export matters here — ~0.85 GB, and llama.cpp on CPU is what makes the cheap tiers usable at all. That work is already done.

### 12.4 The four real blockers

1. **Auth, not compute.** `auth.authenticate_user()` is Colab-only and dies the moment you leave. You need a Google **service account**, and the non-obvious step: it has its own email address, and **the target Drive folder must be shared with that address** or it cannot write. Half an hour. Already Phase 3 / §7.3.5.
2. **Scraping from a datacenter IP.** httlvn and Enduring Word may throttle or block cloud IPs — works from home, fails in production. The SQLite Bible cache (§5.5) removes httlvn from the request path entirely; this promotes it from nice-to-have to deployment prerequisite.
3. **Secrets.** The service-account JSON must never enter the repo. Platform secrets or env vars; ties into §7.3.4.
4. **Cold starts.** Downloading 0.85–1.6 GB of weights per invocation dominates runtime on scale-to-zero platforms. Bake the model into the image or mount a persistent volume.

---

## 13. Scaling to Qwen3.5-2B: the training protocol

*Appended after your question: "for each model, do I train on `A_train`, evaluate on `A_test`, then further train again from the stage-1 checkpoint on `A_train + B`, re-evaluate and compare?"*

### 13.1 Verdict on your understanding

**Yes — and you got the hard part right.** Restarting from the **stage-1 checkpoint** rather than continuing to train the `A_train` model on `B` is the correct instinct, and it is the part most people get wrong. If you continued training the finished `A_train` model on `B`, the second model would have seen `A_train` twice, at a different point in the learning-rate schedule, with inherited optimizer state. When it scored better you would not know whether `B` helped or whether the extra pass over `A_train` did. Restarting isolates the variable.

One structural correction: **this is not a chain, it is a grid.**

### 13.2 You are varying two things, so run the 2×2

Model size and training data are two independent questions. Written out:

| Run | Base | Stage 2 data | Answers |
|---|---|---|---|
| R1 | Qwen3.5-0.8B | `A_train` | The honest baseline |
| R2 | Qwen3.5-0.8B | `A_train + B` | Does `B` help? |
| R3 | Qwen3.5-2B | `A_train` | Does size help? |
| R4 | Qwen3.5-2B | `A_train + B` | Do they compound, or does one substitute for the other? |

All four are graded on the **same frozen `A_test`**, with the **same `A_val`** used for checkpoint selection. R1 is not the model you already have — the existing 0.8B saw all 39 documents and is permanently disqualified as a baseline (§6.2, the equal-footing rule). It must be retrained on `A_train` to earn the row.

**The cost is lower than it looks.** Stage 1 (PhoMT, ~19k pairs) is the expensive run, and it is needed **once per base model** — twice total, and the 0.8B one you have already paid for. Stage 2 is 39 documents; on a LoRA that is minutes, not hours. So the grid is **2 stage-1 runs and 4 stage-2 runs**, and the marginal cost of going from your proposed 2 runs to the full 4 is close to nothing. Run the grid.

If GPU budget does become the constraint, do the 0.8B row first (R1, R2). It is cheap and it answers "does `B` help?" on its own. Only then spend the 2B budget — and if `B` clearly hurt at 0.8B, you may only need R3.

### 13.3 Rules that make the four numbers comparable

1. **Fresh adapter every time.** Merge stage 1 into the base weights, then initialise a **new** LoRA for stage 2. Never reuse a stage-2 adapter across runs.
2. **Identical hyperparameters** across all four — rank, alpha, LR, schedule, max epochs, seed. The moment you tune the 2B differently you are comparing recipes, not models. If you must tune, tune on `A_val` and say so.
3. **`A_val` selects the checkpoint in every run.** Not "last epoch" in one and "best epoch" in another.
4. **`A_test` is never opened until the run is finished.** Once per run, at the end. Looking at it between runs and adjusting is how a frozen test set quietly stops being frozen.
5. **Epochs vs. steps.** `A_train + B` is a larger set, so at fixed epochs it also gets more optimizer steps. Fix **epochs** with early stopping on `A_val` — that matches what you would actually deploy — and state the claim accordingly: *"more data, trained to convergence, helps/does not help."* That is the decision you are actually making. A compute-matched variant (fixed step count) is an appendix experiment, not the headline.
6. **Snapshot `B`.** `B` grows every week. A run trained on "B as of 2026-09-14" is not reproducible unless you record which documents that was. Write a manifest of document IDs plus a hash into the run's config — this is why §10 Phase 0 puts a `provenance` field on every document.

### 13.4 Report it with floors and a ceiling

Four numbers alone mean nothing to a reader who does not know the task. Add three reference rows to the same table, on the same `A_test`:

- **Untuned base model, zero-shot** — the floor. Shows what fine-tuning bought.
- **Google Translate** — the free-alternative floor. This is the row a hiring manager silently asks about.
- **Your own hand translation** — by construction the ceiling, distance 0.

Metrics per row: char-level TER (§6.1), scripture fidelity (§6.4), extraction accuracy (§6.3), and **tokens/sec on your own hardware**. That last column is not decoration — §12 puts the worker on your PC, so if the 2B wins by two points of TER and runs three times slower, that is a real trade-off and the table is where you make it visible.

### 13.5 What the result means either way

R2-vs-R1 is a genuine experiment on **whether training on your own post-edited output helps or hurts**. `B` is not clean data: it is model output that you corrected, so it carries the model's own habits back into the next model. The plan has flagged this as ossification risk. Now it becomes measurable.

- **If `B` helps**, the bootstrap loop in §6.2 is validated and the project has a flywheel: translate → post-edit → retrain → translate faster.
- **If `B` hurts**, you have caught error ossification with evidence, and the fix is known (weight `A_train` higher, or restrict `B` to blocks you edited heavily — the low-HTER blocks are the ones the model already agreed with itself about, and they teach it nothing).

Both outcomes are publishable on a CV. The second is more interesting than the first, and most people never run the experiment that would find it.

### 13.6 Optional, only if you want the sharper claim

The grid answers *"is `A_train + B` better than `A_train`?"* — a fair question, since more data is genuinely the treatment. It does not answer *"is a post-edited example worth as much as a hand-translated one?"*, because the winning set is also simply bigger. If you want that claim, add one run: train on a random subset of `A_train + B` sized exactly `|A_train|`. Nice-to-have. Do not let it delay the grid.

---

## 14. Setup order — what to do before Phase 1 starts

*Appended after your question: "before I start, is there anything I need to set up, and in what order?"*

The honest summary: **almost nothing here is urgent, except two things that stop being possible.** Order the setup by what closes, not by what feels foundational.

### 14.1 Today — the two closing windows (about one hour)

**Step 1. `git init` and commit everything verbatim.** Five minutes. Commit *with* notebook outputs this once — the Hebrews 12 run, the COMET tables and the alignment report are evidence, and they exist only in those outputs. Do not tidy anything first; the messy baseline is the start of the history a reviewer wants to read (§7.3.1, §7.3.6).

**Step 2. Freeze the test set (§6.2).** Ten minutes, and the only step in this entire plan that becomes impossible later. Pick 6–8 of the 39 study guides, write their IDs into a manifest file, commit it, and never train on them.

Selection matters more than people expect. Do not take eight consecutive lessons:

- **Span the canon** — if all eight are Pauline epistles, you have measured your model on epistles.
- **Span document length** — short and long blocks fail differently.
- **Span your own timeline.** Your translation of lesson 5 and your translation of lesson 72 are not the same quality of Vietnamese; if the test set is all early work, you are grading against your weakest references.

Record a content hash per document alongside the ID. In two months you will want to prove the test documents were not silently edited, and a hash is the only thing that can.

**Step 3. Decide, right now, how you post-edit (open question §11.9).** This is the second closing window, and it is easy to miss because nothing breaks. If the next chapter is written into a Doc and you edit that Doc in place, the raw draft is destroyed and its post-editing effort is unmeasurable forever. The fix is one line: **dump raw model output to a `.jsonl` next to the Doc, keyed by block.** Do it before the next run, not after.

While you are there, open the Hebrews 12 Doc's **revision history**. If your edits are in it, the original draft may be recoverable, and you would gain a data point from a chapter already finished. Ten minutes to check, and it either works or it does not.

### 14.2 This week — six answers that cost no code (about one hour)

Every one of these changes what you build, and all six can be answered by looking at something you already have. Answering them now prevents building the wrong thing.

| § | Question | How you answer it | What it decides |
|---|---|---|---|
| 11.1 | Is stage 1 reproducible? | Find, or fail to find, the notebook | **See §14.5 — this one can stall §13** |
| 11.13 | How long did Hebrews 12 take? | Read it off the run you already did | Every runtime estimate in §12 |
| 11.5 | Did Hebrews 12 truncate? | Scroll the generated Doc | Confirms or clears §4.4 |
| 11.2 / 11.3 | Public repo? Do you hold rights to the 39 guides? | Your decision; ask family | Urgency of §7.3.4; whether the dataset ships |
| 11.4 | How many of the 39 are Old Testament? | Count them | Whether §5.4's book map recovers real data |
| 11.12 | Does the family use Telegram? | Ask them | §12.2 bot vs Google Form |

### 14.3 Environment — the actual setup work (half a day)

In dependency order:

1. **A local Python environment that is not Colab.** `pyproject.toml` plus a **pinned** `requirements.txt` (§4.10). Pin now, while the versions still work; an unpinned bleeding-edge dependency is a reproducibility bug that surfaces months later, when it is expensive.
2. **`.gitignore` before the second commit** — `data/`, `*.csv`, `.env`, model weights, `__pycache__`. Fifty megabytes of regenerable CSV, committed once, is in every clone forever.
3. **`.env` and `.env.example`.** Move the Drive folder ID and the model IDs out of the notebooks (§7.3.4). This is what makes the privacy audit tractable rather than an archaeology exercise.
4. **`nbstripout --install`** — *after* the one snapshot commit with outputs, never before.
5. **Google service account, and share the Drive folder with its email address** (§7.3.5). Roughly an hour. This is the real portability blocker: it gates running outside Colab at all, which means it gates Phase 3, all of Phase 7, and every local test of the Docs writer. The step people miss is not creating the account — it is that the account has **its own email address**, and the target folder must be shared with that address, or every write fails with a permission error that looks like a bug in your code.
6. **Privacy audit (§7.3.4)** — strictly required only before a *public* push, but far cheaper now than after `git filter-repo`.

### 14.4 Start this in the background on day one

**Build `bible.sqlite` (§8 Stage A).** All 66 books, VI1934 + NKJV. It is listed under Phase 3, but it is the one prerequisite that is **wall-clock-bound rather than attention-bound** — a polite scrape is an afternoon of waiting, not an afternoon of working. Start it while you do §14.1–§14.3.

It is also a hard deployment prerequisite rather than a nice-to-have: §12.4 blocker 2 is that httlvn may refuse datacenter IPs, and this cache removes httlvn from the request path entirely. Everything downstream reads from it.

### 14.5 The one dependency that can actually stall you

**If the stage-1 notebook is genuinely gone, §13 does not start.** The 2×2 grid needs a stage-1 (PhoMT) checkpoint *for the 2B base*, and that is a run you have to perform, not a file you can copy from the 0.8B. So open question §11.1 is not bookkeeping — it sits on the critical path of the entire scaling plan.

Check for it before committing to §13. If it is unrecoverable, the recipe has to be reconstructed from the PhoMT dataset and whatever hyperparameters survive in the analysis notebooks — a day of work you would much rather discover now than in week three. Whatever you find, **write the stage-1 recipe into the repo as a script this time.** It has to run at least twice more.

### 14.6 The whole thing, in order

```
Day 0  (1 hr)   git init + commit verbatim
                Freeze test set + manifest + hashes        <- window closes
                Raw-output .jsonl before next run          <- window closes
                Check Hebrews 12 revision history
Day 0  (bg)     Kick off the bible.sqlite scrape
Day 0  (1 hr)   Answer the six questions in 14.2
Day 1  (1/2 d)  pyproject + pinned reqs, .gitignore, .env,
                nbstripout, service account + folder share
Day 1  (1 hr)   Locate the stage-1 notebook (14.5)
Day 1           Privacy audit, if the repo will be public
--------------- setup ends; Phase 1 begins ---------------
```

That is Phase 0 of §10, with the closing windows pulled to the front and the scrape moved earlier because it runs unattended.

### 14.7 What not to set up yet

Each of these costs time now and buys nothing, because it is either scoped by a measurement you have not taken or a decision you cannot yet make well:

- **No FAISS, no vector database.** §8 is 31k rows and one NumPy `argmax`. And Phase 2's tier-3 count tells you how much retrieval is worth *before* you build any of it.
- **No VPS, no serverless account, no HF Space.** Phase 7. §12.2 needs none of them, and §12.3's estimates need §11.13's number first.
- **No Zalo Official Account.** For three users, verification costs more than the whole deployment (§12.2).
- **No COMET infrastructure.** Phase 4. The 0.8B numbers already exist, and nothing before Phase 4 consumes new ones.
- **No 2B download, no GPU rental.** §13 is gated on §14.5 and on Phase 2's rebuilt dataset. Training the 2B on the current data would waste the run.
- **No repo restructure into `src/bct/`.** Phase 3 — and §10 says to do it exactly when Phase 2 forces you to edit the same parser in two places, which is the moment the duplication first costs you something.

---

## 15. How to organize this as a proper repo

*Appended after your question: "how do I organize everything like a proper repo?" §7.2 sketched a target layout; this section maps your seventeen actual files onto it and fixes the naming.*

### 15.0 First — a correction to §11.1, found while looking at the folder

`LoRA Fine-tuning Qwen3_5_(4B).ipynb` **is not a 4B notebook and is not stage 1.** It loads `phuclhp1922/qwen3.5_0.8B_translation_merged_16bit` and trains on top of it, pushing to `bct_qwen3.5_0.8B_lora`. That makes it **stage 2**, on the 0.8B, and its recipe is fully recorded:

| | |
|---|---|
| Base | `qwen3.5_0.8B_translation_merged_16bit` (the stage-1 artifact) |
| LoRA | `r=8`, `alpha=8`, `dropout=0`, language + attention + MLP layers |
| Optimiser | `adamw_8bit`, `lr=4e-5`, cosine, `warmup_steps=50`, `weight_decay=0.01` |
| Batch | 2 × grad-accum 4 = effective 8, `max_seq_length=2048`, `load_in_4bit=True` |
| Schedule | `num_train_epochs=2`, `max_steps=-1`, `seed=3407` |

So the revised picture: **the stage-2 recipe is recoverable, and the stage-1 *artifact* survives on the Hub — but the stage-1 *recipe* is still gone.** For the 0.8B that is survivable, since you can start from the merged checkpoint. For the 2B it is not: §13 needs a stage-1 run on a different base, and there is no recipe to copy. §14.5 stands, narrowed to exactly that.

Four things in that notebook are repo problems, not training problems, and they are why this section exists:

1. **`glob.glob('/content/*.jsonl')`.** The training set is *whatever happened to be sitting in the Colab session*. There is no record of which files those were. This is the single biggest reproducibility hole in the project, and it is precisely what §13.6's "snapshot `B`" rule exists to prevent. In repo terms: training data must come from a versioned path plus a manifest, never from a glob over a scratch directory.
2. **The WandB config does not describe the run.** It logs `"architecture": "Qwen3.5-4B"` and `"epochs": 1`; the code trains a 0.8B for 2 epochs. Your run history is currently mislabelled at the source.
3. **The filename says 4B** for a 0.8B notebook. That is §4.9's model-name footgun again, now in the training layer.
4. **No `eval_dataset`, no `load_best_model_at_end`.** §13.3 requires `A_val` to choose the checkpoint in every run. With this trainer config that is not possible yet — it needs adding before the grid, not during.

The good news: **WandB is already wired in** (project `bct-qwen-translation-vn`). Run tracking for §13's four runs is a solved problem; it just needs honest configs.

### 15.1 Where each of your seventeen files goes

```
bible-commentary-translator/
├── README.md                    ← does not exist yet; the CV artifact (§9)
├── LICENSE                      ← code only; see §7.3.7
├── PLAN.md                      ← stays at root
├── pyproject.toml               ← new
├── requirements.txt             ← new, PINNED (§4.10)
├── .gitignore                   ← new
├── .env.example                 ← new
│
├── src/bct/                     ← §7.2's layout, filled in over Phase 3
│
├── notebooks/
│   ├── 01_data_curation.ipynb          ← Data Curation.ipynb
│   ├── 02_finetune_stage1_general.ipynb    ← MISSING (§14.5, §15.0)
│   ├── 03_finetune_stage2_domain.ipynb ← "LoRA Fine-tuning Qwen3_5_(4B).ipynb"
│   ├── 04_eval_comet22.ipynb           ← COMET-22 Reference-based ...
│   ├── 05_eval_cometkiwi.ipynb         ← COMET-Kiwi Reference-free ...
│   └── 06_run_pipeline.ipynb           ← Agent in the Notebook.ipynb
│
├── configs/                     ← new; the fix for §15.0 items 1–2
│   ├── stage1_phomt.yaml
│   ├── stage2_domain_0.8b.yaml
│   ├── stage2_domain_2b.yaml
│   └── models.yaml              ← every HF repo id in one place (§4.9)
│
├── manifests/                   ← new; small, committed, high value
│   ├── documents.jsonl          ← the 39 guides: id, title, book, split, provenance, sha256
│   └── runs/                    ← one record per training run (§13.3 rule 6)
│
├── data/                        ← GITIGNORED
│   ├── raw/  interim/  processed/  bible.sqlite
│
├── artifacts/                   ← GITIGNORED; the 49 MB of PhoMT CSVs live here
│
├── results/                     ← COMMITTED, small, human-readable
│   ├── phomt_benchmark.md
│   ├── fidelity_hebrews12.md
│   └── figures/
│
├── scripts/                     ← build_bible_db.py, freeze_test_set.py, ...
├── tests/
└── docs/
```

Numeric prefixes on the notebooks are worth the rename: a reader can see the pipeline order without opening anything, and the spaces and parentheses in the current names are a nuisance on the command line and in CI.

### 15.2 The 49 MB of CSVs — the one real decision

Your eleven CSVs are not "intermediate data." They are **inference outputs from six systems**, and regenerating them costs GPU time you already spent. §7.3.3 called them regenerable; that was too glib.

But they should still not go into git as they are. Nobody reads five megabytes of rows, and once committed they are in every clone forever. Split them by what they are *for*:

| File(s) | Size | Where | Why |
|---|---|---|---|
| `outputs_PhoMT_*.csv` (5 baselines) | ~28 MB | `artifacts/phomt/`, gitignored | Raw per-row inference; evidence, not reading material |
| `output_PhoMT_qwen3.5-0.8b_lora_fine_tuning.csv` | 5.6 MB | same | same |
| `results_PhoMT_*.csv` (2) | ~14 MB | same | same |
| `outliers_PhoMT_*_COMET-Kiwi.csv` (3) | ~0.8 MB | `results/outliers/`, **committed** | Small, and you actually cite these |
| **Derived score table** | ~2 KB | `results/phomt_benchmark.md`, **committed** | This is what a reader wants |

The rule that generalises: **commit what is read, not what is produced.** Anything under about a megabyte that you cite can go in `results/`; the per-row dumps go to `artifacts/` with a `scripts/` entry saying how they were made and where the copies live (Drive, or Git LFS if you want them versioned).

The one thing you must not do is leave them at root untracked and forget them. Write their provenance into `results/phomt_benchmark.md` — which model, which checkpoint, which date — because in six months the filename is all you will have.

### 15.3 Fix the naming while you are moving things

Four inconsistencies are visible in a seventeen-file listing, which is exactly the kind of thing a repo layout is supposed to expose:

- `output_...` vs `outputs_...` vs `results_...` — three prefixes, no stated difference.
- `qwen3.5-0.8b` vs `qwen3_5_0_8b` — two spellings of one model.
- The notebook labelled `(4B)` trains a 0.8B (§15.0).
- Spaces and parentheses in filenames.

Pick one convention and apply it in the restructure commit — for example `{stage}_{dataset}_{model}_{metric}.csv`, lowercase, hyphens inside model names, underscores between fields. The specific convention matters far less than there being one. And put every HF repo id in `configs/models.yaml` so the 0.8B / 2B / 4B confusion has exactly one place it can be resolved.

### 15.4 The 39 study guides are not in this folder — and that is correct

They live on Drive. The repo should hold a **manifest, not the content**, at least until §11.3 (do you hold the rights?) is settled. `manifests/documents.jsonl`, one line per guide:

```json
{"id": "bai_30", "title": "...", "book": "Hebrews", "chapter": 12,
 "split": "test", "provenance": "human_from_scratch",
 "sha256": "...", "drive_id": "...", "n_blocks": 101}
```

That single file does a surprising amount of work: it *is* the frozen test set from §14.1, it carries the `provenance` field Phase 0 asks for, its hashes prove the test documents were never edited, and `runs/` records can reference it by hash so every training run states exactly what it saw — which is the fix for §15.0 item 1. It is small, it is text, it diffs cleanly, and it contains no third-party content, so it is safe to commit regardless of how §11.2 and §11.3 resolve.

### 15.5 Order of operations, so the history stays readable

Git tracks renames, but only if you let it see them as renames:

1. **Commit the current state verbatim first** (§14.1 step 1) — spaces, `(4B)`, root-level CSVs and all. This is the baseline, and it is what makes `git log --follow` work through the renames.
2. **`.gitignore` in its own commit, before the CSVs move.** If they are committed once at root, removing them later does not shrink the repository.
3. **The restructure as one commit that only moves files.** Use `git mv`, change nothing else. A commit that both moves and edits a file is a commit whose diff nobody can read.
4. **Then the content commits** — `configs/`, `manifests/documents.jsonl`, the README.

Steps 2 and 3 in the wrong order is the single mistake that is genuinely annoying to undo.

### 15.6 What makes it read as "proper" to a reviewer

Layout is the least of it. In rough order of how much they signal:

1. **A README that opens with the result**, not with installation instructions. §9's numbers, an architecture diagram, and an honest limitations section. This is the artifact; everything else is supporting material.
2. **`git clone && pip install -r requirements.txt && bct translate "Hebrews 12"` actually works.** A repo that only runs in its author's Colab session is a notebook dump with directories. This is what Phase 3 and the service account (§14.3) buy you.
3. **A commit history that shows the work** — finding the silent fallback, measuring it, fixing it, measuring again (§7.3.6). More persuasive than the code.
4. **`results/` with tables that the README cites and a script that regenerates them.**
5. **`tests/` with a handful of real tests.** Not coverage — the parser on a saved HTML fixture, the quote-containment check, one alignment case. Five tests that assert something specific read better than fifty trivial ones.
6. **No secrets, no stray IDs, no 50 MB of CSVs** (§7.3.4).

Layout is necessary and cheap. Items 1–3 are what a reviewer actually reads.

---

## 16. The list — what to do, in order, starting now

*Appended after your question: "so what should I do, in order, now?" This merges §14's setup order with §15's restructure into one executable sequence. Where they conflicted, §16.0 resolves it.*

### 16.0 A conflict in §15.5, resolved

§15.5 step 1 says commit the current state verbatim, "root-level CSVs and all." Step 2 says `.gitignore` must land before the CSVs move. Both cannot be true — a CSV committed once at root is in the history permanently, and deleting it later does not shrink the clone.

**The resolution: `.gitignore` is written before the first `git add`, not after the first commit.** "Verbatim" applies to the *notebooks* — do not clean them, do not strip their outputs, that history is evidence. It was never meant to apply to 49 MB of inference dumps. Your first commit should be five notebooks with outputs, `PLAN.md`, and `.gitignore` — roughly 2 MB, not 51 MB.

### 16.1 The sequence

**Session 1 — about one hour. Two of these close windows; nothing else in the project does.**

- [ ] 1. `git init`.
- [ ] 2. Write `.gitignore` **before staging anything**: `*.csv`, `data/`, `artifacts/`, `.env`, `__pycache__/`, `*.gguf`, `outputs/`.
- [ ] 3. `git add -A && git commit` — the baseline. Notebooks keep their outputs; nothing is tidied.
- [ ] 4. **Freeze the test set.** `manifests/documents.jsonl`: all 39 guides, each with `id`, `title`, `book`, `provenance: human_from_scratch`, `sha256`, and `split` — 6–8 marked `test`, ~4 `val`, the rest `train`. Span canon, length, and your own timeline (§14.1). Commit. **← irreversible if skipped**
- [ ] 5. **Add the raw-output dump** to the Agent notebook: write each block's model output to a `.jsonl` beside the Doc, keyed by block id. One line of code, and it must land before the next run. **← irreversible if skipped**
- [ ] 6. Open the Hebrews 12 Doc's revision history. If the pre-edit draft is there, you have recovered a free data point.

**Session 2 — about two hours, and it ends with something running unattended.**

- [ ] 7. Lift the scraper out of the notebooks into `scripts/build_bible_db.py`. The code already exists in both notebooks (§7.1) — this is a move, not a write.
- [ ] 8. **Start the scrape.** All 66 books, VI1934 + NKJV, into `data/bible.sqlite`. It runs for an afternoon without you. Everything below happens while it runs.
- [ ] 9. Answer the six questions in §14.2. One hour, no code, all six change what you build.

**Session 3 — about half a day. Environment.**

- [ ] 10. `pyproject.toml` and a **pinned** `requirements.txt` (§4.10). Pin from the versions in `03_finetune_stage2_domain.ipynb`'s install cell — `torch==2.8.0`, `trl==0.22.2`, `transformers==5.2.0` are already pinned there; the unsloth git installs are not, and those are the ones that will break.
- [ ] 11. `.env` and `.env.example`. Move the Drive folder ID and every HF repo id out of the notebooks.
- [ ] 12. `nbstripout --install` — now, and not before step 3.
- [ ] 13. Google service account; **share the target Drive folder with the service account's email address** (§14.3.5).
- [ ] 14. Privacy audit (§7.3.4) — mandatory only if the repo goes public, cheap only if done now.

**Session 4 — about two hours. Restructure, before Phase 1 edits anything.**

- [ ] 15. The move-only commit: `git mv` the five notebooks to `notebooks/0N_*.ipynb`, the CSVs to `artifacts/phomt/`, the three `outliers_*` files to `results/outliers/`. Change no file contents in this commit.
- [ ] 16. `configs/models.yaml` — every HF repo id in one place, so the 0.8B / 2B / 4B confusion has exactly one resolution point (§15.3).
- [ ] 17. `configs/stage2_domain_0.8b.yaml` — the recipe recovered in §15.0, written down. This is what replaces `glob('/content/*.jsonl')`.
- [ ] 18. `results/phomt_benchmark.md` — the derived score table, with provenance: which model, which checkpoint, which date. In six months the filename is all you will otherwise have.
- [ ] 19. README skeleton. It can be a stub; it just needs to exist so the repo stops reading as a folder.

**— setup ends here. Phase 1 (§10) begins. —**

### 16.2 Step 9's hardest question: where the stage-1 recipe actually is

§15.0 narrowed this: you need the *recipe*, not the artifact, and only for the 2B. Three places to look, cheapest first:

1. **WandB.** You logged to project `bct-qwen-translation-vn`. If stage 1 was logged there too, its run config carries the hyperparameters even though the notebook is gone. This is the most likely recovery and it takes five minutes.
2. **The Hub.** If you pushed a stage-1 *adapter* repo alongside the merged model, its `adapter_config.json` records rank, alpha, and target modules — and `training_args.bin`, if it was pushed, records the rest.
3. **Colab.** File → Open notebook → Recent, and your Drive's `Colab Notebooks/` folder.

If all three come up empty, reconstruct it: the stage-2 recipe in §15.0 is a reasonable starting point, PhoMT is a public dataset, and one run costs you a day. Either way, **write it into `configs/stage1_phomt.yaml` as you go.** It has to run again for the 2B, and possibly a third time.

### 16.3 What "setup is done" means

You are done when all four are true:

1. `git log` shows a baseline commit, a test-set commit, and a move-only restructure commit.
2. `manifests/documents.jsonl` exists, is committed, and marks 6–8 documents `test`.
3. The next pipeline run will write its raw output somewhere you can diff against your edits.
4. `data/bible.sqlite` exists, and a script can rebuild it.

Nothing else on this list blocks Phase 1. If a step is dragging — the service account, the privacy audit, the README — leave it and start Phase 1; those can be finished alongside. Only items 4 and 5 are genuinely urgent, and together they are about twenty minutes.
