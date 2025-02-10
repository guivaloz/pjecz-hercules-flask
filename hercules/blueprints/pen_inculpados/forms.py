"""
Penales Inculpados, formularios
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from hercules.blueprints.pen_inculpados.models import PenInculpado


class PenInculpadosForm(FlaskForm):
    """Formulario PenInculpados"""

    nombres = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    apellido_paterno = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    apellido_materno = StringField("Descripción", validators=[Optional(), Length(max=256)])
    apodo = StringField("Descripción", validators=[Optional(), Length(max=256)])
    sexo = SelectField("Sexo", choices=PenInculpado.items(), validators=[DataRequired()])
    estado = StringField("Status", validators=[Optional(), Length(max=256)])
    solicitud_mp = StringField("Solicitud M.P.", validators=[Optional(), Length(max=256)])
    guardar = SubmitField("Guardar")
