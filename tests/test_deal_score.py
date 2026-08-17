from score.deal_score import (
    calculate_history_score,
    calculate_rating_score,
)


def test_rating_score_no_rating():
    assert calculate_rating_score(None, 100) == 0


def test_rating_score_no_reviews():
    score = calculate_rating_score(
        rating=5,
        reviews=0,
    )

    assert score == 1.5


def test_rating_score_many_reviews():
    score = calculate_rating_score(
        rating=4.5,
        reviews=500,
    )

    assert score == 4.5


def test_history_score_insufficient_observations():
    score = calculate_history_score(
        current_price=600,
        avg_price=700,
        observations=1,
    )

    assert score == 7.5


def test_history_score_same_as_average():
    score = calculate_history_score(
        current_price=600,
        avg_price=600,
        observations=5,
    )

    assert score == 7.5


def test_history_score_discount():
    score = calculate_history_score(
        current_price=595,
        avg_price=700,
        observations=5,
    )

    assert score == 15


def test_history_score_price_above_average():
    score = calculate_history_score(
        current_price=660,
        avg_price=600,
        observations=5,
    )

    assert score < 7.5