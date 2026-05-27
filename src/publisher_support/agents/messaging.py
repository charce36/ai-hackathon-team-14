"""Mensajes al publisher — tono gentil, sin lenguaje técnico."""

from publisher_support.models.events import ClientMessage, ClientMessageType


def message_checking() -> str:
    return (
        "¡Hola! Gracias por escribirnos. "
        "Ya estamos revisando tu consulta con mucho cuidado; en un momento te contamos cómo seguimos."
    )


def message_identified(publisher_summary: str, eta_minutes: int) -> str:
    return (
        f"Gracias por tu paciencia. {publisher_summary.strip()} "
        f"Estamos trabajando en la solución y estimamos tenerlo listo en aproximadamente "
        f"{eta_minutes} minutos. Te avisamos en cuanto puedas seguir operando con normalidad."
    )


def message_resolved(publisher_summary: str) -> str:
    return (
        f"¡Buenas noticias! {publisher_summary.strip()} "
        "Ya podés volver a usar la plataforma con normalidad. "
        "Si necesitás algo más, estamos acá para ayudarte."
    )


def message_escalated() -> str:
    return (
        "Gracias por contactarnos. Tu consulta quedó con nuestro equipo de soporte "
        "y te escribimos en breve con novedades. Apreciamos tu paciencia."
    )


def client_message_checking() -> ClientMessage:
    return ClientMessage(type=ClientMessageType.CHECKING, text=message_checking())


def client_message_identified(publisher_summary: str, eta_minutes: int) -> ClientMessage:
    return ClientMessage(
        type=ClientMessageType.IDENTIFIED,
        text=message_identified(publisher_summary, eta_minutes),
    )


def client_message_resolved(publisher_summary: str) -> ClientMessage:
    return ClientMessage(
        type=ClientMessageType.RESOLVED,
        text=message_resolved(publisher_summary),
    )


def client_message_escalated() -> ClientMessage:
    return ClientMessage(type=ClientMessageType.IDENTIFIED, text=message_escalated())
