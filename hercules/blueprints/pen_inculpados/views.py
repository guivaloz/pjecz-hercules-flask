"""
Penales Inculpados, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.pen_expedientes.models import PenExpediente
from hercules.blueprints.pen_inculpados.forms import PenInculpadoForm
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
    if "pen_expediente_id" in request.form:
        consulta = consulta.filter_by(pen_expediente_id=request.form["pen_expediente_id"])
    if "nombres" in request.form:
        nombres = safe_string(request.form["nombres"], save_enie=True)
        if nombres != "":
            consulta = consulta.filter(PenInculpado.nombres.contains(nombres))
    if "apellido_paterno" in request.form:
        apellido_paterno = safe_string(request.form["apellido_paterno"], save_enie=True)
        if apellido_paterno != "":
            consulta = consulta.filter(PenInculpado.apellido_paterno.contains(apellido_paterno))
    if "apellido_materno" in request.form:
        apellido_materno = safe_string(request.form["apellido_materno"], save_enie=True)
        if apellido_materno != "":
            consulta = consulta.filter(PenInculpado.apellido_materno.contains(apellido_materno))
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
                    "nombre": resultado.nombre,
                    "url": url_for("pen_inculpados.detail", pen_inculpado_id=resultado.id),
                },
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


@pen_inculpados.route("/pen_inculpados/nuevo/<int:pen_expediente_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new(pen_expediente_id):
    """Nuevo Inculpado"""
    pen_expediente = PenExpediente.query.get_or_404(pen_expediente_id)
    form = PenInculpadoForm()
    if form.validate_on_submit():
        # Guardar
        pen_inculpado = PenInculpado(
            pen_expediente_id=pen_expediente.id,
            nombres=safe_string(form.nombres.data, save_enie=True),
            apellido_paterno=safe_string(form.apellido_paterno.data, save_enie=True),
            apellido_materno=safe_string(form.apellido_materno.data, save_enie=True),
            apodo=safe_string(form.apodo.data, save_enie=True),
            sexo=form.sexo.data,
            estado=safe_string(form.estado.data, save_enie=True),
            solicitud_mp=safe_string(form.solicitud_mp.data, save_enie=True),
        )
        pen_inculpado.save()
        # Guardar bitácora
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Inculpado {pen_inculpado.nombres}"),
            url=url_for("pen_inculpados.detail", pen_inculpado_id=pen_inculpado.id),
        )
        bitacora.save()
        # Entregar detalle
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("pen_inculpados/new.jinja2", form=form, pen_expediente=pen_expediente)


@pen_inculpados.route("/pen_inculpados/edicion/<int:pen_inculpado_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(pen_inculpado_id):
    """Editar Inculpado"""
    pen_inculpado = PenInculpado.query.get_or_404(pen_inculpado_id)
    form = PenInculpadoForm()
    if form.validate_on_submit():
        pen_inculpado.nombres = safe_string(form.nombres.data, save_enie=True)
        pen_inculpado.apellido_paterno = safe_string(form.apellido_paterno.data, save_enie=True)
        pen_inculpado.apellido_materno = safe_string(form.apellido_materno.data, save_enie=True)
        pen_inculpado.apodo = safe_string(form.apodo.data, save_enie=True)
        pen_inculpado.sexo = form.sexo.data
        pen_inculpado.estado = safe_string(form.estado.data, save_enie=True)
        pen_inculpado.solicitud_mp = safe_string(form.solicitud_mp.data, save_enie=True)
        pen_inculpado.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Inculpado {pen_inculpado.nombres}"),
            url=url_for("pen_inculpados.detail", pen_inculpado_id=pen_inculpado.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.nombres.data = pen_inculpado.nombres
    form.apellido_paterno.data = pen_inculpado.apellido_paterno
    form.apellido_materno.data = pen_inculpado.apellido_materno
    form.apodo.data = pen_inculpado.apodo
    form.sexo.data = pen_inculpado.sexo
    form.estado.data = pen_inculpado.estado
    form.solicitud_mp.data = pen_inculpado.solicitud_mp
    return render_template("pen_inculpados/edit.jinja2", form=form, pen_inculpado=pen_inculpado)


@pen_inculpados.route("/pen_inculpados/eliminar/<int:pen_inculpado_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(pen_inculpado_id):
    """Eliminar Inculpado"""
    pen_inculpado = PenInculpado.query.get_or_404(pen_inculpado_id)
    if pen_inculpado.estatus == "A":
        pen_inculpado.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Inculpado {pen_inculpado.nombre}"),
            url=url_for("pen_inculpados.detail", pen_inculpado_id=pen_inculpado.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_inculpados.detail", pen_inculpado_id=pen_inculpado.id))


@pen_inculpados.route("/pen_inculpados/recuperar/<int:pen_inculpado_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(pen_inculpado_id):
    """Recuperar Inculpado"""
    pen_inculpado = PenInculpado.query.get_or_404(pen_inculpado_id)
    if pen_inculpado.estatus == "B":
        pen_inculpado.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Inculpado {pen_inculpado.nombre}"),
            url=url_for("pen_inculpados.detail", pen_inculpado_id=pen_inculpado.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_inculpados.detail", pen_inculpado_id=pen_inculpado.id))
