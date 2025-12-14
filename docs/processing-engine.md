# Processing Engine & Logical ⚙️

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

### Limitations
- Extremely sparse files may result in ambiguous dialect scores.
- In such cases, the system falls back to Excel-compatible defaults.

## Future Upgrades
- RFC 4180 compliance parser
- Chunked large file processing
- Rule-based transformation engine
- XLSX/JSON/Parquet export
