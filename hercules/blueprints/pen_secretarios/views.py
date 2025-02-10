"""
Penales Secretarios, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.pen_secretarios.forms import PenSecretarioForm
from hercules.blueprints.pen_secretarios.models import PenSecretario
from hercules.blueprints.permisos.models import Permiso
from hercules.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "PEN SECRETARIOS"

pen_secretarios = Blueprint("pen_secretarios", __name__, template_folder="templates")


@pen_secretarios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@pen_secretarios.route("/pen_secretarios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Secretarios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PenSecretario.query
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
    registros = consulta.order_by(PenSecretario.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("pen_secretarios.detail", pen_secretario_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@pen_secretarios.route("/pen_secretarios")
def list_active():
    """Listado de Secretarios activos"""
    return render_template(
        "pen_secretarios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Secretarios",
        estatus="A",
    )


@pen_secretarios.route("/pen_secretarios/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Secretarios inactivos"""
    return render_template(
        "pen_secretarios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Secretarios inactivos",
        estatus="B",
    )


@pen_secretarios.route("/pen_secretarios/<int:pen_secretario_id>")
def detail(pen_secretario_id):
    """Detalle de un Secretario"""
    pen_secretario = PenSecretario.query.get_or_404(pen_secretario_id)
    return render_template("pen_secretarios/detail.jinja2", pen_secretario=pen_secretario)


@pen_secretarios.route("/pen_secretarios/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Secretario"""
    form = PenSecretarioForm()
    if form.validate_on_submit():
        pen_secretario = PenSecretario(nombre=safe_string(form.nombre.data, save_enie=True))
        pen_secretario.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Secretario {pen_secretario.nombre}"),
            url=url_for("pen_secretarios.detail", pen_secretario_id=pen_secretario.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("pen_secretarios/new.jinja2", form=form)


@pen_secretarios.route("/pen_secretarios/edicion/<int:pen_secretario_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(pen_secretario_id):
    """Editar Secretario"""
    pen_secretario = PenSecretario.query.get_or_404(pen_secretario_id)
    form = PenSecretarioForm()
    if form.validate_on_submit():
        pen_secretario.nombre = safe_string(form.nombre.data, save_enie=True)
        pen_secretario.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Secretario {pen_secretario.nombre}"),
            url=url_for("pen_secretarios.detail", pen_secretario_id=pen_secretario.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.nombre.data = pen_secretario.nombre
    return render_template("pen_secretarios/edit.jinja2", form=form, pen_secretario=pen_secretario)


@pen_secretarios.route("/pen_secretarios/eliminar/<int:pen_secretario_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(pen_secretario_id):
    """Eliminar Secretario"""
    pen_secretario = PenSecretario.query.get_or_404(pen_secretario_id)
    if pen_secretario.estatus == "A":
        pen_secretario.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Secretario {pen_secretario.nombre}"),
            url=url_for("pen_secretarios.detail", pen_secretario_id=pen_secretario.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_secretarios.detail", pen_secretario_id=pen_secretario.id))


@pen_secretarios.route("/pen_secretarios/recuperar/<int:pen_secretario_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(pen_secretario_id):
    """Recuperar Secretario"""
    pen_secretario = PenSecretario.query.get_or_404(pen_secretario_id)
    if pen_secretario.estatus == "B":
        pen_secretario.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Secretario {pen_secretario.nombre}"),
            url=url_for("pen_secretarios.detail", pen_secretario_id=pen_secretario.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_secretarios.detail", pen_secretario_id=pen_secretario.id))


@pen_secretarios.route("/pen_secretarios/select2_json", methods=["GET", "POST"])
def select2_json():
    """Proporcionar el JSON de secretarios para elegir con un Select2"""
    consulta = PenSecretario.query.filter(PenSecretario.estatus == "A")
    if "searchString" in request.form:
        nombre = safe_string(request.form["searchString"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(PenSecretario.nombre.contains(nombre))
    resultados = []
    for pen_secretario in consulta.order_by(PenSecretario.nombre).limit(10).all():
        resultados.append({"id": pen_secretario.id, "text": pen_secretario.nombre})
    return {"results": resultados, "pagination": {"more": False}}
