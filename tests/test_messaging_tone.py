from publisher_support.agents.messaging import (
    message_checking,
    message_identified,
    message_resolved,
)


def test_messages_avoid_technical_jargon():
    tech_terms = ["mysql", "sap", "gcp", "rundeck", "api", "stacktrace", "deploy", "patch"]
    for text in [
        message_checking(),
        message_identified("Tu publicación no se completó por un trámite pendiente.", 15),
        message_resolved("Ya podés publicar con normalidad."),
    ]:
        lower = text.lower()
        for term in tech_terms:
            assert term not in lower


def test_messages_are_warm_tone():
    assert "Gracias" in message_checking() or "gracias" in message_checking().lower()
    identified = message_identified("Estamos revisando tu facturación.", 10)
    assert "paciencia" in identified.lower() or "trabajando" in identified.lower()
