"""
Penales Expedientes, modelos
"""

from datetime import date
from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hercules.extensions import database
from lib.universal_mixin import UniversalMixin


class PenExpediente(database.Model, UniversalMixin):
    """PenExpediente"""

    # Nombre de la tabla
    __tablename__ = "pen_expedientes"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    autoridad_id: Mapped[int] = mapped_column(ForeignKey("autoridades.id"))
    autoridad: Mapped["Autoridad"] = relationship(back_populates="pen_expedientes")
    pen_agente_mp_id: Mapped[int] = mapped_column(ForeignKey("pen_agentes_mp.id"))
    pen_agente_mp: Mapped["PenAgenteMP"] = relationship(back_populates="pen_expedientes")
    pen_juez_id: Mapped[int] = mapped_column(ForeignKey("pen_jueces.id"))
    pen_juez: Mapped["PenJuez"] = relationship(back_populates="pen_expedientes")
    pen_secretario_id: Mapped[int] = mapped_column(ForeignKey("pen_secretarios.id"))
    pen_secretario: Mapped["PenSecretario"] = relationship(back_populates="pen_expedientes")

    # Columnas
    expediente: Mapped[str] = mapped_column(String(24), unique=True)
    fecha: Mapped[date]
    secretario: Mapped[str] = mapped_column(String(256))
    delitos: Mapped[str] = mapped_column(String(256))

    # Hijos
    pen_inculpados: Mapped[List["PenInculpado"]] = relationship(back_populates="pen_expediente")

    def __repr__(self):
        """Representación"""
        return f"<PenExpediente {self.id}>"
