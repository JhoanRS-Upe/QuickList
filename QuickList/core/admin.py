from django.contrib import admin
from .models import Carrera, Academia, Alumno, Profesor, Administrador, Periodo, Materia, Clase, ListaAsistencia, Justificante, ClaseAlumno, AlumnoLista, Usuario, Retroalimentacion

admin.site.register(Carrera)
admin.site.register(Academia)
admin.site.register(Alumno)
admin.site.register(Profesor)
admin.site.register(Administrador)
admin.site.register(Periodo)
admin.site.register(Materia)
admin.site.register(Clase)
admin.site.register(ListaAsistencia)
admin.site.register(Justificante)
admin.site.register(ClaseAlumno)
admin.site.register(AlumnoLista)
admin.site.register(Usuario)
admin.site.register(Retroalimentacion)