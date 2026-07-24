from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from .feasibility import (
    ZERO_VIOLATION_THRESHOLDS,
    CandidateMeasurement,
    FeasibilityDecision,
    evaluate_candidate,
)

PolicyT = TypeVar("PolicyT")
EpisodeT = TypeVar("EpisodeT")


@dataclass(frozen=True)
class RolloutCandidate(Generic[EpisodeT]):
    episode: EpisodeT
    measurement: CandidateMeasurement


@dataclass(frozen=True)
class ClosedLoopRound:
    round_index: int
    generated: int
    accepted: int
    rejected: int
    training_episode_count: int


@dataclass(frozen=True)
class ClosedLoopResult(Generic[PolicyT, EpisodeT]):
    policy: PolicyT
    training_episodes: tuple[EpisodeT, ...]
    decisions: tuple[FeasibilityDecision, ...]
    rounds: tuple[ClosedLoopRound, ...]


RolloutGenerator = Callable[[PolicyT, int, int, int], Iterable[RolloutCandidate[EpisodeT]]]
IncrementalTrainer = Callable[[PolicyT, Sequence[EpisodeT], int], PolicyT]


def run_closed_loop_expansion(
    real_episodes: Sequence[EpisodeT],
    initial_policy: PolicyT,
    rollout_generator: RolloutGenerator[PolicyT, EpisodeT],
    incremental_trainer: IncrementalTrainer[PolicyT, EpisodeT],
    rounds: int,
    candidates_per_round: int,
    base_seed: int,
) -> ClosedLoopResult[PolicyT, EpisodeT]:
    """Execute the paper's screened-rollout and incremental-training loop.

    Simulator and policy details enter through two adapters. This function owns
    the invariant algorithmic behavior: every candidate is screened, only
    accepted episodes are written back, every decision is retained, and the
    current-round policy is passed to the next rollout round. The rollout
    adapter must use receding-horizon control: predict an action chunk, execute
    its first eight actions, acquire a new observation, and predict a new chunk.
    """
    if rounds <= 0 or candidates_per_round <= 0:
        raise ValueError("rounds and candidates_per_round must be positive")
    if not real_episodes:
        raise ValueError("at least one real episode is required")

    policy = initial_policy
    training_episodes = list(real_episodes)
    all_decisions: list[FeasibilityDecision] = []
    summaries: list[ClosedLoopRound] = []

    for round_index in range(1, rounds + 1):
        candidates = list(
            rollout_generator(policy, round_index, candidates_per_round, base_seed + round_index)
        )
        if len(candidates) != candidates_per_round:
            raise ValueError(
                f"round {round_index} generated {len(candidates)} candidates; "
                f"expected {candidates_per_round}"
            )

        accepted_episodes: list[EpisodeT] = []
        for candidate in candidates:
            if candidate.measurement.round_index != round_index:
                raise ValueError("candidate round_index does not match the active round")
            decision = evaluate_candidate(candidate.measurement, ZERO_VIOLATION_THRESHOLDS)
            all_decisions.append(decision)
            if decision.accepted:
                accepted_episodes.append(candidate.episode)

        training_episodes.extend(accepted_episodes)
        policy = incremental_trainer(policy, tuple(training_episodes), round_index)
        summaries.append(
            ClosedLoopRound(
                round_index=round_index,
                generated=len(candidates),
                accepted=len(accepted_episodes),
                rejected=len(candidates) - len(accepted_episodes),
                training_episode_count=len(training_episodes),
            )
        )

    return ClosedLoopResult(
        policy=policy,
        training_episodes=tuple(training_episodes),
        decisions=tuple(all_decisions),
        rounds=tuple(summaries),
    )
