"""
Penales Jueces, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.pen_jueces.models import PenJuez
from hercules.blueprints.permisos.models import Permiso
from hercules.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "PEN JUECES"

pen_jueces = Blueprint("pen_jueces", __name__, template_folder="templates")


@pen_jueces.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@pen_jueces.route("/pen_jueces/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Jueces"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PenJuez.query
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
    registros = consulta.order_by(PenJuez.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("pen_jueces.detail", pen_juez_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@pen_jueces.route("/pen_jueces")
def list_active():
    """Listado de Jueces activos"""
    return render_template(
        "pen_jueces/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Jueces",
        estatus="A",
    )


@pen_jueces.route("/pen_jueces/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Jueces inactivos"""
    return render_template(
        "pen_jueces/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Jueces inactivos",
        estatus="B",
    )


@pen_jueces.route("/pen_jueces/<int:pen_juez_id>")
def detail(pen_juez_id):
    """Detalle de un Juez"""
    pen_juez = PenJuez.query.get_or_404(pen_juez_id)
    return render_template("pen_jueces/detail.jinja2", pen_juez=pen_juez)
