# Bible Commentary Translator

English-to-Vietnamese translation of Bible commentary, grounded in the
Vietnamese 1934 scripture text.

Commentary is not ordinary prose. A paragraph quotes scripture, then discusses
it, and the quoted words are not free to be re-translated: Vietnamese Protestant
congregations read the 1926/1934 translation, so a quotation has exactly one
acceptable rendering -- the one already in that Bible. A general-purpose
translation system will paraphrase it, and the paraphrase is wrong however
fluent it is.

This project locates each quoted phrase in the canonical Vietnamese text and
constrains the model to reuse it verbatim, translating only the commentary
around it.

## How it works

```
Enduring Word commentary page
        |
        v
  parse into blocks          verse headings, quoted scripture, body paragraphs
        |
        v
  align quote -> VI1934      exact match, then fuzzy, then abstain
        |
        v
  translate the commentary   fine-tuned Qwen3.5, quote injected as a constraint
        |
        v
  styled Google Doc          + raw output kept for measurement
```

## Repository layout

```
src/bct/            the library; notebooks import from here
  sources/          scraping Enduring Word and the Vietnamese Bible
  corpus/           building and reading the local scripture database
  align/            matching an English quote to its Vietnamese verse
  pipeline/         extraction, translation, glossary, whole-chapter runs
  output/           Google Docs writer, Markdown fallback
  data/             turning finished translations into training data
  eval/             quote accuracy, scripture fidelity, COMET, edit distance
  cli.py            bct translate "Hebrews 12"

notebooks/          curation, fine-tuning, evaluation, pipeline runs
configs/            model ids and training recipes, as files rather than cells
manifests/          which documents exist, and which split each belongs to
scripts/            one-off jobs (building the scripture database)
results/            committed tables and figures
artifacts/          large inference dumps -- gitignored, kept locally
data/               scripture database and working files -- gitignored
tests/
PLAN.md             design decisions, open questions, sequencing
```

## Two environments

This is the part that surprises people, so it is stated plainly:

| | Installed from | Contains |
|---|---|---|
| **Local** | `pyproject.toml` | Scraping, parsing, alignment, Google Docs output |
| **Colab / Kaggle** | `requirements-colab.txt` | torch, unsloth, trl, transformers, COMET |

`torch` is **deliberately absent** from `pyproject.toml`. Training runs where
the GPU is, and Colab and Kaggle ship their own CUDA-matched build; pinning a
version locally fights the platform and does not resolve on recent Python.

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev,eval]"
pytest
bct --help
```

Copy `.env.example` to `.env` and fill it in. `.env` is gitignored and must
stay that way -- it holds the Google service-account path and the Drive folder
the pipeline writes into.

### After cloning: re-install nbstripout

Notebooks are stored **without outputs**. That is enforced by a git filter, and
**git filters live in `.git/config`, which is not cloned.** A fresh clone will
happily commit 900 KB of embedded outputs unless you run:

```bash
pip install -e ".[dev]"
nbstripout --install --attributes .gitattributes
```

This is the single easiest thing to forget in this repo.

## Notebooks

| Notebook | Purpose |
|---|---|
| `01_data_curation` | Scrape and align commentary against finished translations |
| `02_finetune_stage1_general` | General EN-VI adaptation on PhoMT |
| `03_finetune_stage2_domain` | Bible-commentary adaptation on top of stage 1 |
| `04_eval_comet22` | Reference-based scoring |
| `05_eval_cometkiwi` | Reference-free scoring |
| `06_run_pipeline` | Translate a chapter end to end |

`02_finetune_stage1_general` is **not in the repository.** The stage-1 weights
exist on the Hugging Face Hub, but the notebook that produced them has not been
located, so the recipe is currently unrecoverable. This matters for anything
that starts from a different base model, which needs its own stage-1 run. See
`PLAN.md` sections 14.5 and 16.2.

### Training on Colab or Kaggle

The notebooks are thin. They clone this repository, install the training
requirements, and call into `bct`:

```python
!git clone https://github.com/<user>/bible-commentary-translator.git
%cd bible-commentary-translator
!pip install -q -r requirements-colab.txt
!pip install -q -e . --no-deps

from bct.train import run_stage2          # not implemented yet
run_stage2("configs/stage2_domain_0.8b.yaml")
```

Environment bootstrap stays in the notebook rather than moving into the
package: it differs per platform and is the cell most likely to need editing
when a dependency breaks. On Kaggle, enable Internet in the notebook settings
first, or the clone and the installs both fail.

## Data and provenance

The study guides this system is trained on are hand-translated documents held
in Google Drive. They are **not** in this repository. What belongs here is
`manifests/documents.jsonl` -- one line per document recording its identifier,
its content hash, how it was produced, and which split it belongs to.

The distinction the manifest records is the one that matters most: a document
translated by hand before this model existed is an independent reference, and a
document produced by the model and then corrected is not. Only the first kind
can honestly be used to measure the model.

## Sources and attribution

- Commentary: [Enduring Word](https://enduringword.com), (c)1996 David Guzik.
  Retained in generated output.
- Vietnamese scripture: the 1926/1934 Vietnamese Bible.
- English scripture: NKJV, as quoted by the commentary.

These are third-party works, included by reference. The MIT license below
covers the code in this repository and nothing else.

## License

MIT. See [LICENSE](LICENSE).
