"""
Penales Agentes MP, modelos
"""

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hercules.extensions import database
from lib.universal_mixin import UniversalMixin


class PenAgenteMP(database.Model, UniversalMixin):
    """PenAgenteMP"""

    # Nombre de la tabla
    __tablename__ = "pen_agentes_mp"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    nombre: Mapped[str] = mapped_column(String(256))

    # Hijos
    pen_expedientes: Mapped[List["PenExpediente"]] = relationship(back_populates="pen_agente_mp")

    def __repr__(self):
        """Representación"""
        return f"<PenAgenteMP {self.id}>"
