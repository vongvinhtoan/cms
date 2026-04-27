#!/usr/bin/env python3

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2010-2018 Stefano Maggiolo <s.maggiolo@gmail.com>
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

from abc import abstractmethod

from . import ScoreTypeGroup


def N_(message):
    return message


class RelativeScoreType(ScoreTypeGroup):
    """Abstract base class for score types that scale outcomes relative
    to the best outcome seen across all submissions for each testcase.

    The best values are stored in dataset.best_values as
    {codename: float}. Subclasses must implement scale() and is_better().

    Parameters are [[m, t], ... ] (see ScoreTypeGroup).

    """

    IS_RELATIVE = True

    @abstractmethod
    def scale(self, outcome, best_value, parameter):
        """Scale an outcome relative to the best value.

        outcome (float): raw evaluation outcome for this testcase.
        best_value (float): best outcome across all submissions.
        parameter (list): group parameter [multiplier, testcase_spec].

        return (float): scaled score fraction (0.0 to 1.0).

        """
        pass

    @abstractmethod
    def is_better(self, outcome, best_value):
        """Determine if outcome is better than the stored best_value.

        outcome (float): raw evaluation outcome.
        best_value (float): currently stored best outcome.

        return (bool): True if outcome is an improvement.

        """
        pass

    def compute_score(self, submission_result):
        """See ScoreType.compute_score."""
        if not submission_result.evaluated():
            return 0.0, [], 0.0, [], ["%lg" % 0.0 for _ in self.parameters]

        score = 0
        subtasks = []
        public_score = 0
        public_subtasks = []
        ranking_details = []

        targets = self.retrieve_target_testcases()
        evaluations = {ev.codename: ev for ev in submission_result.evaluations}

        best_values = {}
        if hasattr(submission_result, 'dataset') and \
           hasattr(submission_result.dataset, 'best_values') and \
           submission_result.dataset.best_values is not None:
            best_values = submission_result.dataset.best_values

        for st_idx, parameter in enumerate(self.parameters):
            target = targets[st_idx]

            testcases = []
            public_testcases = []
            previous_tc_all_correct = True

            scaled_outcomes = []

            for tc_idx in target:
                raw_outcome = float(evaluations[tc_idx].outcome)
                best_value = float(best_values.get(tc_idx, 0.0))

                scaled_outcome = self.scale(raw_outcome, best_value, parameter)
                scaled_outcomes.append(scaled_outcome)

                tc_outcome = self.get_public_outcome(scaled_outcome, parameter)

                testcases.append({
                    "idx": tc_idx,
                    "outcome": tc_outcome,
                    "text": evaluations[tc_idx].text,
                    "time": evaluations[tc_idx].execution_time,
                    "memory": evaluations[tc_idx].execution_memory,
                    "best_value": best_value,
                    "show_in_restricted_feedback": previous_tc_all_correct})
                if self.public_testcases[tc_idx]:
                    public_testcases.append(testcases[-1])
                    if tc_outcome != "Correct":
                        previous_tc_all_correct = False
                else:
                    public_testcases.append({"idx": tc_idx})

            st_score_fraction = self.reduce(scaled_outcomes, parameter)
            st_score = st_score_fraction * parameter[0]

            score += st_score
            subtasks.append({
                "idx": st_idx + 1,
                "score_fraction": st_score_fraction,
                "max_score": parameter[0],
                "testcases": testcases})
            if all(self.public_testcases[tc_idx] for tc_idx in target):
                public_score += st_score
                public_subtasks.append(subtasks[-1])
            else:
                public_subtasks.append({"idx": st_idx + 1,
                                        "testcases": public_testcases})
            ranking_details.append("%g" % round(st_score, 2))

        return score, subtasks, public_score, public_subtasks, ranking_details


class LinearRelativeScore(RelativeScoreType):
    """Relative score type with linear scaling: outcome / best_value.

    Parameters are [[m, t], ... ] (see ScoreTypeGroup).

    """

    def get_public_outcome(self, outcome, unused_parameter):
        """See ScoreTypeGroup."""
        if outcome <= 0.0:
            return N_("Not correct")
        elif outcome >= 1.0:
            return N_("Correct")
        else:
            return N_("Partially correct")

    def reduce(self, outcomes, unused_parameter):
        """See ScoreTypeGroup."""
        return sum(outcomes) / len(outcomes)

    def scale(self, outcome, best_value, parameter):
        """See RelativeScoreType."""
        if best_value <= 0.0:
            return 1.0 if outcome > 0.0 else 0.0
        return min(outcome / best_value, 1.0)

    def is_better(self, outcome, best_value):
        """See RelativeScoreType."""
        return outcome > best_value


class ExponentialRelativeScore(RelativeScoreType):
    """Relative score type with quadratic scaling: (outcome/best_value)^2.

    Parameters are [[m, t], ... ] (see ScoreTypeGroup).

    """

    def get_public_outcome(self, outcome, unused_parameter):
        """See ScoreTypeGroup."""
        if outcome <= 0.0:
            return N_("Not correct")
        elif outcome >= 1.0:
            return N_("Correct")
        else:
            return N_("Partially correct")

    def reduce(self, outcomes, unused_parameter):
        """See ScoreTypeGroup."""
        return sum(outcomes) / len(outcomes)

    def scale(self, outcome, best_value, parameter):
        """See RelativeScoreType."""
        if best_value <= 0.0:
            return 1.0 if outcome > 0.0 else 0.0
        ratio = outcome / best_value
        return min(ratio ** 2, 1.0)

    def is_better(self, outcome, best_value):
        """See RelativeScoreType."""
        return outcome > best_value
