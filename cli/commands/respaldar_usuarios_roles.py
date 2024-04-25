"""
Respaldar Usuarios-Roles
"""

import csv
from pathlib import Path

import click

from hercules.blueprints.usuarios.models import Usuario

USUARIOS_ROLES_CSV = "seed/usuarios_roles.csv"


def respaldar_usuarios_roles():
    """Respaldar Usuarios-Roles a un archivo CSV"""
    directorio = Path("seed")
    directorio.mkdir(exist_ok=True)
    ruta = Path(USUARIOS_ROLES_CSV)
    if ruta.exists():
        ruta.unlink()
    click.echo("Respaldando usuarios...")
    contador = 0
    usuarios = Usuario.query.order_by(Usuario.id).all()
    with open(ruta, "w", encoding="utf8") as puntero:
        respaldo = csv.writer(puntero)
        respaldo.writerow(
            [
                "usuario_id",
                "autoridad_clave",
                "email",
                "nombres",
                "apellido_paterno",
                "apellido_materno",
                "curp",
                "puesto",
                "roles",
                "estatus",
            ]
        )
        for usuario in usuarios:
            roles_list = []
            for usuario_rol in usuario.usuarios_roles:
                if usuario_rol.estatus == "A":
                    roles_list.append(usuario_rol.rol.nombre)
            respaldo.writerow(
                [
                    usuario.id,
                    usuario.autoridad.clave,
                    usuario.email,
                    usuario.nombres,
                    usuario.apellido_paterno,
                    usuario.apellido_materno,
                    usuario.curp,
                    usuario.puesto,
                    ",".join(roles_list),
                    usuario.estatus,
                ]
            )
            contador += 1
            if contador % 100 == 0:
                click.echo(f"  Van {contador}...")
    click.echo(f"  {contador} en {ruta.name}")
