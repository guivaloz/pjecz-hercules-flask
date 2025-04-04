"""
Exh Exhortos, tareas en el fondo
"""

from hercules.app import create_app
from hercules.blueprints.exh_exhortos.communications.query import consultar_exhorto
from hercules.blueprints.exh_exhortos.communications.send import enviar_exhorto
from hercules.blueprints.exh_exhortos.models import ExhExhorto
from hercules.extensions import database
from lib.exceptions import MyAnyError
from lib.tasks import set_task_error, set_task_progress

app = create_app()
app.app_context().push()
database.app = app


def task_enviar_exhorto(exh_exhorto_id: int) -> str:
    """Lanzar tarea en el fondo para enviar un exhorto"""
    # Iniciar la tarea en el fondo
    set_task_progress(0, "Se ha lanzado la tarea en el fondo para enviar un exhorto")

    # Ejecutar
    try:
        mensaje_termino, _, _ = enviar_exhorto(exh_exhorto_id)
    except MyAnyError as error:
        # Consultar el exhorto para cambiar su estado a RECHAZADO
        exh_exhorto = ExhExhorto.query.get(exh_exhorto_id)
        if exh_exhorto is not None:
            exh_exhorto.estado_anterior = exh_exhorto.estado
            exh_exhorto.estado = "RECHAZADO"
            exh_exhorto.save()
        # Mandar mensaje de error al usuario
        mensaje_error = str(error)
        set_task_error(mensaje_error)
        return mensaje_error

    # Terminar la tarea en el fondo
    set_task_progress(100, mensaje_termino)

    # Entregar mensaje de termino
    return mensaje_termino


def task_consultar_exhorto(exh_exhorto_id: int) -> str:
    """Lanzar tarea en el fondo para consultar un exhorto"""
    # Iniciar la tarea en el fondo
    set_task_progress(0, "Se ha lanzado la tarea en el fondo para consultar un exhorto")

    # Ejecutar
    try:
        mensaje_termino, _, _ = consultar_exhorto(exh_exhorto_id)
    except MyAnyError as error:
        mensaje_error = str(error)
        set_task_error(mensaje_error)
        return mensaje_error

    # Terminar la tarea en el fondo
    set_task_progress(100, mensaje_termino)

    # Entregar mensaje de termino
    return mensaje_termino
