"""
Tests for how a quiz reads on a phone.

Scenario-based questions are the point of the quiz: "what would you do here"
tells you whether someone could do the job, where "list the three steps" only
tells you whether they watched the video.
"""
import pytest

from agents.question_agent import QuestionAgent


@pytest.fixture
def agent():
    """A QuestionAgent without __init__ - these are pure rendering tests."""
    return QuestionAgent.__new__(QuestionAgent)


SCENARIO_Q = {
    "scenario": "Priya arrives with a kettle bought 40 days ago and no receipt.",
    "question": "What do you offer her, and why?",
}


class TestScoreBar:
    def test_bar_is_always_ten_blocks(self, agent):
        for score in range(0, 11):
            bar = agent._score_bar(score)
            assert len(bar) == 10
            assert bar.count("●") == score

    def test_out_of_range_scores_are_clamped(self, agent):
        """A model that returns 12/10 must not produce a ragged bar."""
        assert len(agent._score_bar(99)) == 10
        assert len(agent._score_bar(-5)) == 10
        assert agent._score_bar(-5).count("●") == 0

    def test_fractional_averages_round(self, agent):
        assert agent._score_bar(7.4).count("●") == 7
        assert agent._score_bar(7.6).count("●") == 8


class TestQuestionRendering:
    def test_scenario_is_shown_and_labelled(self, agent):
        out = agent._render_question(SCENARIO_Q, 2, 3)

        assert "Question 2 of 3" in out
        assert "The situation" in out
        assert "Priya arrives" in out
        assert "What do you offer her" in out

    def test_situation_comes_before_the_question(self, agent):
        """Reading order matters: the setup has to land before the ask."""
        out = agent._render_question(SCENARIO_Q, 1, 3)
        assert out.index("Priya arrives") < out.index("What do you offer her")

    def test_question_without_a_scenario_still_renders(self, agent):
        """Questions written before scenarios existed must stay askable."""
        out = agent._render_question({"question": "Why does the window exist?"}, 1, 2)

        assert "Question 1 of 2" in out
        assert "The situation" not in out
        assert "Why does the window exist?" in out

    def test_empty_scenario_is_treated_as_absent(self, agent):
        out = agent._render_question({"scenario": "   ", "question": "Why?"}, 1, 1)
        assert "The situation" not in out

    def test_voice_is_offered_as_an_answer(self, agent):
        """Voice is the whole reason these are answerable aloud."""
        assert "voice note" in agent._render_question(SCENARIO_Q, 1, 3)

    def test_learner_text_is_sanitised(self, agent):
        """Model output lands inside a formatted message; markers must not."""
        out = agent._render_question(
            {"scenario": "A *bold* claim", "question": "What _now_?"}, 1, 1
        )
        assert "*bold*" not in out
        assert "_now_" not in out


class TestFeedbackRendering:
    def test_score_and_bar_are_shown(self, agent):
        out = agent._render_feedback({"rating": 7, "feedback": "Good start."})
        assert "7/10" in out
        assert "●" * 7 in out
        assert "Good start." in out

    def test_missing_feedback_does_not_break_the_render(self, agent):
        out = agent._render_feedback({"rating": 0})
        assert "0/10" in out
