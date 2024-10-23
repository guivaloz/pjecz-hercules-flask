"""
CID Formatos, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.exceptions import NotFound

from hercules.blueprints.bitacoras.models import Bitacora
from hercules.blueprints.cid_areas.models import CIDArea
from hercules.blueprints.cid_areas_autoridades.models import CIDAreaAutoridad
from hercules.blueprints.cid_formatos.forms import CIDFormatoEdit, CIDFormatoForm
from hercules.blueprints.cid_formatos.models import CIDFormato
from hercules.blueprints.cid_procedimientos.models import CIDProcedimiento
from hercules.blueprints.modulos.models import Modulo
from hercules.blueprints.permisos.models import Permiso
from hercules.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.exceptions import (
    MyBucketNotFoundError,
    MyFilenameError,
    MyFileNotFoundError,
    MyMissingConfigurationError,
    MyNotAllowedExtensionError,
    MyNotValidParamError,
    MyUnknownExtensionError,
)
from lib.safe_string import safe_clave, safe_message, safe_string
from lib.storage import GoogleCloudStorage

MODULO = "CID FORMATOS"

cid_formatos = Blueprint("cid_formatos", __name__, template_folder="templates")

SUBDIRECTORIO = "cid_formatos"

# Roles que deben estar en la base de datos
ROL_ADMINISTRADOR = "ADMINISTRADOR"
ROL_COORDINADOR = "SICGD COORDINADOR"
ROL_DIRECTOR_JEFE = "SICGD DIRECTOR O JEFE"
ROL_DUENO_PROCESO = "SICGD DUENO DE PROCESO"
ROL_INVOLUCRADO = "SICGD INVOLUCRADO"
ROLES_CON_FORMATOS_PROPIOS = (ROL_COORDINADOR, ROL_DIRECTOR_JEFE, ROL_DUENO_PROCESO)


@cid_formatos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cid_formatos.route("/cid_formatos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Formatos"""

    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()

    # Consultar
    consulta = CIDFormato.query

    # Primero hacer el join si se necesita
    if "cid_areas[]" in request.form or "seguimiento" in request.form or "usuario_id" in request.form:
        consulta = consulta.join(CIDProcedimiento)

    # Si viene el filtro con un listado de ids de areas, filtrar por ellas
    if "cid_areas[]" in request.form:
        areas_a_filtrar = request.form.getlist("cid_areas[]")
        listado_areas_ids = [int(area_id) for area_id in areas_a_filtrar]
        consulta = consulta.filter(CIDProcedimiento.id == CIDFormato.procedimiento_id)
        consulta = consulta.filter(CIDProcedimiento.cid_area_id.in_(listado_areas_ids))

    # Filtrar
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "codigo" in request.form:
        codigo = safe_clave(request.form["codigo"])
        if codigo != "":
            consulta = consulta.filter(CIDFormato.codigo.contains(codigo))
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"], save_enie=True)
        if descripcion != "":
            consulta = consulta.filter(CIDFormato.descripcion.contains(descripcion))
    if "seguimiento" in request.form:
        consulta = consulta.filter(CIDProcedimiento.seguimiento == request.form["seguimiento"])
    if "usuario_id" in request.form:
        usuario_id = request.form["usuario_id"]
        consulta = consulta.filter(CIDProcedimiento.usuario_id == usuario_id)

    # Ordenar y paginar
    registros = consulta.order_by(CIDFormato.descripcion).offset(start).limit(rows_per_page).all()
    total = consulta.count()

    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "descripcion": resultado.descripcion,
                    "url": url_for("cid_formatos.detail", cid_formato_id=resultado.id),
                },
                "titulo_procedimiento": resultado.procedimiento.titulo_procedimiento,
                "codigo": resultado.codigo,
                "autoridad": resultado.procedimiento.autoridad.clave,
                "cid_area_clave": resultado.cid_area.clave,
                "descargar": {
                    "archivo": resultado.archivo,
                    "url": resultado.url,
                },
            }
        )

    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cid_formatos.route("/cid_formatos/admin_datatable_json", methods=["GET", "POST"])
