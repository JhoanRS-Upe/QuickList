from django.db import models 
from django.db.models.signals import post_save 
from django.dispatch import receiver 
from django.contrib.auth.hashers import make_password
import os
from django.utils.deconstruct import deconstructible
from django.utils import timezone

@deconstructible
class PathAndRename:
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        # Extraer la extensión del archivo
        ext = filename.split('.')[-1]
        # Construir el nombre del archivo con la matrícula del alumno
        filename = f'{instance.alumno.matricula}.{ext}'
        # Devolver la ruta completa
        return os.path.join(self.path, instance.alumno.matricula, filename)

# Crear una instancia de la clase con la ruta base
upload_to = PathAndRename('alumnos_fotos/')  # Ruta base para las fotos de los alumnos

class Usuario(models.Model):
    correo = models.EmailField(max_length=100, primary_key=True)
    contrasenia = models.CharField(max_length=128)  # Almacenar como hash
    estado = models.BooleanField(default=False)
    RANGO_CHOICES = [
        ('Alumno', 'Alumno'),
        ('Profesor', 'Profesor'),
        ('Administrador', 'Administrador'),
    ]
    rango = models.CharField(max_length=15, choices=RANGO_CHOICES)
    
    def __str__(self):
        return self.correo

# Modelo Carrera
class Carrera(models.Model):
    id = models.AutoField(primary_key=True)  # AutoIncrement equivalente al id en SQL
    nombre = models.CharField(max_length=50)
    cuatrimestres = models.PositiveIntegerField()
    alumnosEgre = models.PositiveIntegerField()  # Número de egresados

    def __str__(self):
        return self.nombre


# Modelo Academia
class Academia(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

# Modelo Alumno
class Alumno(models.Model):
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    RANGO_CHOICES = [
        ('Alumno', 'Alumno'),
    ]

    matricula = models.CharField(max_length=20, primary_key=True)
    nombres = models.CharField(max_length=30)
    apellidoP = models.CharField(max_length=20)
    apellidoM = models.CharField(max_length=20)
    fechaNac = models.DateField()
    genero = models.CharField(max_length=2, choices=GENERO_CHOICES)
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE)
    correo = models.EmailField(max_length=100)
    contrasenia = models.CharField(max_length=128)  # Más seguro para almacenar hashes
    estado = models.BooleanField(default=False)
    rango = models.CharField(max_length=30, choices=RANGO_CHOICES)
    cbiometrico = models.CharField(max_length=100)  # Clave biométrica
    foto = models.ImageField(upload_to=upload_to, null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidoP} {self.apellidoM}"

class Foto(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to=upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto de {self.alumno.nombres} subida el {self.fecha_subida}"

# Modelo Profesor
class Profesor(models.Model):
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    RANGO_CHOICES = [
        ('Profesor', 'Profesor'),
    ]

    clave = models.CharField(max_length=20, primary_key=True)
    nombres = models.CharField(max_length=30)
    apellidoP = models.CharField(max_length=20)
    apellidoM = models.CharField(max_length=20)
    fechaNac = models.DateField()
    genero = models.CharField(max_length=2, choices=GENERO_CHOICES)
    grado = models.CharField(max_length=10)  # Grado académico
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE)
    correo = models.EmailField(max_length=100)
    contrasenia = models.CharField(max_length=128)  # Más seguro para almacenar hashes
    estado = models.BooleanField(default=False)
    rango = models.CharField(max_length=20, choices=RANGO_CHOICES)

    def __str__(self):
        return f"{self.nombres} {self.apellidoP} {self.apellidoM}"

# Modelo Administrador
class Administrador(models.Model):
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    RANGO_CHOICES = [
        ('Administrador', 'Administrador'),
    ]

    claveA = models.CharField(max_length=20, primary_key=True)
    nombres = models.CharField(max_length=30)
    apellidoP = models.CharField(max_length=20)
    apellidoM = models.CharField(max_length=20)
    fechaNac = models.DateField()
    estado = models.BooleanField()
    genero = models.CharField(max_length=2, choices=GENERO_CHOICES)
    correo = models.EmailField(max_length=100)
    contrasenia = models.CharField(max_length=128)  # Más seguro
    rango = models.CharField(max_length=20, choices=RANGO_CHOICES)

    def __str__(self):
        return f"{self.nombres} {self.apellidoP} {self.apellidoM}"

# Modelo Periodo
class Periodo(models.Model):
    idPeriodo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30)
    inicial = models.CharField(max_length=1)  # Inicial del periodo (A, B, etc.)
    anio = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre


# Modelo Materia
class Materia(models.Model):
    clave = models.CharField(max_length=20, primary_key=True)
    nombre = models.CharField(max_length=30)
    creditos = models.PositiveIntegerField()
    eje = models.CharField(max_length=30)
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


# Modelo Clase
class Clase(models.Model):
    codigo = models.CharField(max_length=20, primary_key=True)
    grado = models.PositiveIntegerField()
    grupo = models.CharField(max_length=1)
    anio = models.PositiveIntegerField()
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)

    def __str__(self):
        return self.codigo


# Modelo Lista de Asistencia
class ListaAsistencia(models.Model):
    idLista = models.AutoField(primary_key=True)
    fecha = models.DateField()
    promedio = models.FloatField()
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)

    def __str__(self):
        return f"Lista {self.idLista} - {self.fecha}"


# Modelo Justificante
class Justificante(models.Model):
    idJustificante = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255)
    estado = models.CharField(max_length=20)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)

    def __str__(self):
        return f"Justificante {self.idJustificante} - {self.estado}"


# Modelo ClaseAlumno
class ClaseAlumno(models.Model):
    idcAlumno = models.AutoField(primary_key=True)
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)

    def __str__(self):
        return f"Clase {self.clase.codigo} - Alumno {self.alumno.matricula}"


# Modelo AlumnoLista
class AlumnoLista(models.Model):
    lista = models.ForeignKey(ListaAsistencia, on_delete=models.CASCADE)
    clase_alumno = models.ForeignKey(ClaseAlumno, on_delete=models.CASCADE)
    calificacion = models.CharField(max_length=1)

    class Meta:
        unique_together = ('lista', 'clase_alumno')

    def __str__(self):
        return f"Lista {self.lista.idLista} - ClaseAlumno {self.clase_alumno.idcAlumno}"


class Retroalimentacion(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    descripcion = models.TextField()
    calificacion = models.IntegerField()
    fecha_reporte = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Retroalimentación de {self.alumno.nombres} {self.alumno.apellidoP} {self.alumno.apellidoM} - {self.fecha_reporte}"