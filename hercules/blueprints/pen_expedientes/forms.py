"""
Penales Expedientes, formularios
"""

from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from hercules.blueprints.pen_agentes_mp.models import PenAgenteMP
from hercules.blueprints.pen_jueces.models import PenJuez
from hercules.blueprints.pen_secretarios.models import PenSecretario


class PenExpedienteForm(FlaskForm):
    """Formulario PenExpediente"""

    expediente = StringField("Expediente", validators=[DataRequired(), Length(max=24)])
    fecha = DateField("Fecha", validators=[DataRequired()])
    autoridad = SelectField("Autoridad", choices=None, validators=[DataRequired()], validate_choice=False)
    pen_juez = SelectField("Juez", choices=None, validators=[DataRequired()], validate_choice=False)
    pen_secretario = SelectField("Secretario", choices=None, validators=[DataRequired()], validate_choice=False)
    pen_agente_mp = SelectField("Agente M.P.", choices=None, validators=[DataRequired()], validate_choice=False)
    delitos = StringField("Delitos", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")
