"""
Penales Agentes MP, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.pen_agentes_mp.models import PenAgenteMP
from hercules.blueprints.permisos.models import Permiso
from hercules.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "PEN AGENTES MP"

pen_agentes_mp = Blueprint("pen_agentes_mp", __name__, template_folder="templates")


@pen_agentes_mp.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@pen_agentes_mp.route("/pen_agentes_mp/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Agentes MP"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PenAgenteMP.query
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
    registros = consulta.order_by(PenAgenteMP.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("pen_agentes_mp.detail", pen_agente_mp_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@pen_agentes_mp.route("/pen_agentes_mp")
def list_active():
    """Listado de Agentes MP activos"""
    return render_template(
        "pen_agentes_mp/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Agentes MP",
        estatus="A",
    )


@pen_agentes_mp.route("/pen_agentes_mp/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Agentes MP inactivos"""
    return render_template(
        "pen_agentes_mp/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Agentes MP inactivos",
        estatus="B",
    )


@pen_agentes_mp.route("/pen_agentes_mp/<int:pen_agente_mp_id>")
def detail(pen_agente_mp_id):
    """Detalle de un Agente MP"""
    pen_agente_mp = PenAgenteMP.query.get_or_404(pen_agente_mp_id)
    return render_template("pen_agentes_mp/detail.jinja2", pen_agente_mp=pen_agente_mp)
