"""Moving an installation from one release to the next.

The command itself is two halves, re-exported here: `selection` decides which processes of this
checkout must stop and stops them; `sequence` is the update (preconditions → flag → kill →
fetch/merge/sync → backup → migrate → restart).

Three more files serve the same act from the outside and are imported as submodules, not
re-exported: `status` answers whether this install is behind and may be updated at all, `spawn`
starts `update.sh` from inside the installation, `api` is the HTTP surface both are reached
through. `api` stays out of this list on purpose — the worker imports this package and has no
business pulling FastAPI in with it.
"""

from src.core.update.errors import UpdateRefused
from src.core.update.selection import (
    KILL_GRACE_SECONDS,
    MATCH_DESCENDANT,
    MATCH_LAUNCHER,
    NON_SERVICE_SUBCOMMANDS,
    TERM_GRACE_SECONDS,
    VETO_ARGV_MARKERS,
    KillPlan,
    KillTarget,
    Process,
    ProcessesSurvived,
    ancestor_pids,
    parse_proc_stat,
    parse_proc_state,
    plan_kill,
    process_is_running,
    read_process_table,
    select_kill_targets,
    terminate,
)
from src.core.update.sequence import (
    BRANCH_PATTERN,
    EXIT_BACKEND_DEAD,
    EXIT_BACKUP_FAILED,
    EXIT_HELD,
    EXIT_MIGRATION_FAILED,
    EXIT_OK,
    EXIT_PRECONDITIONS,
    EXIT_ROLLBACK_FAILED,
    EXIT_ROLLED_BACK,
    EXIT_STOP_FAILED,
    GIT_NONINTERACTIVE,
    SYNC_TIMEOUT_SECONDS,
    BackendDidNotStart,
    CommandResult,
    DryRunHost,
    StartingPoint,
    UpdateHost,
    run_update,
    update_command,
    validate_branch,
)

__all__ = [
    "BRANCH_PATTERN",
    "EXIT_BACKEND_DEAD",
    "EXIT_BACKUP_FAILED",
    "EXIT_HELD",
    "EXIT_MIGRATION_FAILED",
    "EXIT_OK",
    "EXIT_PRECONDITIONS",
    "EXIT_ROLLBACK_FAILED",
    "EXIT_ROLLED_BACK",
    "EXIT_STOP_FAILED",
    "GIT_NONINTERACTIVE",
    "KILL_GRACE_SECONDS",
    "MATCH_DESCENDANT",
    "MATCH_LAUNCHER",
    "NON_SERVICE_SUBCOMMANDS",
    "SYNC_TIMEOUT_SECONDS",
    "TERM_GRACE_SECONDS",
    "VETO_ARGV_MARKERS",
    "BackendDidNotStart",
    "CommandResult",
    "DryRunHost",
    "KillPlan",
    "KillTarget",
    "Process",
    "ProcessesSurvived",
    "StartingPoint",
    "UpdateHost",
    "UpdateRefused",
    "ancestor_pids",
    "parse_proc_stat",
    "parse_proc_state",
    "plan_kill",
    "process_is_running",
    "read_process_table",
    "run_update",
    "select_kill_targets",
    "terminate",
    "update_command",
    "validate_branch",
]
