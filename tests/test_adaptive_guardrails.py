import unittest

from factors.auction import delayed_confirmation_score, in_weak_to_strong_soft_pool
from factors.limitup import board_divergence_quality, strength_and_tradability
from factors.sentiment import regime_multipliers
from scoring.evaluation import reweighting_readiness, screening_metrics


class AdaptiveGuardrailTests(unittest.TestCase):
    def test_auction_gap_is_a_soft_feature(self):
        self.assertTrue(in_weak_to_strong_soft_pool(0.0))
        self.assertTrue(in_weak_to_strong_soft_pool(5.0))
        self.assertFalse(in_weak_to_strong_soft_pool(6.0))

    def test_delayed_review_requires_prior_identity(self):
        inputs = dict(
            sector_ladder_score=85,
            above_vwap_ratio=0.9,
            reseal_minutes=12,
            seal_amount_ratio=0.08,
        )
        self.assertEqual(
            delayed_confirmation_score(prior_distinctive=False, **inputs), 0
        )
        self.assertGreater(
            delayed_confirmation_score(prior_distinctive=True, **inputs), 60
        )

    def test_many_openings_are_not_an_automatic_zero_after_a_strong_reseal(self):
        score = board_divergence_quality(
            open_count=32,
            final_sealed=True,
            seal_amount_ratio=0.12,
            above_vwap_ratio=0.92,
            reseal_minutes=25,
        )
        self.assertGreater(score, 60)

    def test_one_word_strength_is_not_tradability(self):
        one_word = strength_and_tradability(
            final_sealed=True,
            is_one_word=True,
            turnover=1.8,
            divergence_quality=90,
        )
        exchanged = strength_and_tradability(
            final_sealed=True,
            is_one_word=False,
            turnover=9.0,
            divergence_quality=80,
        )
        self.assertGreater(one_word["strength"], exchanged["strength"])
        self.assertLess(one_word["tradability"], exchanged["tradability"])

    def test_metrics_keep_precision_and_recall_separate(self):
        result = screening_metrics(
            predicted={"A", "B"},
            promoted={"A", "B", "C"},
            tradable_promoted={"A"},
        )
        self.assertEqual(result["precision"], 1.0)
        self.assertEqual(result["recall"], 2 / 3)
        self.assertEqual(result["false_negative_count"], 1)
        self.assertEqual(result["tradable_success_rate"], 0.5)

    def test_reweighting_requires_multiple_days_and_candidates(self):
        self.assertFalse(reweighting_readiness(1, 17)["ready"])
        self.assertTrue(reweighting_readiness(5, 50)["ready"])

    def test_retreat_tightens_the_high_level_gate(self):
        self.assertGreater(
            regime_multipliers("退潮")["high_level_gate"],
            regime_multipliers("修复")["high_level_gate"],
        )


if __name__ == "__main__":
    unittest.main()
