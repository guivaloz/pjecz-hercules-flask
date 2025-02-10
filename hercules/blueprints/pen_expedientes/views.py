"""
Penales Expedientes, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.pen_expedientes.models import PenExpediente
from hercules.blueprints.permisos.models import Permiso
from hercules.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "PEN EXPEDIENTES"

pen_expedientes = Blueprint("pen_expedientes", __name__, template_folder="templates")


@pen_expedientes.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@pen_expedientes.route("/pen_expedientes/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Expedientes"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PenExpediente.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    # if "persona_id" in request.form:
    #     consulta = consulta.filter_by(persona_id=request.form["persona_id"])
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(PenExpediente.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "expediente": resultado.expediente,
                    "url": url_for("pen_expedientes.detail", pen_expediente_id=resultado.id),
                },
                "fecha": resultado.fecha.strftime("%Y-%m-%d"),
                "autoridad_clave": resultado.autoridad.clave,
                "juez_nombre": resultado.juez.nombre,
                "secretario_nombre": resultado.secretario.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@pen_expedientes.route("/pen_expedientes")
def list_active():
    """Listado de Expedientes activos"""
    return render_template(
        "pen_expedientes/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Expedientes",
        estatus="A",
    )


@pen_expedientes.route("/pen_expedientes/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Expedientes inactivos"""
    return render_template(
        "pen_expedientes/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Expedientes inactivos",
        estatus="B",
    )


@pen_expedientes.route("/pen_expedientes/<int:pen_expediente_id>")
def detail(pen_expediente_id):
    """Detalle de un Expediente"""
    pen_expediente = PenExpediente.query.get_or_404(pen_expediente_id)
    return render_template("pen_expedientes/detail.jinja2", pen_expediente=pen_expediente)
