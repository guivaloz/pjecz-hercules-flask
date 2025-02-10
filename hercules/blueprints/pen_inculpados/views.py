"""
Penales Inculpados, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.pen_inculpados.models import PenInculpado
from hercules.blueprints.permisos.models import Permiso
from hercules.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "PEN INCULPADOS"

pen_inculpados = Blueprint("pen_inculpados", __name__, template_folder="templates")


@pen_inculpados.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@pen_inculpados.route("/pen_inculpados/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Inculpados"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PenInculpado.query
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
    registros = consulta.order_by(PenInculpado.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "expediente": resultado.pen_expediente.expediente,
                "detalle": {
                    "nombres": resultado.nombres,
                    "url": url_for("pen_inculpados.detail", pen_inculpado_id=resultado.id),
                },
                "apellido_paterno": resultado.apellido_paterno,
                "apellido_materno": resultado.apellido_materno,
                "apodo": resultado.apodo,
                "sexo": resultado.sexo,
                "estado": resultado.estado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@pen_inculpados.route("/pen_inculpados")
def list_active():
    """Listado de Inculpados activos"""
    return render_template(
        "pen_inculpados/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Inculpados",
        estatus="A",
    )


@pen_inculpados.route("/pen_inculpados/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Inculpados inactivos"""
    return render_template(
        "pen_inculpados/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Inculpados inactivos",
        estatus="B",
    )


@pen_inculpados.route("/pen_inculpados/<int:pen_inculpado_id>")
def detail(pen_inculpado_id):
    """Detalle de un Inculpado"""
    pen_inculpado = PenInculpado.query.get_or_404(pen_inculpado_id)
    return render_template("pen_inculpados/detail.jinja2", pen_inculpado=pen_inculpado)
