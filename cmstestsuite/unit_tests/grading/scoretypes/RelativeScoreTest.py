#!/usr/bin/env python3

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2018 Stefano Maggiolo <s.maggiolo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for the relative score types."""

import unittest

from unittest.mock import Mock

from cms.grading.scoretypes.RelativeScore import \
    LinearRelativeScore, ExponentialRelativeScore
from cmstestsuite.unit_tests.grading.scoretypes.scoretypetestutils \
    import ScoreTypeTestMixin


class RelativeScoreTestMixin(ScoreTypeTestMixin):
    """Shared mixin for relative score type tests."""

    def setUp(self):
        super().setUp()
        self._public_testcases = {
            "1_0": True,
            "1_1": True,
            "2_0": True,
            "2_1": False,
            "3_0": False,
            "3_1": False,
        }

    def _get_submission_result_with_best(self, best_values=None):
        sr = self.get_submission_result(self._public_testcases)
        sr.dataset = Mock()
        sr.dataset.best_values = best_values if best_values is not None else {}
        return sr

    def test_parameters_correct(self):
        self._score_type_class([], self._public_testcases)
        self._score_type_class([[40, 2], [60.0, 2]], self._public_testcases)
        self._score_type_class(
            [[40, "1_*"], [60.0, "2_*"]], self._public_testcases)

    def test_parameters_invalid_types(self):
        with self.assertRaises(ValueError):
            self._score_type_class([1], self._public_testcases)
        with self.assertRaises(ValueError):
            self._score_type_class(1, self._public_testcases)

    def test_parameters_invalid_wrong_item_len(self):
        with self.assertRaises(ValueError):
            self._score_type_class([[]], self._public_testcases)
        with self.assertRaises(ValueError):
            self._score_type_class([[1]], self._public_testcases)

    def test_parameter_invalid_wrong_max_score_type(self):
        with self.assertRaises(ValueError):
            self._score_type_class([["a", 10]], self._public_testcases)

    def test_parameter_invalid_wrong_testcases_type(self):
        with self.assertRaises(ValueError):
            self._score_type_class([[100, 1j]], self._public_testcases)

    def test_parameter_invalid_inconsistent_testcases_type(self):
        with self.assertRaises(ValueError):
            self._score_type_class(
                [[40, 10], [40, "1_*"]], self._public_testcases)

    def test_max_scores_regexp(self):
        s1, s2, s3 = 10.5, 30.5, 59
        parameters = [[s1, "1_*"], [s2, "2_*"], [s3, "3_*"]]
        header = ["Subtask 1 (10.5)", "Subtask 2 (30.5)", "Subtask 3 (59)"]

        public_testcases = dict(self._public_testcases)
        self.assertEqual(
            self._score_type_class(parameters, public_testcases).max_scores(),
            (s1 + s2 + s3, s1, header))

        for testcase in public_testcases.keys():
            public_testcases[testcase] = True
        self.assertEqual(
            self._score_type_class(parameters, public_testcases).max_scores(),
            (s1 + s2 + s3, s1 + s2 + s3, header))

        for testcase in public_testcases.keys():
            public_testcases[testcase] = False
        self.assertEqual(
            self._score_type_class(parameters, public_testcases).max_scores(),
            (s1 + s2 + s3, 0, header))

    def test_compute_score_all_correct_with_best(self):
        s1, s2, s3 = 10.5, 30.5, 59
        parameters = [[s1, "1_*"], [s2, "2_*"], [s3, "3_*"]]
        st = self._score_type_class(parameters, self._public_testcases)
        sr = self._get_submission_result_with_best(
            {"1_0": 1.0, "1_1": 1.0, "2_0": 1.0, "2_1": 1.0,
             "3_0": 1.0, "3_1": 1.0})

        self.assertComputeScore(st.compute_score(sr),
                                s1 + s2 + s3, s1, [s1, s2, s3])

    def test_compute_score_partial_with_best(self):
        s1, s2, s3 = 10.5, 30.5, 59
        parameters = [[s1, "1_*"], [s2, "2_*"], [s3, "3_*"]]
        st = self._score_type_class(parameters, self._public_testcases)
        sr = self._get_submission_result_with_best(
            {"1_0": 1.0, "1_1": 1.0, "2_0": 1.0, "2_1": 1.0,
             "3_0": 1.0, "3_1": 1.0})

        self.set_outcome(sr, "3_0", 0.5)
        self.set_outcome(sr, "3_1", 0.1)
        scaled_3_0 = self._scale_fraction(0.5, 1.0)
        scaled_3_1 = self._scale_fraction(0.1, 1.0)
        st3_fraction = (scaled_3_0 + scaled_3_1) / 2.0
        expected_score = s1 + s2 + s3 * st3_fraction
        rws = [s1, s2, round(s3 * st3_fraction, 2)]
        self.assertComputeScore(st.compute_score(sr),
                                expected_score, s1, rws)

    def test_compute_score_best_values_zero(self):
        s1, s2 = 40.5, 60.5
        parameters = [[s1, "1_*"], [s2, "2_*"]]
        public_testcases = {"1_0": True, "2_0": False}
        st = self._score_type_class(parameters, public_testcases)
        sr = self._get_submission_result_with_best({})

        self.set_outcome(sr, "1_0", 0.8)
        self.set_outcome(sr, "2_0", 0.5)

        self.assertComputeScore(st.compute_score(sr),
                                s1 + s2, s1, [s1, s2])

    def test_compute_score_best_values_larger(self):
        s1, s2 = 40.5, 60.5
        parameters = [[s1, "1_*"], [s2, "2_*"]]
        public_testcases = {"1_0": True, "2_0": False}
        st = self._score_type_class(parameters, public_testcases)
        sr = self._get_submission_result_with_best(
            {"1_0": 2.0, "2_0": 2.0})

        self.set_outcome(sr, "1_0", 1.0)
        self.set_outcome(sr, "2_0", 1.0)

        f1 = self._scale_fraction(1.0, 2.0)
        f2 = self._scale_fraction(1.0, 2.0)
        total_score = s1 * f1 + s2 * f2
        public_score = s1 * f1
        rws_scores = [round(s1 * f1, 2), round(s2 * f2, 2)]
        self.assertComputeScore(st.compute_score(sr),
                                total_score, public_score, rws_scores)

    def test_is_better(self):
        st = self._score_type_class([[100, 1]], {"t1": True})
        self.assertTrue(st.is_better(1.0, 0.5))
        self.assertFalse(st.is_better(0.5, 1.0))
        self.assertFalse(st.is_better(1.0, 1.0))

    def test_score_details_contain_best_value(self):
        parameters = [[100, "1_*"]]
        public_testcases = {"1_0": True}
        st = self._score_type_class(parameters, public_testcases)
        sr = self._get_submission_result_with_best({"1_0": 2.0})

        _, score_details, _, _, _ = st.compute_score(sr)
        testcase_detail = score_details[0]["testcases"][0]
        self.assertEqual(testcase_detail["best_value"], 2.0)

    @property
    def _score_type_class(self):
        raise NotImplementedError

    def _scale_fraction(self, outcome, best_value):
        raise NotImplementedError


class TestLinearRelativeScore(RelativeScoreTestMixin, unittest.TestCase):
    """Test the LinearRelativeScore score type."""

    @property
    def _score_type_class(self):
        return LinearRelativeScore

    def _scale_fraction(self, outcome, best_value):
        if best_value <= 0.0:
            return 1.0 if outcome > 0.0 else 0.0
        return min(outcome / best_value, 1.0)

    def test_scale(self):
        st = LinearRelativeScore([[100, 1]], {"t1": True})
        self.assertAlmostEqual(st.scale(0.5, 1.0, [100, 1]), 0.5)
        self.assertAlmostEqual(st.scale(1.0, 1.0, [100, 1]), 1.0)
        self.assertAlmostEqual(st.scale(2.0, 1.0, [100, 1]), 1.0)
        self.assertAlmostEqual(st.scale(0.0, 1.0, [100, 1]), 0.0)
        self.assertAlmostEqual(st.scale(0.5, 0.0, [100, 1]), 1.0)
        self.assertAlmostEqual(st.scale(0.0, 0.0, [100, 1]), 0.0)

    def test_compute_score_linear_specific(self):
        s1, s2 = 40.5, 60.5
        parameters = [[s1, "1_*"], [s2, "2_*"]]
        public_testcases = {"1_0": True, "2_0": False}
        st = LinearRelativeScore(parameters, public_testcases)
        sr = self._get_submission_result_with_best(
            {"1_0": 2.0, "2_0": 4.0})

        self.set_outcome(sr, "1_0", 1.0)
        self.set_outcome(sr, "2_0", 2.0)

        self.assertComputeScore(st.compute_score(sr),
                                s1 * 0.5 + s2 * 0.5,
                                s1 * 0.5,
                                [s1 * 0.5, s2 * 0.5])


class TestExponentialRelativeScore(RelativeScoreTestMixin, unittest.TestCase):
    """Test the ExponentialRelativeScore score type."""

    @property
    def _score_type_class(self):
        return ExponentialRelativeScore

    def _scale_fraction(self, outcome, best_value):
        if best_value <= 0.0:
            return 1.0 if outcome > 0.0 else 0.0
        ratio = outcome / best_value
        return min(ratio ** 2, 1.0)

    def test_scale(self):
        st = ExponentialRelativeScore([[100, 1]], {"t1": True})
        self.assertAlmostEqual(st.scale(0.5, 1.0, [100, 1]), 0.25)
        self.assertAlmostEqual(st.scale(1.0, 1.0, [100, 1]), 1.0)
        self.assertAlmostEqual(st.scale(2.0, 1.0, [100, 1]), 1.0)
        self.assertAlmostEqual(st.scale(0.0, 1.0, [100, 1]), 0.0)
        self.assertAlmostEqual(st.scale(0.5, 0.0, [100, 1]), 1.0)
        self.assertAlmostEqual(st.scale(0.0, 0.0, [100, 1]), 0.0)

    def test_compute_score_exponential_specific(self):
        s1, s2 = 40.5, 60.5
        parameters = [[s1, "1_*"], [s2, "2_*"]]
        public_testcases = {"1_0": True, "2_0": False}
        st = ExponentialRelativeScore(parameters, public_testcases)
        sr = self._get_submission_result_with_best(
            {"1_0": 2.0, "2_0": 4.0})

        self.set_outcome(sr, "1_0", 1.0)
        self.set_outcome(sr, "2_0", 2.0)

        total_score = s1 * 0.25 + s2 * 0.25
        public_score = s1 * 0.25
        rws_scores = [round(s1 * 0.25, 2), round(s2 * 0.25, 2)]
        self.assertComputeScore(st.compute_score(sr),
                                total_score, public_score, rws_scores)


if __name__ == "__main__":
    unittest.main()
