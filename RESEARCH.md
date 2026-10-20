# Research —20 October2026

Demand is **inferred**, not a verified request for this tool. A NOT IN list containing NULL can produce UNKNOWN, whose rows WHERE discards; a true/false-only mental model hides the cause.

## Observed comparables

Query `sql parser language:Python`, GitHub repository search sorted by Most stars: [exact search](https://github.com/search?q=sql+parser+language%3APython&type=repositories&s=stars&o=desc). The highest-star relevant comparable found in this research pool is `tobymao/sqlglot`; this is not an exhaustive global ranking.

| Repository | Stars observed | Last push | License metadata | Workflow / scope |
| --- | ---: | --- | --- | --- |
| [tobymao/sqlglot](https://github.com/tobymao/sqlglot) | 9699 | 2026-10-19T21:40:15Z | MIT | Python parser/transpiler/optimizer and engine; broad dialect support. |
| [andialbrecht/sqlparse](https://github.com/andialbrecht/sqlparse) | 4023 | 2026-08-13T19:17:19Z | BSD-3-Clause | Nonvalidating token-tree parser, formatter and script splitter. |
| [macbre/sql-metadata](https://github.com/macbre/sql-metadata) | 889 | 2026-10-19T02:47:12Z | MIT | SQLGlot-backed table/column metadata extraction. |

## Workflow choice and tradeoffs

Analysts debugging why nullable rows disappear from a WHERE clause. Parse a strict SQL predicate subset and explain TRUE/FALSE/UNKNOWN results and retained row indexes with an AST and postorder trace.

Existing sqlite-plan-witness inspects plans, sqlite-fixture-closure extracts parent rows, sqlite-rehearsal rehearses SQL, and json tools compare structure. This explains nullable predicate semantics without connecting to or running a user database.

This is a bounded dedicated report with an invented fixture and zero runtime dependencies. The established tools are broader; choose them when their ecosystem, formats or capabilities match the job. Our own installed example proves only our documented behavior. Competitor clean installs, time to first useful result, support response times, reliability and equivalent-workload performance were not measured. Current docs offer install/usage guidance; sampled issue activity is preserved as evidence, not a support-quality score. No feature absence or superiority is claimed.

## Coverage and evidence

The keyword search includes irrelevant results (SQL knowledge graphs, CSS critical paths, routing deployment projects and regex engines). Relevant comparables were also found directly; filtering was based on current README scope. [Exact dated metadata and issue samples](RESEARCH_PROVENANCE.json). Own acceptance and distinction: [brief](BRIEF.json). No implementation, branding or prose was copied.

SQL NULL/AND/OR/IN semantics were checked against [SQLite expression documentation](https://www.sqlite.org/lang_expr.html), then compared with Python’s bundled SQLite only inside the supported strict subset. This tool does not implement all SQLite expression behavior.
