"""
Penales Inculpados, formularios
"""

from flask_wtf import FlaskForm
from wtforms import RadioField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from hercules.blueprints.pen_inculpados.models import PenInculpado


class PenInculpadoForm(FlaskForm):
    """Formulario PenInculpados"""

    nombres = StringField("Nombres", validators=[DataRequired(), Length(max=256)])
    apellido_paterno = StringField("Apellido paterno", validators=[DataRequired(), Length(max=256)])
    apellido_materno = StringField("Apellido materno", validators=[Optional(), Length(max=256)])
    apodo = StringField("Apodo", validators=[Optional(), Length(max=256)])
    sexo = RadioField("Sexo", choices=PenInculpado.SEXOS.items(), validators=[DataRequired()])
    estado = StringField("Status", validators=[Optional(), Length(max=256)])
    solicitud_mp = StringField("Solicitud M.P.", validators=[Optional(), Length(max=256)])
    guardar = SubmitField("Guardar")
