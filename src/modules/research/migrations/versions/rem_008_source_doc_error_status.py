"""research: source status `error` + backfill from the page fetch outcome

Two halves of one change. **Schema:** the source status set gains `error` in place of the
unused `fetch_error` — a source mirrors the page it hangs off, and the review statuses say
nothing about whether the material arrived. **Data:** until now the status was written blind
(always `pending`), so a source whose page never downloaded entered the review queue looking
like any other and was reviewed from the search snippet alone. The forward path now derives it
(`research/mcp/research.py::_initial_source_status`); this applies the same rule to the rows
that predate it, **including already reviewed ones** (`kept` / `filtered`) — a verdict reached
without the material is not a verdict.

`relevance` and `note` survive: the old assessment stays readable next to the `error` status,
and the source returns to the queue once its page is refetched.

The CHECK goes first: SQLite's batch mode copies the rows into a table that already carries the
new constraint, so the copy has to happen while every row still holds a review status. Batch
mode at all because SQLite has no ALTER for constraints.

Reads `web_search_page` (another module's chain) → `depends_on` the migration that creates that
table, per docs/conventions/db-migrations.md.

Revision ID: rem_008_source_doc_error_status
Revises: rem_007_research_group_code
Create Date: 2026-08-27
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "rem_008_source_doc_error_status"
down_revision: Union[str, None] = "rem_007_research_group_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = "wsm_002_page"

_CONSTRAINT = "ck_research_source_document_status"
_REVIEW_STATUSES = "'pending', 'kept', 'filtered'"
_ACCEPTS_ERROR = f"status IN ('error', {_REVIEW_STATUSES})"
_ACCEPTS_FETCH_ERROR = f"status IN ('fetch_error', {_REVIEW_STATUSES})"

_BACKFILL = """
    UPDATE research_source_document
       SET status = 'error'
     WHERE page_code IN (SELECT code FROM web_search_page WHERE status = 'error')
       AND status <> 'error'
"""


def _set_allowed_statuses(condition: str) -> None:
    with op.batch_alter_table("research_source_document") as batch_op:
        batch_op.drop_constraint(_CONSTRAINT, type_="check")
        batch_op.create_check_constraint(_CONSTRAINT, condition)


def upgrade() -> None:
    _set_allowed_statuses(_ACCEPTS_ERROR)
    op.execute(_BACKFILL)


def downgrade() -> None:
    """Only the schema half is reversible — which status each source held before the backfill
    is recorded nowhere, so the rows stay parked in the pre-downgrade state."""
    op.execute("UPDATE research_source_document SET status = 'pending' WHERE status = 'error'")
    _set_allowed_statuses(_ACCEPTS_FETCH_ERROR)
