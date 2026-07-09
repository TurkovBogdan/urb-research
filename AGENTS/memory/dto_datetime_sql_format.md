---
name: dto_datetime_sql_format
description: "API DTOs must serialize datetime in SQL format (space, no T) or the frontend renders \"—\""
metadata: 
  node_type: memory
  type: project
  originSessionId: c8bb93d0-0253-4c78-97c4-13ccab4bfabe
---

The frontend date formatters in `web/src/shared/utils/date.ts` parse with Luxon
**`DateTime.fromSQL`** (`"yyyy-MM-dd HH:mm:ss"`, space separator, UTC). Pydantic's
default datetime JSON serialization is **ISO 8601 with a `T`** — `fromSQL` can't parse
it → `fmtDate/fmtDateTime` return `"—"`.

So any API DTO returning a datetime to this SPA must serialize in SQL format. Pattern
(see `src/modules/web_search/dto.py`):

```python
def _to_sql(v: datetime | None) -> str | None:
    return v.isoformat(sep=" ", timespec="seconds") if v is not None else None

SqlDateTime = Annotated[datetime, PlainSerializer(_to_sql, return_type=str)]
```

Use `SqlDateTime` / `SqlDateTime | None` for every datetime field. No global encoder
exists in core yet — each module's DTOs handle it. Related: [[web_search/INDEX]].
