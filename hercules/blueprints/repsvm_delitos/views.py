"""
REPSVM Delitos, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.permisos.models import Permiso
from hercules.blueprints.repsvm_delitos.models import REPSVMDelito
from hercules.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "REPSVM DELITOS"

repsvm_delitos = Blueprint("repsvm_delitos", __name__, template_folder="templates")


@repsvm_delitos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@repsvm_delitos.route("/repsvm_delitos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Delitos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = REPSVMDelito.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    # Ordenar y paginar
    registros = consulta.order_by(REPSVMDelito.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("repsvm_delitos.detail", repsvm_delito_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@repsvm_delitos.route("/repsvm_delitos")
def list_active():
    """Listado de Delitos activos"""
    return render_template(
        "repsvm_delitos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Delitos",
        estatus="A",
    )


@repsvm_delitos.route("/repsvm_delitos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Delitos inactivos"""
    return render_template(
        "repsvm_delitos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Delitos inactivos",
        estatus="B",
    )


@repsvm_delitos.route("/repsvm_delitos/<int:repsvm_delito_id>")
def detail(repsvm_delito_id):
    """Detalle de un Delitos"""
    repsvm_delito = REPSVMDelito.query.get_or_404(repsvm_delito_id)
    return render_template("repsvm_delitos/detail.jinja2", repsvm_delito=repsvm_delito)
