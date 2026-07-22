import unittest

from odgs_sparse_demo.feasibility import CRITERION_ORDER, CandidateMeasurement
from odgs_sparse_demo.pipeline import RolloutCandidate, run_closed_loop_expansion


def measurement(
    candidate_id: str, round_index: int, collision: float = 0.0
) -> CandidateMeasurement:
    violations = {criterion: 0.0 for criterion in CRITERION_ORDER}
    violations["collision"] = collision
    return CandidateMeasurement(
        candidate_id=candidate_id,
        round_index=round_index,
        seed=round_index,
        checkpoint=f"checkpoint-{round_index - 1}",
        source_episode="real-0",
        sampled_state={"structure_type": "hinge"},
        violations=violations,
        manual_review_passed=True,
    )


class PipelineTest(unittest.TestCase):
    def test_only_accepted_rollouts_enter_incremental_training(self) -> None:
        training_sizes = []

        def generate(policy, round_index, budget, seed):
            self.assertEqual(budget, 2)
            return [
                RolloutCandidate(f"accepted-{round_index}", measurement("a", round_index)),
                RolloutCandidate(
                    f"rejected-{round_index}",
                    measurement("b", round_index, collision=0.01),
                ),
            ]

        def train(policy, episodes, round_index):
            training_sizes.append(len(episodes))
            return policy + 1

        result = run_closed_loop_expansion(
            real_episodes=["real-0"],
            initial_policy=0,
            rollout_generator=generate,
            incremental_trainer=train,
            rounds=2,
            candidates_per_round=2,
            base_seed=10,
        )
        self.assertEqual(result.policy, 2)
        self.assertEqual(result.training_episodes, ("real-0", "accepted-1", "accepted-2"))
        self.assertEqual(training_sizes, [2, 3])
        self.assertEqual([item.accepted for item in result.decisions], [True, False, True, False])


if __name__ == "__main__":
    unittest.main()
