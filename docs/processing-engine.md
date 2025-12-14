# CSV Processing Engine

The engine performs:
- delimiter detection
- schema inference
- key-value expansion
- CSV injection prevention
- data normalization
- anomaly detection & logging

## Schema Inference Algorithm

Example input:
Name, John
Age, 23
Name, Mary
Age, 30
City, NY

Algorithm:
1. Parse rows as key-value pairs.
2. Build a set of all discovered keys.
3. Group values into logical records.
4. Fill missing keys with null.
5. Output normalized table.

## Sanitization Logic

Cells starting with dangerous characters:
=, +, -, @

→ replaced with escaped versions or prefixed with `'`

## Future Upgrades
- RFC 4180 compliance parser
- Chunked large file processing
- Rule-based transformation engine
- XLSX/JSON/Parquet export

# ⚙️ Processing Engine & Logic

The engine uses a heuristic approach to handle "messy" CSV files without demanding user configuration.

## 1. Dialect Detection Strategy
We do not force users to specify delimiters (comma, semicolon, pipe). Instead, we use a **Data Consistency Measure**.

### The Algorithm
The `DialectDetector` service calculates a **Consistency Score (Q)** for every potential dialect (candidate).

$$Q(D) = P(D) \times T(D)$$

Where:
* **$D$**: The candidate dialect (e.g., delimiter=`,`, quote=`"`).
* **$P(D)$ (Pattern Score)**: Measures how consistent the row lengths are. A file where every row has 5 columns gets a perfect score. A jagged file gets a lower score.
* **$T(D)$ (Type Score)**: Measures how consistent the data types are within columns (e.g., Column 1 is always Date, Column 2 is always Integer).

The candidate with the highest $Q$ score is selected.

## 2. Sanitization (Formula Injection)
CSV Injection occurs when untrusted input allows Excel/Sheets to execute arbitrary commands.

**Defense Mechanism:**
Before any cell is processed, the engine checks if it starts with a trigger character: `=`, `+`, `-`, `@`.

If triggered:
1.  The value is escaped by prepending a single quote `'`.
2.  `=SUM(1+1)` becomes `'=SUM(1+1)`.
3.  Spreadsheets treat this as text, neutralizing the attack.
