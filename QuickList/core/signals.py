from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Usuario, Alumno, Profesor, Administrador

# Alumno y Usuario
@receiver(post_save, sender=Alumno)
def sync_user_with_alumno(sender, instance, created, **kwargs):
    if created:  # Si se crea un alumno
        Usuario.objects.create(
            correo=instance.correo,
            contrasenia=instance.contrasenia,
            estado=instance.estado,
            rango='Alumno'
        )
    else:  # Si se actualiza
        try:
            user = Usuario.objects.get(correo=instance.correo)
            user.contrasenia = instance.contrasenia
            user.estado = instance.estado
            user.save()
        except Usuario.DoesNotExist:
            pass

@receiver(pre_delete, sender=Alumno)
def delete_user_with_alumno(sender, instance, **kwargs):
    try:
        Usuario.objects.get(correo=instance.correo).delete()
    except Usuario.DoesNotExist:
        pass

# Profesor y Usuario
@receiver(post_save, sender=Profesor)
def sync_user_with_profesor(sender, instance, created, **kwargs):
    if created:
        Usuario.objects.create(
            correo=instance.correo,
            contrasenia=instance.contrasenia,
            estado=instance.estado,
            rango='Profesor'
        )
    else:
        try:
            user = Usuario.objects.get(correo=instance.correo)
            user.contrasenia = instance.contrasenia
            user.estado = instance.estado
            user.save()
        except Usuario.DoesNotExist:
            pass

@receiver(pre_delete, sender=Profesor)
def delete_user_with_profesor(sender, instance, **kwargs):
    try:
        Usuario.objects.get(correo=instance.correo).delete()
    except Usuario.DoesNotExist:
        pass

# Administrador y Usuario
@receiver(post_save, sender=Administrador)
def sync_user_with_administrador(sender, instance, created, **kwargs):
    if created:
        Usuario.objects.create(
            correo=instance.correo,
            contrasenia=instance.contrasenia,
            estado=instance.estado,
            rango='Administrador'
        )
    else:
        try:
            user = Usuario.objects.get(correo=instance.correo)
            user.contrasenia = instance.contrasenia
            user.estado = instance.estado
            user.save()
        except Usuario.DoesNotExist:
            pass

@receiver(pre_delete, sender=Administrador)
def delete_user_with_administrador(sender, instance, **kwargs):
    try:
        Usuario.objects.get(correo=instance.correo).delete()
    except Usuario.DoesNotExist:
        pass


from .models import Carrera, Materia, Alumno

@receiver(pre_delete, sender=Carrera)
def delete_related_with_carrera(sender, instance, **kwargs):
    # Eliminar todas las materias relacionadas
    Materia.objects.filter(carrera=instance).delete()
    # Actualizar los alumnos para que no tengan carrera
    Alumno.objects.filter(carrera=instance).update(carrera=None)


from .models import Clase, ClaseAlumno

@receiver(pre_delete, sender=Clase)
def delete_related_with_clase(sender, instance, **kwargs):
    # Eliminar todas las relaciones ClaseAlumno asociadas a la Clase
    ClaseAlumno.objects.filter(clase=instance).delete()

from .models import ListaAsistencia, AlumnoLista

@receiver(pre_delete, sender=ListaAsistencia)
def delete_related_with_lista_asistencia(sender, instance, **kwargs):
    # Eliminar todas las entradas AlumnoLista relacionadas con la ListaAsistencia
    AlumnoLista.objects.filter(lista_asistencia=instance).delete()

from .models import ClaseAlumno, AlumnoLista

@receiver(pre_delete, sender=ClaseAlumno)
def delete_related_with_clase_alumno(sender, instance, **kwargs):
    # Eliminar todas las relaciones AlumnoLista asociadas al alumno de esta clase
    AlumnoLista.objects.filter(alumno=instance.alumno, clase=instance.clase).delete()

@receiver(post_save, sender=Alumno)
def update_graduated_count(sender, instance, **kwargs):
    if instance.estado == 'Egresado':
        carrera = instance.carrera
        carrera.egresados += 1
        carrera.save()

from django.db.models import Avg

@receiver(post_save, sender=AlumnoLista)
def update_lista_asistencia_average(sender, instance, **kwargs):
    lista = instance.lista
    promedio = AlumnoLista.objects.filter(lista=lista).aggregate(Avg('calificacion'))['calificacion__avg']
    lista.promedio = promedio
    lista.save()

from .models import Justificante

@receiver(pre_delete, sender=Alumno)
def delete_justificante_with_alumno(sender, instance, **kwargs):
    # Eliminar justificantes relacionados con el Alumno
    Justificante.objects.filter(alumno=instance).delete()

@receiver(pre_delete, sender=Profesor)
def delete_justificante_with_profesor(sender, instance, **kwargs):
    # Eliminar justificantes relacionados con el Profesor
    Justificante.objects.filter(profesor=instance).delete()

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Alumno, Retroalimentacion

@receiver(pre_delete, sender=Alumno)
def delete_retroalimentacion_with_alumno(sender, instance, **kwargs):
    Retroalimentacion.objects.filter(alumno=instance).delete()

@receiver(post_save, sender=Alumno)
def update_retroalimentacion_with_alumno(sender, instance, **kwargs):
    retroalimentaciones = Retroalimentacion.objects.filter(alumno=instance)
    for retroalimentacion in retroalimentaciones:
        retroalimentacion.alumno = instance
        retroalimentacion.save()