def admin_datatable_json():
    """DataTable JSON para listado de Formatos"""

    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()

    # Consultar
    consulta = CIDFormato.query

    # Primero hacer el join si se necesita
    if "cid_areas[]" in request.form or "seguimiento" in request.form or "usuario_id" in request.form:
        consulta = consulta.join(CIDProcedimiento)

    # Si viene el filtro con un listado de ids de áreas, filtrar por ellas
    if "cid_areas[]" in request.form:
        areas_a_filtrar = request.form.getlist("cid_areas[]")
        listado_areas_ids = [int(area_id) for area_id in areas_a_filtrar]
        consulta = consulta.filter(CIDProcedimiento.id == CIDFormato.procedimiento_id)
        consulta = consulta.filter(CIDProcedimiento.cid_area_id.in_(listado_areas_ids))

    # Filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(CIDFormato.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(CIDFormato.estatus == "A")
    if "cid_formato_id" in request.form:
        try:
            cid_formato_id = int(request.form["cid_formato_id"])
            consulta = consulta.filter(CIDFormato.id == cid_formato_id)
        except ValueError:
            pass
    if "usuario_id" in request.form:
        usuario_id = request.form["usuario_id"]
        consulta = consulta.filter(CIDProcedimiento.usuario_id == usuario_id)
    if "codigo" in request.form:
        codigo = safe_clave(request.form["codigo"])
        if codigo != "":
            consulta = consulta.filter(CIDFormato.codigo.contains(codigo))
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"], save_enie=True)
        if descripcion != "":
            consulta = consulta.filter(CIDFormato.descripcion.contains(descripcion))
    if "seguimiento" in request.form:
        consulta = consulta.filter(CIDProcedimiento.seguimiento == request.form["seguimiento"])

    # Ordenar y paginar
    registros = consulta.order_by(CIDFormato.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()

    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        print(resultado.procedimiento.usuario_id)
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("cid_formatos.detail", cid_formato_id=resultado.id),
                },
                "titulo_procedimiento": resultado.procedimiento.titulo_procedimiento,
                "codigo": resultado.codigo,
                "descripcion": resultado.descripcion,
                "autoridad": resultado.procedimiento.autoridad.clave,
                "cid_area_clave": resultado.cid_area.clave,
                "descargar": {
                    "archivo": resultado.archivo,
                    "url": resultado.url,
                },
            }
        )

    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cid_formatos.route("/cid_formatos")
