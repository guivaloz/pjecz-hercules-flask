"""
Penales Expedientes, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from hercules.blueprints.autoridades.models import Autoridad
from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.distritos.models import Distrito
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.pen_expedientes.forms import PenExpedienteForm
from hercules.blueprints.pen_expedientes.models import PenExpediente
from hercules.blueprints.permisos.models import Permiso
from hercules.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_expediente, safe_message, safe_string

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
                "pen_juez_nombre": resultado.pen_juez.nombre,
                "pen_secretario_nombre": resultado.pen_secretario.nombre,
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


@pen_expedientes.route("/pen_expedientes/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Expediente"""
    form = PenExpedienteForm()
    if form.validate_on_submit():
        expediente = safe_expediente(form.expediente.data)
        fecha = form.fecha.data
        autoridad_id = form.autoridad.data  # Select2
        pen_juez_id = form.pen_juez.data  # Select2
        pen_secretario_id = form.pen_secretario.data  # Select2
        pen_agente_mp_id = form.pen_agente_mp.data  # Select2
        delitos = safe_string(form.delitos.data, save_enie=True)
        pen_expediente = PenExpediente(
            expediente=expediente,
            fecha=fecha,
            autoridad_id=autoridad_id,
            pen_juez_id=pen_juez_id,
            pen_secretario_id=pen_secretario_id,
            pen_agente_mp_id=pen_agente_mp_id,
            delitos=delitos,
        )
        pen_expediente.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Expediente {pen_expediente.expediente}"),
            url=url_for("pen_expedientes.detail", pen_expediente_id=pen_expediente.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("pen_expedientes/new.jinja2", form=form)


@pen_expedientes.route("/pen_expedientes/edicion/<int:pen_expediente_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(pen_expediente_id):
    """Editar Expediente"""
    pen_expediente = PenExpediente.query.get_or_404(pen_expediente_id)
    form = PenExpedienteForm()
    if form.validate_on_submit():
        pen_expediente.expediente = safe_expediente(form.expediente.data)
        pen_expediente.fecha = form.fecha.data
        pen_expediente.autoridad_id = form.autoridad.data  # Select2
        pen_expediente.pen_juez_id = form.pen_juez.data  # Select2
        pen_expediente.pen_secretario_id = form.pen_secretario.data  # Select2
        pen_expediente.pen_agente_mp_id = form.pen_agente_mp.data  # Select2
        pen_expediente.delitos = safe_string(form.delitos.data)
        pen_expediente.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Expediente {pen_expediente.delitos}"),
            url=url_for("pen_expedientes.detail", pen_expediente_id=pen_expediente.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.expediente.data = pen_expediente.expediente
    form.fecha.data = pen_expediente.fecha
    form.autoridad.data = pen_expediente.autoridad_id  # Select2
    form.pen_juez.data = pen_expediente.pen_juez_id  # Select2
    form.pen_secretario.data = pen_expediente.pen_secretario_id  # Select2
    form.pen_agente_mp.data = pen_expediente.pen_agente_mp_id  # Select2
    form.delitos.data = pen_expediente.delitos
    return render_template("pen_expedientes/edit.jinja2", form=form, pen_expediente=pen_expediente)


@pen_expedientes.route("/pen_expedientes/eliminar/<int:pen_expediente_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(pen_expediente_id):
    """Eliminar Expediente"""
    pen_expediente = PenExpediente.query.get_or_404(pen_expediente_id)
    if pen_expediente.estatus == "A":
        pen_expediente.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Expediente {pen_expediente.expediente}"),
            url=url_for("pen_expedientes.detail", pen_expediente_id=pen_expediente.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_expedientes.detail", pen_expediente_id=pen_expediente.id))


@pen_expedientes.route("/pen_expedientes/recuperar/<int:pen_expediente_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(pen_expediente_id):
    """Recuperar Expediente"""
    pen_expediente = PenExpediente.query.get_or_404(pen_expediente_id)
    if pen_expediente.estatus == "B":
        pen_expediente.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Expediente {pen_expediente.expediente}"),
            url=url_for("pen_expedientes.detail", pen_expediente_id=pen_expediente.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pen_expedientes.detail", pen_expediente_id=pen_expediente.id))
