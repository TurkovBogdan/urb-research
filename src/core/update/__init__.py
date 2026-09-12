"""Moving an installation from one release to the next.

Three halves, re-exported here: `selection` is the evidence-based sweep that now only detects
strays, `stop` decides which processes of this checkout must stop — from the records they wrote
about themselves — and stops them, `sequence` is the update itself (preconditions → flag → stop →
fetch/merge/sync → backup → migrate → restart).

Three more files serve the same act from the outside and are imported as submodules, not
re-exported: `status` answers whether this install is behind and may be updated at all, `spawn`
starts `update.sh` from inside the installation, `api` is the HTTP surface both are reached
through. `api` stays out of this list on purpose — the worker imports this package and has no
business pulling FastAPI in with it.
"""

from src.core.update.errors import UpdateRefused
from src.core.update.selection import (
    MATCH_DESCENDANT,
    MATCH_LAUNCHER,
    NON_SERVICE_SUBCOMMANDS,
    VETO_ARGV_MARKERS,
    KillTarget,
    ancestor_pids,
    argv_is_vetoed,
    descendants,
    select_kill_targets,
)
from src.core.update.sequence import (
    BRANCH_PATTERN,
    EXIT_BACKEND_DEAD,
    EXIT_BACKUP_FAILED,
    EXIT_CRASHED,
    EXIT_HELD,
    EXIT_MIGRATION_FAILED,
    EXIT_OK,
    EXIT_PRECONDITIONS,
    EXIT_ROLLBACK_FAILED,
    EXIT_ROLLED_BACK,
    EXIT_STOP_FAILED,
    EXIT_UNREGISTERED,
    EXIT_UNSUPPORTED_PLATFORM,
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
from src.core.update.stop import (
    KILL_GRACE_SECONDS,
    MATCH_GROUP_MEMBER,
    MATCH_RECORDED,
    MATCH_UNREGISTERED,
    TERM_GRACE_SECONDS,
    ForeignProcesses,
    GroupStop,
    OwnIdentity,
    ProcessesSurvived,
    StopPlan,
    StopTarget,
    UnregisteredProcesses,
    UpdaterInsideInstall,
    classify_records,
    execute_stop,
    plan_live_stop,
    plan_stop,
)

__all__ = [
    "BRANCH_PATTERN",
    "EXIT_BACKEND_DEAD",
    "EXIT_BACKUP_FAILED",
    "EXIT_CRASHED",
    "EXIT_HELD",
    "EXIT_MIGRATION_FAILED",
    "EXIT_OK",
    "EXIT_PRECONDITIONS",
    "EXIT_ROLLBACK_FAILED",
    "EXIT_ROLLED_BACK",
    "EXIT_STOP_FAILED",
    "EXIT_UNREGISTERED",
    "EXIT_UNSUPPORTED_PLATFORM",
    "GIT_NONINTERACTIVE",
    "KILL_GRACE_SECONDS",
    "MATCH_DESCENDANT",
    "MATCH_GROUP_MEMBER",
    "MATCH_LAUNCHER",
    "MATCH_RECORDED",
    "MATCH_UNREGISTERED",
    "NON_SERVICE_SUBCOMMANDS",
    "SYNC_TIMEOUT_SECONDS",
    "TERM_GRACE_SECONDS",
    "VETO_ARGV_MARKERS",
    "BackendDidNotStart",
    "CommandResult",
    "DryRunHost",
    "ForeignProcesses",
    "GroupStop",
    "KillTarget",
    "OwnIdentity",
    "ProcessesSurvived",
    "StartingPoint",
    "StopPlan",
    "StopTarget",
    "UnregisteredProcesses",
    "UpdateHost",
    "UpdateRefused",
    "UpdaterInsideInstall",
    "ancestor_pids",
    "argv_is_vetoed",
    "classify_records",
    "descendants",
    "execute_stop",
    "plan_live_stop",
    "plan_stop",
    "run_update",
    "select_kill_targets",
    "update_command",
    "validate_branch",
]