def list_active():
    """Listado de formatos autorizados de mis áreas"""

    # Definir valores por defecto
    current_user_cid_areas_ids = []
    current_user_roles = set(current_user.get_roles())
    filtros = None
    plantilla = "cid_formatos/list.jinja2"
    titulo = None

    # Si es administrador, usar la plantilla es list_admin.jinja2
    if current_user.can_admin(MODULO):
        plantilla = "cid_formatos/list_admin.jinja2"

    # Si viene area_id o area_clave en la URL, agregar a los filtros
    cid_area = None
    try:
        if "area_id" in request.args:
            area_id = int(request.args["area_id"])
            cid_area = CIDArea.query.get(area_id)
        elif "area_clave" in request.args:
            area_clave = safe_clave(request.args["area_clave"])
            cid_area = CIDArea.query.filter_by(clave=area_clave).first()
        if cid_area is not None:
            filtros = {"estatus": "A", "cid_area": cid_area.id}
            titulo = f"Procedimientos del área {cid_area.nombre}"
    except (TypeError, ValueError):
        pass

    # Si titulo es None y es administrador, mostrar todos los formatos activos
    if titulo is None and current_user.can_admin(MODULO):
        titulo = "Todos los formatos activos"
        filtros = {"estatus": "A"}

    # Si titulo es none y tiene el rol "SICGD AUDITOR", mostrar los formatos de procedimientos autorizados
    if titulo is None and "SICGD AUDITOR" in current_user_roles:
        titulo = "Formatos de procedimientos autorizados"
        filtros = {"estatus": "A", "seguimiento": "AUTORIZADO", "seguimiento_posterior": "ARCHIVADO"}

    # Si titulo es None y tiene el rol "SICGD COORDINADOR", mostrar todos los formatos activos
    if titulo is None and "SICGD COORDINADOR" in current_user_roles:
        titulo = "Todos los formatos"
        filtros = {"estatus": "A"}

    # Obtener los IDs de las áreas del usuario
    current_user_cid_areas_ids = [
        cid_area.id
        for cid_area in (
            CIDArea.query.join(CIDAreaAutoridad).filter(CIDAreaAutoridad.autoridad_id == current_user.autoridad.id).all()
        )
    ]

    # Si el titulo es None y tiene áreas, mostrar los procedimientos autorizados de sus áreas
    if titulo is None and len(current_user_cid_areas_ids) > 0:
        titulo = "Formatos de procedimientos autorizados de mis áreas"
        filtros = {
            "estatus": "A",
            "seguimiento": "AUTORIZADO",
            "seguimiento_posterior": "ARCHIVADO",
            "cid_areas": current_user_cid_areas_ids,
        }

    # Por defecto, mostrar todos los procedimientos autorizados
    if titulo is None:
        titulo = "Formatos de procedimientos autorizados de todas las áreas"
        filtros = {"estatus": "A", "seguimiento": "AUTORIZADO", "seguimiento_posterior": "ARCHIVADO"}

    # Entregar
    return render_template(
        plantilla,
        titulo=titulo,
        filtros=json.dumps(filtros),
        estatus="A",
    )


