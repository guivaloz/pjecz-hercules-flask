"""
Penales Agentes MP, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.pen_agentes_mp.forms import PenAgenteMPForm
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


@pen_agentes_mp.route("/pen_agentes_mp/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Agente MP"""
    form = PenAgenteMPForm()
    if form.validate_on_submit():
        pen_agente_mp = PenAgenteMP(nombre=safe_string(form.nombre.data, save_enie=True))
        pen_agente_mp.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Agente MP {pen_agente_mp.nombre}"),
            url=url_for("pen_agentes_mp.detail", pen_agente_mp_id=pen_agente_mp.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("pen_agentes_mp/new.jinja2", form=form)


@pen_agentes_mp.route("/pen_agentes_mp/edicion/<int:pen_agente_mp_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(pen_agente_mp_id):
    """Editar Agente MP"""
    pen_agente_mp = PenAgenteMP.query.get_or_404(pen_agente_mp_id)
    form = PenAgenteMPForm()
    if form.validate_on_submit():
        pen_agente_mp.nombre = safe_string(form.nombre.data, save_enie=True)
        pen_agente_mp.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Agente MP {pen_agente_mp.nombre}"),
            url=url_for("pen_agentes_mp.detail", pen_agente_mp_id=pen_agente_mp.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.nombre.data = pen_agente_mp.nombre
    return render_template("pen_agentes_mp/edit.jinja2", form=form, pen_agente_mp=pen_agente_mp)


@pen_agentes_mp.route("/pen_agentes_mp/eliminar/<int:pen_agente_mp_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(pen_agente_mp_id):
    """Eliminar Agente MP"""
    pen_agente_mp = PenAgenteMP.query.get_or_404(pen_agente_mp_id)
    if pen_agente_mp.estatus == "A":
        pen_agente_mp.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Modulo {pen_agente_mp.nombre}"),
            url=url_for("pen_agentes_mp.detail", instance_id=pen_agente_mp.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_agentes_mp.detail", pen_agente_mp_id=pen_agente_mp.id))


@pen_agentes_mp.route("/pen_agentes_mp/recuperar/<int:pen_agente_mp_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(pen_agente_mp_id):
    """Recuperar Agente MP"""
    pen_agente_mp = PenAgenteMP.query.get_or_404(pen_agente_mp_id)
    if pen_agente_mp.estatus == "B":
        pen_agente_mp.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Agente MP {pen_agente_mp.nombre}"),
            url=url_for("pen_agentes_mp.detail", pen_agente_mp_id=pen_agente_mp.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_agentes_mp.detail", pen_agente_mp_id=pen_agente_mp.id))


@pen_agentes_mp.route("/pen_agentes_mp/select2_json", methods=["GET", "POST"])
def select2_json():
    """Proporcionar el JSON de agentes mp para elegir con un Select2"""
    consulta = PenAgenteMP.query.filter(PenAgenteMP.estatus == "A")
    if "searchString" in request.form:
        nombre = safe_string(request.form["searchString"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(PenAgenteMP.nombre.contains(nombre))
    resultados = []
    for pen_agente_mp in consulta.order_by(PenAgenteMP.nombre).limit(10).all():
        resultados.append({"id": pen_agente_mp.id, "text": pen_agente_mp.nombre})
    return {"results": resultados, "pagination": {"more": False}}
