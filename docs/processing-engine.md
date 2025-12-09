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