@cid_formatos.route("/cid_formatos/eliminados")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de formatos eliminados, solo para administrador"""
    return render_template(
        "cid_formatos/list_admin.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Todos los formatos eliminados",
        estatus="B",
    )


@cid_formatos.route("/cid_formatos/<int:cid_formato_id>")
def detail(cid_formato_id):
    """Detalle de un CID Formato"""
    cid_formato = CIDFormato.query.get_or_404(cid_formato_id)
    return render_template(
        "cid_formatos/detail.jinja2",
        cid_formato=cid_formato,
        show_button_edit_admin=current_user.can_admin(MODULO) or ROL_COORDINADOR in current_user.get_roles(),
    )


@cid_formatos.route("/cid_formatos/nuevo/<int:cid_procedimiento_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new(cid_procedimiento_id):
    """Nuevo CID Formato"""
    # Validar procedimiento
    cid_procedimiento = CIDProcedimiento.query.get_or_404(cid_procedimiento_id)
    if cid_procedimiento.estatus != "A":
        flash("El procedmiento no es activo.", "warning")
        return redirect(url_for("cid_procedimientos.list_active"))
    # Si viene el formulario
    form = CIDFormatoForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        es_valido = True
        # Validar la descripción
        descripcion = safe_string(form.descripcion.data)
        if descripcion == "":
            flash("La descripción es requerida.", "warning")
            es_valido = False
        # Validar archivo
        archivo = request.files["archivo"]
        storage = GoogleCloudStorage(base_directory=SUBDIRECTORIO, allowed_extensions=["pdf"])
        try:
            storage.set_content_type(archivo.filename)
        except MyNotAllowedExtensionError:
            flash("Tipo de archivo no permitido.", "warning")
            es_valido = False
        except MyUnknownExtensionError:
            flash("Tipo de archivo desconocido.", "warning")
            es_valido = False

        # Si es válido
        if es_valido:
            # Insertar el registro, para obtener el ID
            cid_formato = CIDFormato(
                procedimiento=cid_procedimiento,
                codigo=safe_clave(form.codigo.data),
                descripcion=descripcion,
                cid_area_id=1,
            )
            cid_formato.save()
            # Subir a Google Cloud Storage
            es_exitoso = True
            try:
                storage.set_filename(hashed_id=cid_formato.encode_id(), description=descripcion)
                storage.upload(archivo.stream.read())
                cid_formato.archivo = archivo.filename  # Conservar el nombre original
                cid_formato.url = storage.url
                cid_formato.save()
            except (MyFilenameError, MyNotAllowedExtensionError, MyUnknownExtensionError):
                flash("Error fatal al subir el archivo a GCS.", "warning")
                es_exitoso = False
            except MyMissingConfigurationError:
                flash("Error al subir el archivo porque falla la configuración de GCS.", "danger")
                es_exitoso = False
            except Exception:
                flash("Error desconocido al subir el archivo.", "danger")
                es_exitoso = False
            # Si se sube con exito, actualizar el registro con la URL del archivo y mostrar el detalle
            if es_exitoso:
                # Registrar la acción en la bitácora
                bitacora = Bitacora(
                    modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                    usuario=current_user,
                    descripcion=safe_message(f"Nuevo formato {cid_formato.descripcion}"),
                    url=url_for("cid_formatos.detail", cid_formato_id=cid_formato.id),
                )
                bitacora.save()
                flash(bitacora.descripcion, "success")
                return redirect(bitacora.url)
    # Mostrar formulario
    form.procedimiento_titulo.data = cid_procedimiento.titulo_procedimiento  # Read only
    return render_template("cid_formatos/new.jinja2", form=form, cid_procedimiento=cid_procedimiento)


@cid_formatos.route("/cid_formatos/edicion/<int:cid_formato_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cid_formato_id):
    """Editar CID Formato"""
    cid_formato = CIDFormato.query.get_or_404(cid_formato_id)
    form = CIDFormatoEdit()
    if form.validate_on_submit():
        cid_formato.codigo = safe_clave(form.codigo.data)
        cid_formato.descripcion = safe_string(form.descripcion.data)
        cid_formato.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado el formato {cid_formato.descripcion}"),
            url=url_for("cid_formatos.detail", cid_formato_id=cid_formato.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.procedimiento_titulo.data = cid_formato.procedimiento.titulo_procedimiento  # Read only
    form.codigo.data = cid_formato.codigo
    form.descripcion.data = cid_formato.descripcion
    return render_template("cid_formatos/edit.jinja2", form=form, cid_formato=cid_formato)


@cid_formatos.route("/cid_formatos/eliminar/<int:cid_formato_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(cid_formato_id):
    """Eliminar Formato"""
    cid_formato = CIDFormato.query.get_or_404(cid_formato_id)
    if cid_formato.estatus == "A":
        cid_formato.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado el formato {cid_formato.descripcion}"),
            url=url_for("cid_formatos.detail", cid_formato_id=cid_formato.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cid_formatos.detail", cid_formato_id=cid_formato.id))


@cid_formatos.route("/cid_formatos/recuperar/<int:cid_formato_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(cid_formato_id):
    """Recuperar Formato"""
    cid_formato = CIDFormato.query.get_or_404(cid_formato_id)
    if cid_formato.estatus == "B":
        cid_formato.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado el formato {cid_formato.descripcion}"),
            url=url_for("cid_formatos.detail", cid_formato_id=cid_formato.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cid_formatos.detail", cid_formato_id=cid_formato.id))


@cid_formatos.route("/cid_formatos/exportar_lista_maestra_xlsx")
@permission_required(MODULO, Permiso.VER)
def exportar_xlsx():
    """Lanzar tarea en el fondo para exportar la Lista Maestra a un archivo XLSX"""
    tarea = current_user.launch_task(
        comando="cid_formatos.tasks.lanzar_exportar_xlsx",
        mensaje="Exportando la Lista Maestra a un archivo XLSX...",
    )
    flash("Se ha lanzado esta tarea en el fondo. Esta página se va a recargar en 30 segundos...", "info")
    return redirect(url_for("tareas.detail", tarea_id=tarea.id))
