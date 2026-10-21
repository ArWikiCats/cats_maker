from unittest.mock import MagicMock, patch

from arwikibot.database.tools.services import wikilink_service


@patch("arwikibot.database.tools.services.session.SessionLocal")
def test_wikilink_service_get_ar(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    mock_execute = MagicMock()
    mock_session.execute.return_value = mock_execute
    mock_execute.scalar_one_or_none.return_value = "قالب:بذرة"

    ar_title = wikilink_service.get_ar("Template:Stub")
    assert ar_title == "قالب:بذرة"


@patch("arwikibot.database.tools.services.session.SessionLocal")
def test_wikilink_service_get_en(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    mock_execute = MagicMock()
    mock_session.execute.return_value = mock_execute
    mock_execute.scalar_one_or_none.return_value = "template:stub"

    en_title = wikilink_service.get_en("قالب:بذرة")
    assert en_title == "template:stub"


@patch("arwikibot.database.tools.services.session.SessionLocal")
def test_wikilink_service_get_all(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    fake1 = MagicMock()
    fake1.ar = "a1"
    fake1.en = "e1"
    fake2 = MagicMock()
    fake2.ar = "a2"
    fake2.en = "e2"
    mock_session.execute.return_value.scalars.return_value.all.return_value = [fake1, fake2]

    rows = wikilink_service.get_all()
    assert [(w.ar, w.en) for w in rows] == [("a1", "e1"), ("a2", "e2")]
