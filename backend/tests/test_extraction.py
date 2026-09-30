from app.services.extraction import extract_insights_from_text


def test_extract_explicit_technology():
    text = "I have been working with AWS for the last three years."

    results = extract_insights_from_text(text)

    assert len(results) == 1
    assert results[0].category == "TECHNOLOGY"
    assert results[0].subject == "AWS"
    assert results[0].confidence == "high"
    assert "AWS" in results[0].evidence_text


def test_extract_explicit_hobby():
    text = "Outside work, I enjoy playing golf."

    results = extract_insights_from_text(text)

    assert len(results) == 1
    assert results[0].category == "HOBBY"
    assert results[0].subject == "Golf"
    assert results[0].confidence == "high"
    assert "golf" in results[0].evidence_text.lower()


def test_extract_multiple_insights():
    text = (
        "I have been working with AWS for the last three years. "
        "Outside work, I enjoy playing golf."
    )

    results = extract_insights_from_text(text)

    assert len(results) == 2

    categories = {result.category for result in results}
    subjects = {result.subject.lower() for result in results}

    assert categories == {"TECHNOLOGY", "HOBBY"}
    assert "aws" in subjects
    assert "golf" in subjects


def test_do_not_infer_hobby_from_event_attendance():
    text = "The person attended a golf tournament."

    results = extract_insights_from_text(text)

    assert results == []


def test_empty_text_returns_no_insights():
    results = extract_insights_from_text("")

    assert results == []


def test_whitespace_only_text_returns_no_insights():
    results = extract_insights_from_text("   ")

    assert results == []


def test_duplicate_technology_is_removed():
    text = "I use AWS every day. My projects also run on AWS."

    results = extract_insights_from_text(text)

    aws_results = [
        result
        for result in results
        if result.category == "TECHNOLOGY"
        and result.subject.lower() == "aws"
    ]

    assert len(aws_results) == 1
    