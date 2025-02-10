"""
Penales Expedientes, formularios
"""

from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class PenExpedienteForm(FlaskForm):
    """Formulario PenExpediente"""

    expediente = StringField("Clave", validators=[DataRequired(), Length(max=24)])
    fecha = DateField("Fecha", validators=[DataRequired()])
    delitos = StringField("Delitos", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")
