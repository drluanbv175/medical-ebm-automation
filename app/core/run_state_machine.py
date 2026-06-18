"""State machine kiểm soát vòng đời một lần chạy V7."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, Iterable


class RunState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    WAITING_FOR_REVIEW = "waiting_for_review"
    APPROVED = "approved"
    RELEASED = "released"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


ALLOWED_TRANSITIONS: Dict[RunState, FrozenSet[RunState]] = {
    RunState.QUEUED: frozenset({RunState.RUNNING, RunState.CANCELLED}),
    RunState.RUNNING: frozenset({
        RunState.WAITING_FOR_INPUT,
        RunState.WAITING_FOR_REVIEW,
        RunState.FAILED,
        RunState.CANCELLED,
    }),
    RunState.WAITING_FOR_INPUT: frozenset({RunState.RUNNING, RunState.CANCELLED}),
    RunState.WAITING_FOR_REVIEW: frozenset({RunState.APPROVED, RunState.RUNNING, RunState.CANCELLED}),
    RunState.APPROVED: frozenset({RunState.RELEASED, RunState.SUPERSEDED, RunState.RETIRED}),
    RunState.RELEASED: frozenset({RunState.SUPERSEDED, RunState.RETIRED}),
    RunState.FAILED: frozenset({RunState.RUNNING, RunState.RETIRED}),
    RunState.CANCELLED: frozenset({RunState.RETIRED}),
    RunState.SUPERSEDED: frozenset({RunState.RETIRED}),
    RunState.RETIRED: frozenset(),
}


class InvalidTransition(ValueError):
    """Chuyển trạng thái không hợp lệ."""


@dataclass(frozen=True)
class StateTransition:
    previous: RunState
    current: RunState
    reason: str


def transition(current: RunState, target: RunState, reason: str = "") -> StateTransition:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransition(f"Không được chuyển {current.value} -> {target.value}")
    return StateTransition(previous=current, current=target, reason=reason)


def next_states(current: RunState) -> Iterable[RunState]:
    return ALLOWED_TRANSITIONS[current]
