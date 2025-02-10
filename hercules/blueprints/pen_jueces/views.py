"""
Penales Jueces, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.pen_jueces.forms import PenJuezForm
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


@pen_jueces.route("/pen_jueces/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Juez"""
    form = PenJuezForm()
    if form.validate_on_submit():
        pen_juez = PenJuez(nombre=safe_string(form.nombre.data, save_enie=True))
        pen_juez.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Juez {pen_juez.nombre}"),
            url=url_for("pen_jueces.detail", pen_juez_id=pen_juez.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("pen_jueces/new.jinja2", form=form)


@pen_jueces.route("/pen_jueces/edicion/<int:pen_juez_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(pen_juez_id):
    """Editar Juez"""
    pen_juez = PenJuez.query.get_or_404(pen_juez_id)
    form = PenJuezForm()
    if form.validate_on_submit():
        pen_juez.nombre = safe_string(form.nombre.data, save_enie=True)
        pen_juez.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Juez {pen_juez.nombre}"),
            url=url_for("pen_jueces.detail", pen_juez_id=pen_juez.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.nombre.data = pen_juez.nombre
    return render_template("pen_jueces/edit.jinja2", form=form, pen_juez=pen_juez)


@pen_jueces.route("/pen_jueces/eliminar/<int:pen_juez_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(pen_juez_id):
    """Eliminar Juez"""
    pen_juez_id = PenJuez.query.get_or_404(pen_juez_id)
    if pen_juez_id.estatus == "A":
        pen_juez_id.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Modulo {pen_juez_id.nombre}"),
            url=url_for("pen_jueces.detail", pen_juez_id_id=pen_juez_id.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_jueces.detail", pen_juez_id=pen_juez_id.id))


@pen_jueces.route("/pen_jueces/recuperar/<int:pen_juez_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(pen_juez_id):
    """Recuperar Juez"""
    pen_juez = PenJuez.query.get_or_404(pen_juez_id)
    if pen_juez.estatus == "B":
        pen_juez.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Juez {pen_juez.nombre}"),
            url=url_for("pen_jueces.detail", pen_juez_id=pen_juez.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_jueces.detail", pen_juez_id=pen_juez.id))


@pen_jueces.route("/pen_jueces/select2_json", methods=["GET", "POST"])
def select2_json():
    """Proporcionar el JSON de jueces para elegir con un Select2"""
    consulta = PenJuez.query.filter(PenJuez.estatus == "A")
    if "searchString" in request.form:
        nombre = safe_string(request.form["searchString"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(PenJuez.nombre.contains(nombre))
    resultados = []
    for pen_juez in consulta.order_by(PenJuez.nombre).limit(10).all():
        resultados.append({"id": pen_juez.id, "text": pen_juez.nombre})
    return {"results": resultados, "pagination": {"more": False}}
