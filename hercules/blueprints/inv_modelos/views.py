"""
Inventarios Modelos, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.inv_marcas.models import InvMarca
from hercules.blueprints.inv_modelos.forms import InvModeloForm
from hercules.blueprints.inv_modelos.models import InvModelo
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.permisos.models import Permiso
from hercules.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "INV MODELOS"

inv_modelos = Blueprint("inv_modelos", __name__, template_folder="templates")


@inv_modelos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@inv_modelos.route("/inv_modelos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de InvModelo"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = InvModelo.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "inv_marca_id" in request.form:
        consulta = consulta.filter_by(inv_marca_id=request.form["inv_marca_id"])
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"])
        if descripcion != "":
            consulta = consulta.filter(InvModelo.descripcion.contains(descripcion))
    # Ordenar y paginar
    registros = consulta.order_by(InvModelo.descripcion).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "descripcion": resultado.descripcion,
                    "url": url_for("inv_modelos.detail", inv_modelo_id=resultado.id),
                },
                "marca": {
                    "nombre": resultado.inv_marca.nombre,
                    "url": (
                        url_for("inv_marcas.detail", inv_marca_id=resultado.inv_marca_id)
                        if current_user.can_view("INV MARCAS")
                        else ""
                    ),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@inv_modelos.route("/inv_modelos")
def list_active():
    """Listado de InvModelo activos"""
    return render_template(
        "inv_modelos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Modelos",
        estatus="A",
    )


@inv_modelos.route("/inv_modelos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de InvModelo inactivos"""
    return render_template(
        "inv_modelos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Modelos inactivos",
        estatus="B",
    )


@inv_modelos.route("/inv_modelos/<int:inv_modelo_id>")
def detail(inv_modelo_id):
    """Detalle de un InvModelo"""
    inv_modelo = InvModelo.query.get_or_404(inv_modelo_id)
    return render_template("inv_modelos/detail.jinja2", inv_modelo=inv_modelo)


@inv_modelos.route("/inv_modelos/nuevo/<int:inv_marca_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new(inv_marca_id):
    """Nuevo InvModelo"""
    inv_marca = InvMarca.query.get_or_404(inv_marca_id)
    form = InvModeloForm()
    if form.validate_on_submit():
        # Validar descripcion
        descripcion = safe_string(form.descripcion.data, save_enie=True)
        if descripcion == "":
            flash("La descripcion es incorrecta", "warning")
            return render_template("inv_modelos/new.jinja2", form=form)
        # Guardar
        inv_modelo = InvModelo(
            inv_marca_id=inv_marca.id,
            descripcion=descripcion,
        )
        inv_modelo.save()
        # Guardar bitácora
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo InvModelo {inv_modelo.descripcion} de {inv_marca.nombre}"),
            url=url_for("inv_modelos.detail", inv_modelo_id=inv_modelo.id),
        )
        bitacora.save()
        # Entregar detalle
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("inv_modelos/new.jinja2", inv_marca=inv_marca, form=form)


@inv_modelos.route("/inv_modelos/edicion/<int:inv_modelo_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(inv_modelo_id):
    """Editar InvModelo"""
    inv_modelo = InvModelo.query.get_or_404(inv_modelo_id)
    form = InvModeloForm()
    if form.validate_on_submit():
        es_valido = True
        # Validar descripcion
        descripcion = safe_string(form.descripcion.data, save_enie=True)
        if descripcion == "":
            flash("La descripcion es incorrecta", "warning")
            es_valido = False
        # Si es válido
        if es_valido:
            # Guardar
            inv_modelo.descripcion = descripcion
            inv_modelo.save()
            # Guardar bitácora
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado InvModelo {inv_modelo.descripcion} de {inv_modelo.inv_marca.nombre}"),
                url=url_for("inv_modelos.detail", inv_modelo_id=inv_modelo.id),
            )
            bitacora.save()
            # Entregar detalle
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.descripcion.data = inv_modelo.descripcion
    return render_template("inv_modelos/edit.jinja2", form=form, inv_modelo=inv_modelo)


@inv_modelos.route("/inv_modelos/eliminar/<int:inv_modelo_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(inv_modelo_id):
    """Eliminar InvModelo"""
    inv_modelo = InvModelo.query.get_or_404(inv_modelo_id)
    if inv_modelo.estatus == "A":
        inv_modelo.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado InvModelo {inv_modelo.descripcion} de {inv_modelo.inv_marca.nombre}"),
            url=url_for("inv_modelos.detail", inv_modelo_id=inv_modelo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("inv_modelos.detail", inv_modelo_id=inv_modelo.id))


@inv_modelos.route("/inv_modelos/recuperar/<int:inv_modelo_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(inv_modelo_id):
    """Recuperar InvModelo"""
    inv_modelo = InvModelo.query.get_or_404(inv_modelo_id)
    if inv_modelo.estatus == "B":
        inv_modelo.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado InvModelo {inv_modelo.descripcion} de {inv_modelo.inv_marca.nombre}"),
            url=url_for("inv_modelos.detail", inv_modelo_id=inv_modelo.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("inv_modelos.detail", inv_modelo_id=inv_modelo.id))


@inv_modelos.route("/inv_modelos/inv_modelos_json", methods=["POST"])
def query_inv_modelos_json():
    """Proporcionar el JSON para elegir un InvModelo con Select2"""
    consulta = InvModelo.query
    # Filtrar si viene el ID de InvMarca
    if "inv_marca_id" in request.args:
        try:
            consulta = consulta.filter(InvModelo.inv_marca_id == int(request.args["inv_marca_id"]))
        except ValueError:
            pass
    # Filtrar por descripción de InvModelo
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"], save_enie=True)
        if descripcion != "":
            consulta = consulta.filter(InvModelo.descripcion.contains(descripcion))
    # Filtrar por el nombre de InvMarca o por la descripción de InvModelo
    if "nombre_o_descripcion" in request.form:
        nombre_o_descripcion = safe_string(request.form["nombre_o_descripcion"], save_enie=True)
        if nombre_o_descripcion != "":
            consulta = consulta.join(InvMarca).filter(
                or_(InvMarca.nombre.contains(nombre_o_descripcion), InvModelo.descripcion.contains(nombre_o_descripcion))
            )
    # Entregar las opciones para Select2
    results = []
    for inv_modelo in consulta.filter(InvModelo.estatus == "A").order_by(InvModelo.descripcion).limit(15).all():
        results.append({"id": inv_modelo.id, "text": f"{inv_modelo.inv_marca.nombre} - {inv_modelo.descripcion}"})
    return {"results": results, "pagination": {"more": False}}
