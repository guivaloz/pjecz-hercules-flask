"""
Penales Inculpados, modelos
"""

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hercules.extensions import database
from lib.universal_mixin import UniversalMixin


class PenInculpado(database.Model, UniversalMixin):
    """PenInculpado"""

    SEXOS = {
        "M": "MASCULINO",
        "F": "FEMENINO",
        "-": "SIN SEXO",
    }

    # Nombre de la tabla
    __tablename__ = "pen_inculpados"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    pen_expediente_id: Mapped[int] = mapped_column(ForeignKey("pen_expedientes.id"))
    pen_expediente: Mapped["PenExpediente"] = relationship(back_populates="pen_inculpados")

    # Columnas
    nombres: Mapped[str] = mapped_column(String(256))
    apellido_paterno: Mapped[str] = mapped_column(String(256))
    apellido_materno: Mapped[str] = mapped_column(String(256))
    apodo: Mapped[str] = mapped_column(String(256))
    sexo = mapped_column(Enum(*SEXOS, name="pen_inculpados_sexos", native_enum=False))
    estado: Mapped[str] = mapped_column(String(256))
    solicitud_mp: Mapped[str] = mapped_column(String(256))

    @property
    def nombre(self):
        """Nombre completo"""
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"

    def __repr__(self):
        """Representación"""
        return f"<PenInculpado {self.id}>"
