# Processing Engine — Design & Heuristics ⚙️

This document describes the internal logic of the CSV Processing Engine.
The engine is designed to reliably ingest **messy, human-generated CSV files**
without requiring manual configuration or strict adherence to RFC standards.

The primary goal is **correct structure inference**, not blind syntactic validity.

## Design Principles

1. **Prefer coherent data over perfect formatting**
2. **Avoid false positives on non-CSV text**
3. **Fail safely on ambiguous inputs**
4. **Optimize for real-world CSVs, not ideal ones**

---

## 1. Processing Pipeline Overview

The engine follows a deterministic, multi-stage pipeline:Detect → Decide → Parse → Sanitize


### Stages

1. **Dialect Detection**
   - Identify delimiter and quoting strategy via statistical consistency.
2. **Layout Classification**
   - Decide whether the file is:
     - Horizontal (tabular)
     - Vertical (key-value stream)
3. **Adaptive Parsing**
   - Select the appropriate parsing strategy.
4. **Sanitization**
   - Neutralize CSV / Formula Injection before output generation.

Each stage is independent and testable.


## 2. Dialect Detection via Consistency Scoring

Instead of relying on trial-and-error parsing, the engine evaluates candidate
dialects using a **Consistency Score (Q)**.

$Q(\theta) = P(x,\theta)\times T(x,\theta)$

Where:
- `θ` is a candidate dialect
- `x` is a fixed-size sample (default: first 8KB)
- `P` measures **structural consistency**
- `T` measures **semantic consistency**

---

## 3. Pattern Score (P) — Structural Consistency

### Intuition

Well-formed CSV files tend to have **stable row widths**.
Messy or non-CSV text tends to produce jagged row lengths.

The Pattern Score rewards:
- A dominant row width
- Multiple columns
- Repeated structural patterns

### Formula

$P = \frac{1}{K} \sum_{k=1}^{K} N_{k} \frac{L_{k} - 1}{L_{k}}$

Where:
- `K` = number of distinct row length patterns
- `$N_{k}$` = number of rows with length `Lk`
- `$L_{k}$` = row length

### Key Behaviors

- Single-column layouts (`L ≈ 1`) are heavily penalized  
  → prevents plain text files from being misclassified as CSV.
- Files with a dominant row width score higher than jagged files.

---

## 4. Type Score (T) — Semantic Consistency

### Intuition

A structurally valid CSV is not necessarily meaningful.
Columns containing random strings should not dominate cleaner datasets.

### Type Inference Strategy

Cells are evaluated using a **regex precedence chain**: Integer → Float → Date → String

### Formula

$T = \frac{1}{M} \sum_{cells} \mathbb{I}(\text{cell} \in \text{KnownTypes})$


Where:
- `M` = total number of evaluated cells
- `I` = indicator function (1 if a known type matches, else 0)

### Implementation Notes

- Empty values are treated as neutral (neither positive nor negative).
- If multiple regexes match, the **highest-precedence type wins**.
- Type scoring is column-agnostic by design to tolerate sparse or drifting schemas.

This prevents perfectly aligned but meaningless data from winning dialect selection.

---

## 5. Vertical Layout Detection (Key-Value Streams)

Some CSV-like inputs represent records vertically:
```text
name, John age, 23 city, NY name, Mary age, 30 city, LA
```

### Detection Heuristics

A file is classified as *vertical* if:

1. **Average row width ≈ 2**
2. **Column-0 repetition ratio > 0.3**

Rationale:
- In tabular CSVs, column 0 is often unique.
- In key-value streams, column 0 repeats as field names.

---

## 6. Vertical Transposition Algorithm

The vertical parser operates as a **single-pass state machine**.

### State

- `current_record`: OrderedDict
- `fields`: insertion-ordered schema list
- `anchor_key`: first detected key in the file

### Boundary Detection

A new record is detected when:
- The current key equals `anchor_key`
- AND `current_record` already contains that key

### Schema Evolution

- New keys are appended dynamically.
- Missing keys in earlier records are simply absent.

This allows schema drift without invalidating prior records.

---

## 7. Sanitization — CSV / Formula Injection

Attack Vector: CSV Injection (RFC 7111 limitation). Malicious cell values (e.g., =cmd|' /C calc'!A0) can execute code when opened in Excel.

​Sanitization Logic:
Treat the CSV as untrusted user input.
​Trigger Detection: Check if cell starts with =, +, -, @.
​Neutralization: Prepend a single quote '.
​Input: =SUM(1+1)
​Output: '=SUM(1+1) (Rendered as literal text by spreadsheets).

---

## 8. Complexity Analysis

### Time Complexity

| Component | Complexity | Notes |
|---------|------------|------|
| Dialect Detection | O(1) | Fixed sample size |
| Layout Detection | O(1) | First N rows only |
| Parsing | O(N) | Linear scan |
| Sanitization | O(N × M) | M = avg cell length |

### Space Complexity

| Component | Current | Future |
|---------|--------|--------|
| Parsing | O(N) | O(1) with generators |
| Vertical Transpose | O(N) | Streamable |

---

## 9. Known Limitations

- Very large files (>500MB) may cause memory pressure
- Two-column non-key-value datasets may be misclassified
- Type inference is heuristic, not schema-strict

These trade-offs are intentional.

---

## 10. Reference & Theoretical Basis ​📚

This engine is based on:

> *Wrangling Messy CSV Files by Detecting Row and Type Patterns*  
> Gerrit J.J. van den Burg et al., The Alan Turing Institute (2018)  
> arXiv:1811.11242

The implementation adapts the paper’s principles for production use,
prioritizing **robustness over formal correctness**.
