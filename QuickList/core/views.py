from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Alumno, Profesor, Carrera, Academia, Administrador, Clase, ClaseAlumno, Periodo, Materia, Clase, Justificante, AlumnoLista, Foto, ListaAsistencia
from django.db import connection
from django.http import Http404
from django.db import transaction
from django.db.models import Q
from django.db.utils import DatabaseError
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from core.models import ClaseAlumno
import face_recognition
import cv2
import numpy as np
from django.utils import timezone
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import base64
from PIL import Image
from io import BytesIO
from django.db.models import Avg, Count
from django.core.files.storage import FileSystemStorage
import os
import subprocess
import mysql.connector
from mysql.connector import Error
from django.core.management import call_command
from io import StringIO
from django.db import IntegrityError
from .models import Alumno, Retroalimentacion
from .forms import RetroalimentacionForm

# Vista de inicio de sesión
def login_view(request):
    if request.method == "POST":
        # Capturamos los datos enviados desde el formulario
        correo = request.POST.get("correo", "").strip()
        contrasenia = request.POST.get("contrasenia", "").strip()

        # Validar que los campos no estén vacíos
        if not correo or not contrasenia:
            return render(request, "core/login.html", {"error": "Todos los campos son obligatorios"})

        # Consulta a la base de datos para buscar al usuario por correo
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT correo, contrasenia, estado, rango
                FROM core_usuario
                WHERE correo = %s
                """,
                [correo],
            )
            user = cursor.fetchone()

        # Verificar si el usuario existe
        if user is None:
            return render(request, "core/login.html", {"error": "Correo no registrado"})

        # Desempaquetamos los valores obtenidos de la consulta
        user_correo, user_password, user_estado, user_rango = user

        # Validar la contraseña
        if contrasenia != user_password:
            return render(request, "core/login.html", {"error": "Contraseña incorrecta"})

        # Validar el estado del usuario
        if user_estado != 1:
            return render(request, "core/login.html", {"error": "El usuario está inhabilitado. Contacta al administrador."})

        # Si pasa todas las validaciones, guardar los datos en la sesión
        request.session["correo"] = user_correo
        request.session["rango"] = user_rango

        # Redirigir según el rol del usuario
        if user_rango == "Administrador":
            return redirect("administrativo_dashboard")
        elif user_rango == "Profesor":
            return redirect("profesor_dashboard")
        elif user_rango == "Alumno":
            return redirect("alumno_dashboard")
        else:
            return render(request, "core/login.html", {"error": "Rol de usuario no válido. Contacta al administrador."})

    # Si el método no es POST, renderizar el formulario vacío
    return render(request, "core/login.html")

# Vista para cerrar sesión
def logout_view(request):
    # Eliminar todos los datos de la sesión
    request.session.flush()  # Vacía completamente la sesión del usuario
    return redirect('login')  # Redirige al usuario a la página de inicio de sesión

# Registro de alumno del inicio de sesion
def registro_alumno(request):
    if request.method == 'POST':
        matricula = request.POST['matricula']
        nombres = request.POST['nombres']
        apellidoP = request.POST['apellidoP']
        apellidoM = request.POST['apellidoM']
        fechaNac = request.POST['fechaNac']
        genero = request.POST['genero']
        carrera_id = request.POST['carrera']
        correo = request.POST['correo']
        contrasenia = request.POST['contrasenia']
        confirmPassword = request.POST['confirmPassword']
        
        if Alumno.objects.filter(matricula=matricula).exists():
            messages.error(request, 'La matrícula ya está registrada.')
            carreras = Carrera.objects.all()
            academias = Academia.objects.all()
            context = {'carreras': carreras, 'academias': academias}
            return render(request, 'core/AlumnoR.html', context)

        if Alumno.objects.filter(correo=correo).exists():
            messages.error(request, 'El correo ya esta registrado.')
            carreras = Carrera.objects.all()
            academias = Academia.objects.all()
            context = {'carreras': carreras, 'academias': academias}
            return render(request, 'core/AlumnoR.html', context)

        carrera = Carrera.objects.get(id=carrera_id)
        Alumno.objects.create(
            matricula=matricula,
            nombres=nombres,
            apellidoP=apellidoP,
            apellidoM=apellidoM,
            fechaNac=fechaNac,
            genero=genero,
            carrera=carrera,
            correo=correo,
            contrasenia=contrasenia,  # Guardar en texto plano
            estado=False,  # Inhabilitado por defecto
            rango='Alumno',
            cbiometrico=''  # O cualquier valor necesario
        )
        messages.success(request, 'Registro de alumno exitoso. Ahora puedes iniciar sesión.')
        return redirect('login')
    else:
        carreras = Carrera.objects.all()
        academias = Academia.objects.all()
        context = {'carreras': carreras, 'academias': academias}
        return render(request, 'core/AlumnoR.html', context)

# Registro de profesor del inicio de sesion
def registro_profesor(request):
    if request.method == 'POST':
        clave = request.POST['clave']
        nombres = request.POST['nombres']
        apellidoP = request.POST['apellidoP']
        apellidoM = request.POST['apellidoM']
        fechaNac = request.POST['fechaNac']
        genero = request.POST['genero']
        grado = request.POST['grado']
        academia_id = request.POST['academia']
        correo = request.POST['correo']
        contrasenia = request.POST['contrasenia']
        confirmPassword = request.POST['confirmPassword']

        if Profesor.objects.filter(clave=clave).exists():
            messages.error(request, 'La clave ya está registrada.')
            carreras = Carrera.objects.all()
            academias = Academia.objects.all()
            context = {'carreras': carreras, 'academias': academias}
            return render(request, 'core/ProfesorR.html', context)

        if Profesor.objects.filter(correo=correo).exists():
            messages.error(request, 'El correo ya esta registrado.')
            carreras = Carrera.objects.all()
            academias = Academia.objects.all()
            context = {'carreras': carreras, 'academias': academias}
            return render(request, 'core/ProfesorR.html', context)

        academia = Academia.objects.get(id=academia_id)
        Profesor.objects.create(
            clave=clave,
            nombres=nombres,
            apellidoP=apellidoP,
            apellidoM=apellidoM,
            fechaNac=fechaNac,
            genero=genero,
            grado=grado,
            academia=academia,
            correo=correo,
            contrasenia=contrasenia,  # Guardar en texto plano
            estado=False,  # Inhabilitado por defecto
            rango='Profesor'
        )
        messages.success(request, 'Registro de profesor exitoso. Ahora puedes iniciar sesión.')
        return redirect('login')
    else:
        carreras = Carrera.objects.all()
        academias = Academia.objects.all()
        context = {'carreras': carreras, 'academias': academias}
        return render(request, 'core/ProfesorR.html', context)

# Dashboards
def administrativo_dashboard(request):
    return render(request, 'core/administrativo_dashboard.html')

def alumno_dashboard(request):
    return render(request, 'core/alumno_dashboard.html')

def profesor_dashboard(request):
    return render(request, 'core/profesor_dashboard.html')

def usuarios_registro(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')  # Obtenemos el tipo de usuario desde el POST
        if user_type == 'administrador':
            claveA = request.POST['administrador_claveA']
            nombres = request.POST['administrador_nombres']
            apellidoP = request.POST['administrador_apellidoP']
            apellidoM = request.POST['administrador_apellidoM']
            fechaNac = request.POST['administrador_fechaNac']
            genero = request.POST['administrador_genero']
            correo = request.POST['administrador_correo']
            contrasenia = request.POST['administrador_contrasenia']
            estado = request.POST['administrador_estado']
            
            # Verificación de clave administrativa y correo
            if Administrador.objects.filter(claveA=claveA).exists():
                messages.error(request, 'La clave administrativa ya está registrada.')
                return render(request, 'core/usuarios_registro.html')

            if Administrador.objects.filter(correo=correo).exists():
                messages.error(request, 'El correo ya está registrado.')
                return render(request, 'core/usuarios_registro.html')

            # Crear el Administrador
            Administrador.objects.create(
                claveA=claveA,
                nombres=nombres,
                apellidoP=apellidoP,
                apellidoM=apellidoM,
                fechaNac=fechaNac,
                genero=genero,
                correo=correo,
                contrasenia=contrasenia,  # Guardar en texto plano
                estado=estado,
                rango='Administrador'
            )
            print("Administrador registrado correctamente")
            print("Creando administrador:", claveA, nombres)
            messages.success(request, 'Administrador registrado exitosamente.')
        
        elif user_type == 'profesor':
            clave = request.POST['profesor_clave']
            nombres = request.POST['profesor_nombres']
            apellidoP = request.POST['profesor_apellidoP']
            apellidoM = request.POST['profesor_apellidoM']
            fechaNac = request.POST['profesor_fechaNac']
            genero = request.POST['profesor_genero']
            grado = request.POST['profesor_grado']
            academia_id = request.POST['profesor_academia']
            correo = request.POST['profesor_correo']
            contrasenia = request.POST['profesor_contrasenia']
            estado = request.POST['profesor_estado']

            # Verificación de clave y correo del profesor
            if Profesor.objects.filter(clave=clave).exists():
                messages.error(request, 'La clave de profesor ya está registrada.')
                return render(request, 'core/usuarios_registro.html')

            if Profesor.objects.filter(correo=correo).exists():
                messages.error(request, 'El correo ya está registrado.')
                return render(request, 'core/usuarios_registro.html')

            academia = Academia.objects.get(id=academia_id)

            # Crear el Profesor
            Profesor.objects.create(
                clave=clave,
                nombres=nombres,
                apellidoP=apellidoP,
                apellidoM=apellidoM,
                fechaNac=fechaNac,
                genero=genero,
                grado=grado,
                academia=academia,
                correo=correo,
                contrasenia=contrasenia,  # Guardar en texto plano
                estado=estado,  # Inhabilitado por defecto
                rango='Profesor',  # El rango sería 'Profesor'
            )
            messages.success(request, 'Profesor registrado exitosamente.')

        elif user_type == 'alumno':
            matricula = request.POST['alumno_matricula']
            nombres = request.POST['alumno_nombres']
            apellidoP = request.POST['alumno_apellidoP']
            apellidoM = request.POST['alumno_apellidoM']
            fechaNac = request.POST['alumno_fechaNac']
            genero = request.POST['alumno_genero']
            carrera_id = request.POST['alumno_carrera']
            correo = request.POST['alumno_correo']
            contrasenia = request.POST['alumno_contrasenia']
            estado = request.POST['alumno_estado']

            # Verificación de matrícula y correo del alumno
            if Alumno.objects.filter(matricula=matricula).exists():
                messages.error(request, 'La matrícula ya está registrada.')
                return render(request, 'core/usuarios_registro.html')

            if Alumno.objects.filter(correo=correo).exists():
                messages.error(request, 'El correo ya está registrado.')
                return render(request, 'core/usuarios_registro.html')

            carrera = Carrera.objects.get(id=carrera_id)

            # Crear el Alumno
            Alumno.objects.create(
                matricula=matricula,
                nombres=nombres,
                apellidoP=apellidoP,
                apellidoM=apellidoM,
                fechaNac=fechaNac,
                genero=genero,
                carrera=carrera,
                correo=correo,
                contrasenia=contrasenia,  # Guardar en texto plano
                estado=estado,  # Inhabilitado por defecto
                rango='Alumno',  # El rango sería 'Alumno'
                cbiometrico=''  # O cualquier valor necesario
            )
            messages.success(request, 'Alumno registrado exitosamente.')

        return redirect('usuarios_registro')

    else:
        carreras = Carrera.objects.all()
        academias = Academia.objects.all()
        context = {'carreras': carreras, 'academias': academias}
        return render(request, 'core/usuarios_registro.html', context)

def usuarios_consulta(request):
    tipo_usuario = request.GET.get('tipo_usuario')
    busqueda = request.GET.get('busqueda')
    estado = request.GET.get('estado')
    academia_id = request.GET.get('academia')
    carrera_id = request.GET.get('carrera')
    grupo_id = request.GET.get('grupo')

    filtros = {
        'tipo_usuario': request.GET.get('tipo_usuario', ''),
        'busqueda': request.GET.get('busqueda', ''),
        'estado': request.GET.get('estado', ''),
        'carrera': request.GET.get('carrera', ''),
        'grupo': request.GET.get('grupo', ''),
    }

    # Lógica para decidir si mostrar la tabla de administradores
    mostrar_tabla_admin = filtros['tipo_usuario'] == "administrador"
    mostrar_tabla_profesor = filtros['tipo_usuario'] == "profesor"
    mostrar_tabla_alumno = filtros['tipo_usuario'] == "alumno"
    
    # Inicializar una lista vacía para los resultados
    resultados = []

    # Filtrar administradores
    if tipo_usuario == "administrador":
        # Filtrar administradores según los parámetros proporcionados
        query = Administrador.objects.all()

        if busqueda:
            query = query.filter(claveA__icontains=busqueda) | query.filter(correo__icontains=busqueda)
        
        if estado:
            query = query.filter(estado=estado)
        
        # Asignar los resultados filtrados
        resultados = query

    # Filtrar profesores
    elif tipo_usuario == "profesor":
        # Filtrar profesores según los parámetros proporcionados
        query = Profesor.objects.all()

        if busqueda:
            query = query.filter(clave__icontains=busqueda) | query.filter(correo__icontains=busqueda)
        
        if estado:
            query = query.filter(estado=estado)
        
        if academia_id:
            query = query.filter(academia_id=academia_id)

        # Asignar los resultados filtrados
        resultados = query

    # Filtrar alumnos
    elif tipo_usuario == "alumno":
        # Filtrar alumnos según los parámetros proporcionados
        query = Alumno.objects.all()

        if busqueda:
            query = query.filter(matricula__icontains=busqueda) | query.filter(correo__icontains=busqueda)
        
        if estado:
            query = query.filter(estado=estado)
        
        if carrera_id:
            query = query.filter(carrera_id=carrera_id)
        
        if grupo_id:
            query = query.filter(clasealumno__clase_id=grupo_id)
        
        # Asignar los resultados filtrados
        resultados = query

    # Cargar las opciones de academia, carrera y clase para los filtros
    academias = Academia.objects.all()
    carreras = Carrera.objects.all()
    clases = Clase.objects.all()

    context = {
        'filtros': filtros,
        'resultados': resultados,
        'mostrar_tabla_admin': mostrar_tabla_admin,
        'mostrar_tabla_profesor': mostrar_tabla_profesor,
        'mostrar_tabla_alumno': mostrar_tabla_alumno,
    }
    return render(request, 'core/usuarios_consulta.html', context)

# Funciones auxiliares para las consultas individuales
def consulta_alumnos(filtros):
    query = Alumno.objects.all()
    if filtros['busqueda']:
        query = query.filter(Q(matricula__icontains=filtros['busqueda']) | Q(correo__icontains=filtros['busqueda']))
    if filtros['estado'] is not None:
        query = query.filter(estado=(filtros['estado'] == 'habilitado'))
    if filtros['carrera_id'] is not None:
        query = query.filter(carrera__id=filtros['carrera_id'])
    if filtros['grupo']:  # Aplicar el filtro de grupo
        query = query.filter(clasealumno__clase__codigo=filtros['grupo'])
    return query

def consulta_profesores(filtros):
    query = Profesor.objects.all()
    if filtros['busqueda']:
        query = query.filter(Q(clave__icontains=filtros['busqueda']) | Q(correo__icontains=filtros['busqueda']))
    if filtros['estado'] is not None:
        query = query.filter(estado=(filtros['estado'] == 'habilitado'))
    if filtros['academia_id'] is not None:
        query = query.filter(academia__id=filtros['academia_id'])
    return query

def consulta_administradores(filtros):
    query = Administrador.objects.all()
    if filtros['busqueda']:
        query = query.filter(Q(claveA__icontains=filtros['busqueda']) | Q(correo__icontains=filtros['busqueda']))
    if filtros['estado'] is not None:
        query = query.filter(estado=(filtros['estado'] == 'habilitado'))
    return query

def modificar_administrador(request, claveA):
    # Obtener el registro del administrador
    administrador = get_object_or_404(Administrador, claveA=claveA)

    if request.method == 'POST':
        # Actualizar los datos con los valores enviados
        administrador.nombres = request.POST.get('nombres')
        administrador.apellidoP = request.POST.get('apellidoP')
        administrador.apellidoM = request.POST.get('apellidoM')
        administrador.genero = request.POST.get('genero')
        administrador.correo = request.POST.get('correo')
        administrador.estado = bool(request.POST.get('estado'))
        try:
            administrador.save()
            messages.success(request, "El administrador fue modificado exitosamente.")
            return redirect('usuarios_consulta')  # Regresa a la tabla de consulta
        except Exception as e:
            messages.error(request, f"Error al modificar el administrador: {e}")

    # Renderiza la página de modificación con los datos actuales del administrador
    return render(request, 'core/usuarios_modificar.html', {'administrador': administrador})

def eliminar_administrador(request, claveA):
    administrador = get_object_or_404(Administrador, claveA=claveA)

    if request.method == 'POST':
        try:
            administrador.delete()
            messages.success(request, "El administrador fue eliminado exitosamente.")
            return redirect('usuarios_consulta')  # Regresa a la tabla de consulta
        except Exception as e:
            messages.error(request, f"Error al eliminar el administrador: {e}")

    # Renderiza la página de confirmación de eliminación
    return render(request, 'core/usuarios_eliminar.html', {'administrador': administrador})

def modificar_profesor(request, clave):
    # Obtener el registro del profesor
    profesor = get_object_or_404(Profesor, clave=clave)

    if request.method == 'POST':
        # Actualizar los datos con los valores enviados
        profesor.nombres = request.POST.get('nombres')
        profesor.apellidoP = request.POST.get('apellidoP')
        profesor.apellidoM = request.POST.get('apellidoM')
        profesor.genero = request.POST.get('genero')
        profesor.correo = request.POST.get('correo')
        profesor.estado = bool(request.POST.get('estado'))
        try:
            profesor.save()
            messages.success(request, "El profesor fue modificado exitosamente.")
            return redirect('usuarios_consulta')  # Regresa a la tabla de consulta
        except Exception as e:
            messages.error(request, f"Error al modificar el profesor: {e}")

    # Renderiza la página de modificación con los datos actuales del administrador
    return render(request, 'core/usuarios_modificarP.html', {'profesor': profesor})

def eliminar_profesor(request, clave):
    profesor = get_object_or_404(Profesor, clave=clave)

    if request.method == 'POST':
        try:
            profesor.delete()
            messages.success(request, "El profesor fue eliminado exitosamente.")
            return redirect('usuarios_consulta')
        except Exception as e:
            messages.error(request, f"Error al eliminar al profesor: {e}")

    return render(request, 'core/usuarios_eliminarP.html',{'profesor': profesor})

def modificar_alumno(request, matricula):
    alumno = get_object_or_404(Alumno, matricula=matricula)

    if request.method == 'POST':
        alumno.nombres = request.POST.get('nombres')
        alumno.apellidoP = request.POST.get('apeliidoP')
        alumno.apellidoM = request.POST.get('apellidoM')
        alumno.genero = request.POST.get('genero')
        alumno.correo = request.POST.get('correo')
        alumno.estado = bool(request.POST.get('estado'))
        try:
            alumno.save()
            messages.success(request, "El alumno fue modificado exitosamente.")
            return redirect('usuarios_consulta')  # Regresa a la tabla de consulta
        except Exception as e:
            messages.error(request, f"Error al modificar al alumno: {e}")

    # Renderiza la página de modificación con los datos actuales del administrador
    return render(request, 'core/usuarios_modificarA.html', {'alumno': alumno})

def eliminar_alumno(request, matricula):
    alumno = get_object_or_404(Alumno, matricula=matricula)

    if request.method == 'POST':
        try:
            alumno.delete()
            messages.success(request, "El alumno fue eliminado exitosamente.")
            return redirect('usuarios_consulta')
        except Exception as e:
            messages.error(request, f"Error al eliminar al alumno: {e}")

    return render(request, 'core/usuarios_eliminarA.html',{'alumno': alumno})

def grupos_registro(request):
    # Si el método es POST, significa que el formulario fue enviado
    if request.method == 'POST':
        # Obtén los datos del formulario
        codigo = request.POST.get('codigo')
        grado = request.POST.get('grado')
        grupo = request.POST.get('grupo')
        anio = request.POST.get('anio')
        profesor_id = request.POST.get('profesor')
        carrera_id = request.POST.get('carrera')
        periodo_id = request.POST.get('periodo')
        materia_id = request.POST.get('materia')

        # Verifica que los campos obligatorios no estén vacíos
        if not codigo or not grado or not grupo or not anio or not profesor_id or not carrera_id or not periodo_id or not materia_id:
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/grupos_registro.html', {
                'profesores': Profesor.objects.all(),
                'carreras': Carrera.objects.all(),
                'periodos': Periodo.objects.all(),
                'materias': Materia.objects.all()
            })

        try:
            # Crear el nuevo grupo
            profesor = Profesor.objects.get(clave=profesor_id)
            carrera = Carrera.objects.get(id=carrera_id)
            periodo = Periodo.objects.get(idPeriodo=periodo_id)
            materia = Materia.objects.get(clave=materia_id)

            nuevo_grupo = Clase(
                codigo=codigo,
                grado=grado,
                grupo=grupo,
                anio=anio,
                profesor=profesor,
                carrera=carrera,
                periodo=periodo,
                materia=materia
            )
            nuevo_grupo.save()
            messages.success(request, 'El grupo ha sido registrado exitosamente.')

            return redirect('grupos_registro')  # Redirige a la lista de grupos o cualquier otra página

        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')
            return render(request, 'core/grupos_registro.html', {
                'profesores': Profesor.objects.all(),
                'carreras': Carrera.objects.all(),
                'periodos': Periodo.objects.all(),
                'materias': Materia.objects.all()
            })

    # Si el método no es POST, simplemente muestra el formulario vacío
    else:
        return render(request, 'core/grupos_registro.html', {
            'profesores': Profesor.objects.all(),
            'carreras': Carrera.objects.all(),
            'periodos': Periodo.objects.all(),
            'materias': Materia.objects.all()
        })

def grupos_consulta(request):
    carrera_id = request.GET.get('carrera')
    materia_id = request.GET.get('materia')
    periodo_id = request.GET.get('periodo')
    profesor_id = request.GET.get('profesor')
    busqueda = request.GET.get('busqueda')

    filtros = {
        'carrera': carrera_id,
        'materia': materia_id,
        'periodo': periodo_id,
        'profesor': profesor_id,
        'busqueda': busqueda
    }

    # Filtrar clases según los parámetros proporcionados
    query = Clase.objects.all()

    if busqueda:
        query = query.filter(codigo__icontains=busqueda) | query.filter(materia__nombre__icontains=busqueda)

    if carrera_id:
        query = query.filter(carrera_id=carrera_id)

    if materia_id:
        query = query.filter(materia_id=materia_id)

    if periodo_id:
        query = query.filter(periodo_id=periodo_id)

    if profesor_id:
        query = query.filter(profesor_id=profesor_id)

    # Obtener los filtros para el formulario
    carreras = Carrera.objects.all()
    materias = Materia.objects.all()
    periodos = Periodo.objects.all()
    profesores = Profesor.objects.all()

    context = {
        'filtros': filtros,
        'resultados': query,
        'carreras': carreras,
        'materias': materias,
        'periodos': periodos,
        'profesores': profesores
    }

    return render(request, 'core/grupos_consulta.html', context)

def modificar_grupo(request, codigo):
    # Obtener el grupo
    grupo = get_object_or_404(Clase, codigo=codigo)
    profesores = Profesor.objects.all()
    carreras = Carrera.objects.all()
    periodos = Periodo.objects.all()
    materias = Materia.objects.all()

    if request.method == 'POST':
        # Actualizar los datos, sin cambiar llaves primarias
        grupo.grado = request.POST.get('grado')
        grupo.grupo = request.POST.get('grupo')
        grupo.anio = request.POST.get('anio')
        grupo.profesor = Profesor.objects.get(clave=request.POST.get('profesor'))
        grupo.carrera = Carrera.objects.get(id=request.POST.get('carrera'))
        grupo.periodo = Periodo.objects.get(idPeriodo=request.POST.get('periodo'))
        grupo.materia = Materia.objects.get(clave=request.POST.get('materia'))

        try:
            grupo.save()
            messages.success(request, "El grupo fue modificado exitosamente.")
            return redirect('grupos_consulta')  # Redirige a la página de consulta
        except Exception as e:
            messages.error(request, f"Error al modificar el grupo: {e}")

    return render(request, 'core/grupo_modificar.html', {
        'grupo': grupo,
        'profesores': profesores,
        'carreras': carreras,
        'periodos': periodos,
        'materias': materias
    })

def eliminar_grupo(request, codigo):
    grupo = get_object_or_404(Clase, codigo=codigo)

    if request.method == 'POST':
        try:
            grupo.delete()
            messages.success(request, "El grupo fue eliminado exitosamente.")
            return redirect('grupos_consulta')  # Regresa a la tabla de consulta
        except Exception as e:
            messages.error(request, f"Error al eliminar el grupo: {e}")

    # Renderiza la página de confirmación de eliminación
    return render(request, 'core/grupo_eliminar.html', {'grupo': grupo})

def academias_registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')

        # Verificar si el nombre de la academia ya existe
        if Academia.objects.filter(nombre=nombre).exists():
            messages.error(request, 'Ya existe una academia con ese nombre.')
            return render(request, 'core/academias_registro.html')

        if not nombre:
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/academias_registro.html')

        try:
            nueva_academia = Academia(
                nombre=nombre,
            )
            nueva_academia.save()
            messages.success(request, 'La academia ha sido registrada exitosamente.')

            return redirect('academias_registro')  # Redirige a la lista de academias o cualquier otra página

        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')
            return render(request, 'core/academias_registro.html')

    else:
        return render(request, 'core/academias_registro.html')

def academias_consulta(request):
    busqueda = request.GET.get('busqueda')
    filtros = {
        'busqueda': busqueda
    }
    
    # Filtrar academias solo si hay un valor de búsqueda
    if busqueda:
        query = Academia.objects.filter(nombre__icontains=busqueda)
    else:
        query = Academia.objects.all()  # Si no hay búsqueda, se muestran todas las academias

    context = {
        'filtros': filtros,
        'academias': query  # Cambié 'resultados' por 'academias' para que coincida con la plantilla
    }

    return render(request, 'core/academias_consulta.html', context)

def modificar_academia(request, id):
    academia = get_object_or_404(Academia, id=id)

    if request.method == 'POST':
        academia.nombre = request.POST.get('nombre')

        try:
            academia.save()
            messages.success(request, "La academia fue modificada exitosamente.")
            return redirect('academias_consulta')  # Redirige a la página de consulta
        except Exception as e:
            messages.error(request, f"Error al modificar la academia: {e}")

    return render(request, 'core/academias_modificar.html', {'academia': academia})

def eliminar_academia(request, id):
    academia = get_object_or_404(Academia, id=id)

    if request.method == 'POST':
        try:
            academia.delete()
            messages.success(request, "La academia fue eliminada exitosamente.")
            return redirect('academias_consulta')  # Regresa a la tabla de consulta
        except Exception as e:
            messages.error(request, f"Error al eliminar la academia: {e}")

    # Renderiza la página de confirmación de eliminación
    return render(request, 'core/academias_eliminar.html', {'academia': academia})

def carreras_registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        cuatrimestres = request.POST.get('cuatrimestres')
        alumnosEgre = request.POST.get('alumnosEgre')

        # Validación de campos
        if not nombre or not cuatrimestres or not alumnosEgre:
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/carreras_registro.html')

        # Verificar si la carrera ya existe
        if Carrera.objects.filter(nombre=nombre).exists():
            messages.error(request, 'Ya existe una carrera con ese nombre.')
            return render(request, 'core/carreras_registro.html')

        try:
            nueva_carrera = Carrera(
                nombre=nombre,
                cuatrimestres=cuatrimestres,
                alumnosEgre=alumnosEgre
            )
            nueva_carrera.save()
            messages.success(request, 'La carrera ha sido registrada exitosamente.')
            return redirect('carreras_registro')  # Redirige a la lista de carreras
        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')
            return render(request, 'core/carreras_registro.html')
    else:
        return render(request, 'core/carreras_registro.html')

def carreras_consulta(request):
    busqueda = request.GET.get('busqueda', '')
    carreras = Carrera.objects.all()

    if busqueda:
        carreras = carreras.filter(nombre__icontains=busqueda)  # Filtrado por nombre de carrera

    context = {
        'carreras': carreras
    }

    return render(request, 'core/carreras_consulta.html', context)

def modificar_carrera(request, id):
    carrera = get_object_or_404(Carrera, id=id)

    if request.method == 'POST':
        carrera.nombre = request.POST.get('nombre')
        carrera.cuatrimestres = request.POST.get('cuatrimestres')
        carrera.alumnosEgre = request.POST.get('alumnosEgre')

        try:
            carrera.save()
            messages.success(request, "La carrera fue modificada exitosamente.")
            return redirect('carreras_consulta')
        except Exception as e:
            messages.error(request, f"Error al modificar la carrera: {e}")

    return render(request, 'core/carreras_modificar.html', {'carrera': carrera})

def eliminar_carrera(request, id):
    carrera = get_object_or_404(Carrera, id=id)

    if request.method == 'POST':
        try:
            carrera.delete()
            messages.success(request, "La carrera fue eliminada exitosamente.")
            return redirect('carreras_consulta')
        except Exception as e:
            messages.error(request, f"Error al eliminar la carrera: {e}")

    return render(request, 'core/carreras_eliminar.html', {'carrera': carrera})

def justificantes_registro(request):
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        estado = request.POST.get('estado')
        alumno_id = request.POST.get('alumno')
        profesor_id = request.POST.get('profesor')

        # Verificar que los datos estén presentes
        if not descripcion or not estado:
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/justificantes_registro.html')

        try:
            # Asegurarse de que se esté recuperando el objeto correcto
            alumno = Alumno.objects.get(matricula=alumno_id)  # Usamos matricula para identificar al alumno
            profesor = Profesor.objects.get(clave=profesor_id)  # Usamos clave para identificar al profesor

            # Crear y guardar el justificante
            justificante = Justificante(
                descripcion=descripcion,
                estado=estado,
                alumno=alumno,
                profesor=profesor
            )
            justificante.save()

            messages.success(request, 'El justificante ha sido registrado exitosamente.')
            return redirect('justificantes_consulta')
        except Alumno.DoesNotExist:
            messages.error(request, 'No se encontró el alumno con esa matrícula.')
        except Profesor.DoesNotExist:
            messages.error(request, 'No se encontró el profesor con esa clave.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')

    # Obtener la lista de alumnos y profesores para el formulario
    alumnos = Alumno.objects.all()
    profesores = Profesor.objects.all()

    return render(request, 'core/justificantes_registro.html', {'alumnos': alumnos, 'profesores': profesores})

def justificantes_consulta(request):
    # Prefetch las clases relacionadas a través de ClaseAlumno
    clases_prefetch = Prefetch(
        'clasealumno_set',  # Relación inversa desde Alumno hacia ClaseAlumno
        queryset=ClaseAlumno.objects.select_related('clase')  # Prefetch las clases relacionadas
    )

    # Obtén los justificantes con los alumnos y las clases de los alumnos
    justificantes = Justificante.objects.select_related('alumno', 'profesor').prefetch_related(
        Prefetch('alumno__clasealumno_set', queryset=ClaseAlumno.objects.select_related('clase'))
    )

    # Filtrar si hay búsqueda
    busqueda = request.GET.get('busqueda', '')
    if busqueda:
        justificantes = justificantes.filter(descripcion__icontains=busqueda)

    return render(request, 'core/justificantes_consulta.html', {'justificantes': justificantes})

def modificar_justificante(request, idJustificante):
    justificante = get_object_or_404(Justificante, idJustificante=idJustificante)

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        estado = request.POST.get('estado')
        alumno_id = request.POST.get('alumno')
        profesor_id = request.POST.get('profesor')
        clase_id = request.POST.get('clase')  # Nuevo campo

        # Validar campos obligatorios
        if not descripcion or not estado or not alumno_id or not profesor_id or not clase_id:
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/justificantes_modificar.html', {
                'justificante': justificante,
                'alumnos': Alumno.objects.all(),
                'profesores': Profesor.objects.all(),
                'clases': justificante.alumno.clasealumno_set.select_related('clase').all()
            })

        try:
            alumno = Alumno.objects.get(matricula=alumno_id)
            profesor = Profesor.objects.get(clave=profesor_id)
            clase = Clase.objects.get(codigo=clase_id)

            # Validar que la clase pertenezca al alumno seleccionado
            if not ClaseAlumno.objects.filter(clase=clase, alumno=alumno).exists():
                messages.error(request, 'La clase seleccionada no pertenece al alumno.')
                return render(request, 'core/justificantes_modificar.html', {
                    'justificante': justificante,
                    'alumnos': Alumno.objects.all(),
                    'profesores': Profesor.objects.all(),
                    'clases': alumno.clasealumno_set.select_related('clase').all()
                })

            # Actualizar datos del justificante
            justificante.descripcion = descripcion
            justificante.estado = estado
            justificante.alumno = alumno
            justificante.profesor = profesor
            justificante.save()

            messages.success(request, 'El justificante ha sido modificado exitosamente.')
            return redirect('justificantes_consulta')

        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')

    # Prefetch las clases del alumno actual
    clases = justificante.alumno.clasealumno_set.select_related('clase').all()
    alumnos = Alumno.objects.all()
    profesores = Profesor.objects.all()

    return render(request, 'core/justificantes_modificar.html', {
        'justificante': justificante,
        'alumnos': alumnos,
        'profesores': profesores,
        'clases': clases
    })

def eliminar_justificante(request, idJustificante):
    justificante = Justificante.objects.get(idJustificante=idJustificante)
    if request.method == 'POST':
        try:
            justificante.delete()
            messages.success(request, 'El justificante ha sido eliminado.')
            return redirect('justificantes_consulta')
        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')
            return redirect('justificantes_consulta')

    return render(request, 'core/justificantes_eliminar.html', {'justificante': justificante})

# Registro de Materias
def materias_registro(request):
    if request.method == 'POST':
        clave = request.POST.get('clave')
        nombre = request.POST.get('nombre')
        creditos = request.POST.get('creditos')
        eje = request.POST.get('eje')
        carrera_id = request.POST.get('carrera')
        periodo_id = request.POST.get('periodo')

        # Verificar si todos los campos están completos
        if not (clave and nombre and creditos and eje):
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/materias_registro.html')

        # Verificar si la clave ya existe
        if Materia.objects.filter(clave=clave).exists():
            messages.error(request, 'Ya existe una materia con esa clave.')
            return render(request, 'core/materias_registro.html')

        try:
            carrera = Carrera.objects.get(id=carrera_id)
            periodo = Periodo.objects.get(idPeriodo=periodo_id)

            nueva_materia = Materia(
                clave=clave,
                nombre=nombre,
                creditos=creditos,
                eje=eje,
                carrera=carrera,
                periodo=periodo
            )
            nueva_materia.save()
            messages.success(request, 'La materia ha sido registrada exitosamente.')
            return redirect('materias_registro')
        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')

    # Obtener las carreras y periodos disponibles para mostrar en el formulario
    carreras = Carrera.objects.all()
    periodos = Periodo.objects.all()

    context = {
        'carreras': carreras,
        'periodos': periodos
    }

    return render(request, 'core/materias_registro.html', context)

# Consulta de Materias
def materias_consulta(request):
    # Filtros
    clave = request.GET.get('clave', None)
    nombre = request.GET.get('nombre', None)
    carrera_id = request.GET.get('carrera', None)
    periodo_id = request.GET.get('periodo', None)

    # Consulta base
    query = Materia.objects.all()

    # Aplicar filtros si existen
    if clave:
        query = query.filter(clave__icontains=clave)
    if nombre:
        query = query.filter(nombre__icontains=nombre)
    if carrera_id:
        query = query.filter(carrera_id=carrera_id)
    if periodo_id:
        query = query.filter(periodo_id=periodo_id)

    # Obtener carreras y periodos para filtros
    carreras = Carrera.objects.all()
    periodos = Periodo.objects.all()

    context = {
        'materias': query,
        'carreras': carreras,
        'periodos': periodos,
        'filtros': {
            'clave': clave,
            'nombre': nombre,
            'carrera': carrera_id,
            'periodo': periodo_id,
        }
    }

    return render(request, 'core/materias_consulta.html', context)

# Modificar Materia
def modificar_materia(request, clave):
    materia = get_object_or_404(Materia, clave=clave)

    if request.method == 'POST':
        materia.nombre = request.POST.get('nombre')
        materia.creditos = request.POST.get('creditos')
        materia.eje = request.POST.get('eje')
        carrera_id = request.POST.get('carrera')
        periodo_id = request.POST.get('periodo')

        # Validar campos
        if not (materia.nombre and materia.creditos and materia.eje):
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/materias_modificar.html', {'materia': materia})

        try:
            materia.carrera = Carrera.objects.get(id=carrera_id)
            materia.periodo = Periodo.objects.get(idPeriodo=periodo_id)
            materia.save()
            messages.success(request, 'La materia fue modificada exitosamente.')
            return redirect('materias_consulta')
        except Exception as e:
            messages.error(request, f"Error al modificar la materia: {e}")

    # Obtener carreras y periodos para el formulario
    carreras = Carrera.objects.all()
    periodos = Periodo.objects.all()

    context = {
        'materia': materia,
        'carreras': carreras,
        'periodos': periodos
    }

    return render(request, 'core/materias_modificar.html', context)

# Eliminar Materia
def eliminar_materia(request, clave):
    materia = get_object_or_404(Materia, clave=clave)

    if request.method == 'POST':
        try:
            materia.delete()
            messages.success(request, 'La materia fue eliminada exitosamente.')
            return redirect('materias_consulta')
        except Exception as e:
            messages.error(request, f'Error al eliminar la materia: {e}')

    return render(request, 'core/materias_eliminar.html', {'materia': materia})

def periodos_registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        inicial = request.POST.get('inicial')
        anio = request.POST.get('anio')

        # Validación básica
        if not nombre or not inicial or not anio:
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/periodos_registro.html')

        try:
            nuevo_periodo = Periodo(nombre=nombre, inicial=inicial, anio=anio)
            nuevo_periodo.save()
            messages.success(request, 'Periodo registrado exitosamente.')
            return redirect('periodos_registro')
        except Exception as e:
            messages.error(request, f'Error al registrar el periodo: {e}')

    return render(request, 'core/periodos_registro.html')

def periodos_consulta(request):
    busqueda = request.GET.get('busqueda')
    periodos = Periodo.objects.filter(nombre__icontains=busqueda) if busqueda else Periodo.objects.all()
    context = {'periodos': periodos, 'busqueda': busqueda}
    return render(request, 'core/periodos_consulta.html', context)

def modificar_periodo(request, idPeriodo):
    periodo = get_object_or_404(Periodo, idPeriodo=idPeriodo)

    if request.method == 'POST':
        periodo.nombre = request.POST.get('nombre')
        periodo.inicial = request.POST.get('inicial')
        periodo.anio = request.POST.get('anio')

        try:
            periodo.save()
            messages.success(request, 'Periodo modificado exitosamente.')
            return redirect('periodos_consulta')
        except Exception as e:
            messages.error(request, f'Error al modificar el periodo: {e}')

    return render(request, 'core/periodos_modificar.html', {'periodo': periodo})

def eliminar_periodo(request, idPeriodo):
    periodo = get_object_or_404(Periodo, idPeriodo=idPeriodo)

    if request.method == 'POST':
        try:
            periodo.delete()
            messages.success(request, 'Periodo eliminado exitosamente.')
            return redirect('periodos_consulta')
        except Exception as e:
            messages.error(request, f'Error al eliminar el periodo: {e}')

    return render(request, 'core/periodos_eliminar.html', {'periodo': periodo})
  
def grupos_profesor_registro(request):
    # Si el método es POST, significa que el formulario fue enviado
    if request.method == 'POST':
        # Obtén los datos del formulario
        codigo = request.POST.get('codigo')
        grado = request.POST.get('grado')
        grupo = request.POST.get('grupo')
        anio = request.POST.get('anio')
        profesor_id = request.POST.get('profesor')
        carrera_id = request.POST.get('carrera')
        periodo_id = request.POST.get('periodo')
        materia_id = request.POST.get('materia')

        # Verifica que los campos obligatorios no estén vacíos
        if not codigo or not grado or not grupo or not anio or not profesor_id or not carrera_id or not periodo_id or not materia_id:
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/profesor_grupos_registro.html', {
                'profesores': Profesor.objects.all(),
                'carreras': Carrera.objects.all(),
                'periodos': Periodo.objects.all(),
                'materias': Materia.objects.all()
            })

        try:
            # Crear el nuevo grupo
            profesor = Profesor.objects.get(clave=profesor_id)
            carrera = Carrera.objects.get(id=carrera_id)
            periodo = Periodo.objects.get(idPeriodo=periodo_id)
            materia = Materia.objects.get(clave=materia_id)

            nuevo_grupo = Clase(
                codigo=codigo,
                grado=grado,
                grupo=grupo,
                anio=anio,
                profesor=profesor,
                carrera=carrera,
                periodo=periodo,
                materia=materia
            )
            nuevo_grupo.save()
            messages.success(request, 'El grupo ha sido registrado exitosamente.')

            return redirect('grupos_profesor_registro')  # Redirige a la lista de grupos o cualquier otra página

        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')
            return render(request, 'core/profesor_grupos_registro.html', {
                'profesores': Profesor.objects.all(),
                'carreras': Carrera.objects.all(),
                'periodos': Periodo.objects.all(),
                'materias': Materia.objects.all()
            })

    # Si el método no es POST, simplemente muestra el formulario vacío
    else:
        return render(request, 'core/profesor_grupos_registro.html', {
            'profesores': Profesor.objects.all(),
            'carreras': Carrera.objects.all(),
            'periodos': Periodo.objects.all(),
            'materias': Materia.objects.all()
        })

def grupos_profesor_consulta(request):
    # Obtener el correo del profesor desde la sesión
    profesor_correo = request.session.get("correo")
    if not profesor_correo:
        messages.error(request, "No tienes permiso para acceder a esta sección.")
        return redirect("inicio")

    # Filtrar los grupos del profesor en sesión
    grupos = Clase.objects.filter(profesor__correo=profesor_correo)

    # Buscar por nombre o clave del grupo (campo de búsqueda)
    busqueda = request.GET.get('busqueda', '')
    if busqueda:
        grupos = grupos.filter(
            Q(materia__nombre__icontains=busqueda) |
            Q(codigo__icontains=busqueda)
        )

    context = {
        'resultados': grupos,
        'busqueda': busqueda,
    }

    return render(request, 'core/profesor_grupos_consulta.html', context)

def grupos_profesor_modificar(request, codigo):
    # Obtener el grupo
    grupo = get_object_or_404(Clase, codigo=codigo)
    profesores = Profesor.objects.all()
    carreras = Carrera.objects.all()
    periodos = Periodo.objects.all()
    materias = Materia.objects.all()

    if request.method == 'POST':
        # Actualizar los datos, sin cambiar llaves primarias
        grupo.grado = request.POST.get('grado')
        grupo.grupo = request.POST.get('grupo')
        grupo.anio = request.POST.get('anio')
        grupo.profesor = Profesor.objects.get(clave=request.POST.get('profesor'))
        grupo.carrera = Carrera.objects.get(id=request.POST.get('carrera'))
        grupo.periodo = Periodo.objects.get(idPeriodo=request.POST.get('periodo'))
        grupo.materia = Materia.objects.get(clave=request.POST.get('materia'))

        try:
            grupo.save()
            messages.success(request, "El grupo fue modificado exitosamente.")
            return redirect('grupos_profesor_consulta')  # Redirige a la página de consulta
        except Exception as e:
            messages.error(request, f"Error al modificar el grupo: {e}")

    return render(request, 'core/profesor_grupos_modificar.html', {
        'grupo': grupo,
        'profesores': profesores,
        'carreras': carreras,
        'periodos': periodos,
        'materias': materias
    })

def grupos_profesor_eliminar(request, codigo):
    grupo = get_object_or_404(Clase, codigo=codigo)

    if request.method == 'POST':
        try:
            grupo.delete()
            messages.success(request, "El grupo fue eliminado exitosamente.")
            return redirect('grupos_profesor_consulta')  # Regresa a la tabla de consulta
        except Exception as e:
            messages.error(request, f"Error al eliminar el grupo: {e}")

    # Renderiza la página de confirmación de eliminación
    return render(request, 'core/profesor_grupos_eliminar.html', {'grupo': grupo})

def profesor_justificantes_consulta(request):
    # Obtener el correo del profesor desde la sesión
    profesor_correo = request.session.get("correo")

    # Validar que el profesor esté en sesión
    if not profesor_correo:
        messages.error(request, "No se pudo identificar al profesor en sesión.")
        return redirect('login')  # Redirigir al inicio o a la página de login

    # Obtener el profesor en sesión
    profesor = Profesor.objects.filter(correo=profesor_correo).first()
    if not profesor:
        messages.error(request, "Profesor no encontrado.")
        return redirect('login')

    # Obtener los justificantes asociados al profesor en sesión
    justificantes = Justificante.objects.filter(profesor=profesor).select_related(
        'alumno', 'profesor'
    ).prefetch_related(
        Prefetch('alumno__clasealumno_set', queryset=ClaseAlumno.objects.select_related('clase'))
    )

    # Filtro de búsqueda opcional
    busqueda = request.GET.get('busqueda', '')
    if busqueda:
        justificantes = justificantes.filter(descripcion__icontains=busqueda)

    return render(request, 'core/profesor_justificantes_consulta.html', {
        'justificantes': justificantes
    })

def profesor_justificantes_modificar(request, idJustificante):
    # Obtener el correo del profesor desde la sesión
    profesor_correo = request.session.get("correo")

    # Validar que el profesor esté en sesión
    if not profesor_correo:
        messages.error(request, "No se pudo identificar al profesor en sesión.")
        return redirect('inicio')

    # Obtener el profesor en sesión
    profesor = Profesor.objects.filter(correo=profesor_correo).first()
    if not profesor:
        messages.error(request, "Profesor no encontrado.")
        return redirect('inicio')

    # Verificar que el justificante pertenece al profesor
    justificante = get_object_or_404(Justificante, idJustificante=idJustificante, profesor=profesor)

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        estado = request.POST.get('estado')

        # Validar campos obligatorios
        if not descripcion or not estado:
            messages.error(request, 'Por favor, complete todos los campos.')
            return render(request, 'core/profesor_justificantes_modificar.html', {'justificante': justificante})

        try:
            # Actualizar datos del justificante
            justificante.descripcion = descripcion
            justificante.estado = estado
            justificante.save()

            messages.success(request, 'El justificante ha sido modificado exitosamente.')
            return redirect('profesor_justificantes_consulta')

        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')

    return render(request, 'core/profesor_justificantes_modificar.html', {
        'justificante': justificante
    })

def profesor_justificantes_eliminar(request, idJustificante):
    # Obtener el correo del profesor desde la sesión
    profesor_correo = request.session.get("correo")

    # Validar que el profesor esté en sesión
    if not profesor_correo:
        messages.error(request, "No se pudo identificar al profesor en sesión.")
        return redirect('inicio')

    # Obtener el profesor en sesión
    profesor = Profesor.objects.filter(correo=profesor_correo).first()
    if not profesor:
        messages.error(request, "Profesor no encontrado.")
        return redirect('inicio')

    # Verificar que el justificante pertenece al profesor
    justificante = get_object_or_404(Justificante, idJustificante=idJustificante, profesor=profesor)

    if request.method == 'POST':
        try:
            justificante.delete()
            messages.success(request, 'El justificante ha sido eliminado.')
            return redirect('profesor_justificantes_consulta')
        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')

    return render(request, 'core/profesor_justificantes_eliminar.html', {
        'justificante': justificante
    })

def alumno_grupos_inscribirse(request):
    # Recuperar el correo del alumno en la sesión
    correo_alumno = request.session.get('correo')

    # Obtener al alumno en base a su correo
    alumno = Alumno.objects.filter(correo=correo_alumno).first()

    # Obtener parámetros de los filtros de la consulta
    carrera_id = request.GET.get('carrera')
    materia_id = request.GET.get('materia')
    periodo_id = request.GET.get('periodo')
    profesor_id = request.GET.get('profesor')
    busqueda = request.GET.get('busqueda')

    # Grupos en los que el alumno ya está inscrito
    grupos_inscritos = ClaseAlumno.objects.filter(alumno=alumno).values_list('clase__codigo', flat=True)

    # Filtrar las clases donde el alumno no está inscrito
    query = Clase.objects.exclude(codigo__in=grupos_inscritos)

    # Aplicar los filtros de la consulta
    if busqueda:
        query = query.filter(Q(codigo__icontains=busqueda) | Q(materia__nombre__icontains=busqueda))
    if carrera_id:
        query = query.filter(carrera_id=carrera_id)
    if materia_id:
        query = query.filter(materia_id=materia_id)
    if periodo_id:
        query = query.filter(periodo_id=periodo_id)
    if profesor_id:
        query = query.filter(profesor_id=profesor_id)

    # Obtener los datos para los filtros en el formulario
    carreras = Carrera.objects.all()
    materias = Materia.objects.all()
    periodos = Periodo.objects.all()
    profesores = Profesor.objects.all()

    context = {
        'filtros': {
            'carrera': carrera_id,
            'materia': materia_id,
            'periodo': periodo_id,
            'profesor': profesor_id,
            'busqueda': busqueda
        },
        'resultados': query,
        'carreras': carreras,
        'materias': materias,
        'periodos': periodos,
        'profesores': profesores
    }

    return render(request, 'core/alumno_grupos_inscribirse.html', context)

def alumno_grupos_registarse(request, codigo):
    # Recuperar el correo del alumno en la sesión
    correo_alumno = request.session.get('correo')

    # Obtener al alumno en base a su correo
    alumno = Alumno.objects.filter(correo=correo_alumno).first()

    # Obtener el grupo basado en el código
    grupo = Clase.objects.filter(codigo=codigo).first()

    if request.method == 'POST' and grupo:
        # Crear la inscripción en la tabla ClaseAlumno
        ClaseAlumno.objects.create(clase=grupo, alumno=alumno)
        return redirect('alumno_grupos_consulta')  # Redirigir a la página de consulta de grupos

    return render(request, 'core/alumno_grupos_registrarse.html', {'grupo': grupo})

def alumno_grupos_consulta(request):
    # Recuperar el correo del alumno en la sesión
    correo_alumno = request.session.get('correo')

    # Obtener al alumno en base a su correo
    alumno = Alumno.objects.filter(correo=correo_alumno).first()

    # Obtener parámetros de los filtros de la consulta
    carrera_id = request.GET.get('carrera')
    materia_id = request.GET.get('materia')
    periodo_id = request.GET.get('periodo')
    profesor_id = request.GET.get('profesor')
    busqueda = request.GET.get('busqueda')

    # Obtener los grupos en los que el alumno está inscrito
    grupos_inscritos = ClaseAlumno.objects.filter(alumno=alumno).select_related('clase')

    # Filtrar los grupos inscritos
    query = grupos_inscritos
    if busqueda:
        query = query.filter(Q(clase__codigo__icontains=busqueda) | Q(clase__materia__nombre__icontains=busqueda))
    if carrera_id:
        query = query.filter(clase__carrera_id=carrera_id)
    if materia_id:
        query = query.filter(clase__materia_id=materia_id)
    if periodo_id:
        query = query.filter(clase__periodo_id=periodo_id)
    if profesor_id:
        query = query.filter(clase__profesor_id=profesor_id)

    # Obtener los datos para los filtros en el formulario
    carreras = Carrera.objects.all()
    materias = Materia.objects.all()
    periodos = Periodo.objects.all()
    profesores = Profesor.objects.all()

    context = {
        'filtros': {
            'carrera': carrera_id,
            'materia': materia_id,
            'periodo': periodo_id,
            'profesor': profesor_id,
            'busqueda': busqueda
        },
        'resultados': [grupo.clase for grupo in query],
        'carreras': carreras,
        'materias': materias,
        'periodos': periodos,
        'profesores': profesores
    }

    return render(request, 'core/alumno_grupos_consulta.html', context)

def alumno_grupos_asistencia(request, codigo):
    # Recuperar el correo del alumno en la sesión
    correo_alumno = request.session.get('correo')

    if not correo_alumno:
        messages.error(request, "No se ha encontrado el correo del alumno en la sesión.")
        return redirect('alumno_dashboard')  # Redirigir a una página adecuada

    # Obtener al alumno en base a su correo
    alumno = get_object_or_404(Alumno, correo=correo_alumno)

    # Verificar que el grupo especificado exista
    clase = get_object_or_404(Clase, codigo=codigo)

    # Obtener las asistencias del alumno para el grupo especificado
    asistencias = AlumnoLista.objects.filter(clase_alumno__alumno=alumno, clase_alumno__clase=clase).select_related('lista', 'clase_alumno__alumno')

    if not asistencias.exists():
        messages.warning(request, "No se encontraron registros de asistencia para este grupo.")
        return redirect('alumno_grupos_consulta')  # Redirigir a la página de consulta de grupos

    context = {
        'asistencias': asistencias
    }

    return render(request, 'core/alumno_grupos_asistencia.html', context)

def alumno_justificantes_registro(request):
    # Recuperar el correo del alumno en la sesión
    correo_alumno = request.session.get('correo')

    if not correo_alumno:
        messages.error(request, "No se ha encontrado el correo del alumno en la sesión.")
        return redirect('alumno_dashboard')  # Redirigir a una página adecuada

    # Obtener al alumno en base a su correo
    alumno = Alumno.objects.filter(correo=correo_alumno).first()

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        grupo_codigo = request.POST.get('grupo')

        # Obtener el grupo basado en el código
        grupo = Clase.objects.filter(codigo=grupo_codigo).first()

        if not grupo:
            messages.error(request, "Grupo no encontrado.")
        else:
            # Crear el justificante con estado inicial "Pendiente"
            Justificante.objects.create(
                descripcion=descripcion,
                estado="Pendiente",  # Estado inicial
                alumno=alumno,
                profesor=grupo.profesor
            )
            messages.success(request, 'Justificante registrado con éxito.')
            return redirect('alumno_justificantes_registro')

    # Obtener la lista de grupos en los que el alumno está inscrito
    grupos_inscritos = ClaseAlumno.objects.filter(alumno=alumno).select_related('clase')

    context = {
        'grupos': [grupo.clase for grupo in grupos_inscritos]
    }

    return render(request, 'core/alumno_justificante_registro.html', context)

def alumno_justificantes_consulta(request):
    # Recuperar el correo del alumno en la sesión
    correo_alumno = request.session.get('correo')

    if not correo_alumno:
        messages.error(request, "No se ha encontrado el correo del alumno en la sesión.")
        return redirect('alumno_dashboard')  # Redirigir a una página adecuada

    # Obtener al alumno en base a su correo
    alumno = Alumno.objects.filter(correo=correo_alumno).first()

    # Obtener los justificantes asociados al alumno
    justificantes = Justificante.objects.filter(alumno=alumno).select_related('profesor')

    # Filtro de búsqueda opcional
    busqueda = request.GET.get('busqueda', '')
    if busqueda:
        justificantes = justificantes.filter(descripcion__icontains=busqueda)

    return render(request, 'core/alumno_justificante_consulta.html', {
        'justificantes': justificantes,
        'busqueda': busqueda
    })

def alumno_subir_foto(request):
    # Recuperar el correo del alumno en la sesión
    correo_alumno = request.session.get('correo')

    if not correo_alumno:
        messages.error(request, "No se ha encontrado el correo del alumno en la sesión.")
        return redirect('alumno_dashboard')  # Redirigir a una página adecuada

    # Obtener al alumno en base a su correo
    alumno = Alumno.objects.filter(correo=correo_alumno).first()

    if request.method == 'POST' and request.FILES:
        fotos = request.FILES.getlist('foto')
        for foto in fotos:
            # Crear una nueva instancia de Foto y guardarla
            Foto.objects.create(alumno=alumno, imagen=foto)
        messages.success(request, 'Fotos subidas con éxito.')
        return redirect('alumno_subir_foto')

    # Obtener las fotos subidas por el alumno
    fotos = Foto.objects.filter(alumno=alumno)

    context = {
        'alumno': alumno,
        'fotos': fotos
    }

    return render(request, 'core/alumno_subir_foto.html', context)

def iniciar_pase_lista(request, codigo):
    # Obtener el grupo basado en el código
    grupo = get_object_or_404(Clase, codigo=codigo)

    if request.method == 'POST':
        # Capturar la imagen de la cámara
        video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Usar DirectShow para la captura de video en Windows
        ret, frame = video_capture.read()
        video_capture.release()

        if not ret:
            messages.error(request, "No se pudo capturar la imagen.")
            return redirect('iniciar_pase_lista', codigo=codigo)

        # Convertir la imagen de BGR (OpenCV) a RGB (face_recognition)
        rgb_frame = frame[:, :, ::-1]

        # Encontrar todas las caras en la imagen
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        print(face_locations)
        # Obtener las fotos de los alumnos registrados en el grupo
        alumnos = ClaseAlumno.objects.filter(clase=grupo).select_related('alumno')
        known_face_encodings = []
        known_face_names = []

        for clase_alumno in alumnos:
            fotos = Foto.objects.filter(alumno=clase_alumno.alumno)
            for foto in fotos:
                image = face_recognition.load_image_file(foto.imagen.path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    encoding = encodings[0]
                    known_face_encodings.append(encoding)
                    known_face_names.append(clase_alumno.alumno.matricula)

        # Comparar las caras encontradas con las caras conocidas
        asistencia = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Desconocido"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            print(face_distances)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                asistencia.append(name)

        # Registrar la asistencia solo si hay coincidencias
        if asistencia:
            lista_asistencia = ListaAsistencia.objects.create(fecha=timezone.now(), promedio=0.0)
            for matricula in asistencia:
                alumno = Alumno.objects.get(matricula=matricula)
                clase_alumno = ClaseAlumno.objects.get(clase=grupo, alumno=alumno)
                AlumnoLista.objects.create(lista=lista_asistencia, clase_alumno=clase_alumno, calificacion='1')

            messages.success(request, "Pase de lista completado.")
        else:
            messages.warning(request, "No se encontraron coincidencias de caras.")

        return redirect('iniciar_pase_lista', codigo=codigo)

    context = {
        'grupo': grupo
    }
    return render(request, 'core/iniciar_pase_lista.html', context)

def reporte_carrera(request):
    if request.method == 'POST':
        carrera_id = request.POST.get('carrera')
        return redirect('generar_reporte_carrera', carrera_id=carrera_id)

    carreras = Carrera.objects.all()
    return render(request, 'core/reporte_carrera.html', {'carreras': carreras})

def reporte_grupo(request):
    if request.method == 'POST':
        grupo_codigo = request.POST.get('grupo')
        if grupo_codigo:  # Verificar que grupo_codigo no sea None o vacío
            return redirect('generar_reporte_grupo', grupo_codigo=grupo_codigo)
        else:
            messages.error(request, "Por favor, selecciona un grupo válido.")
            return redirect('reporte_grupo')

    grupos = Clase.objects.all()
    return render(request, 'core/reporte_grupo.html', {'grupos': grupos})

def generar_reporte_carrera(request, carrera_id):
    carrera = get_object_or_404(Carrera, id=carrera_id)
    grupos = Clase.objects.filter(carrera=carrera)
    alumnos = Alumno.objects.filter(carrera=carrera)

    # Estadísticas y Análisis
    promedio_calificaciones = AlumnoLista.objects.filter(clase_alumno__clase__carrera=carrera).aggregate(Avg('calificacion'))['calificacion__avg'] or 0
    tasa_asistencia = AlumnoLista.objects.filter(clase_alumno__clase__carrera=carrera, calificacion='A').count() / AlumnoLista.objects.filter(clase_alumno__clase__carrera=carrera).count() if AlumnoLista.objects.filter(clase_alumno__clase__carrera=carrera).count() > 0 else 0
    distribucion_genero = alumnos.values('genero').annotate(count=Count('genero'))

    context = {
        'carrera': carrera,
        'grupos': grupos,
        'promedio_calificaciones': promedio_calificaciones,
        'tasa_asistencia': tasa_asistencia,
        'distribucion_genero': distribucion_genero,
    }

    return render(request, 'core/generar_reporte_carrera.html', context)

def generar_pdf_reporte_carrera(request, carrera_id):
    carrera = get_object_or_404(Carrera, id=carrera_id)
    grupos = Clase.objects.filter(carrera=carrera)
    alumnos = Alumno.objects.filter(carrera=carrera)

    # Estadísticas y Análisis
    promedio_calificaciones = AlumnoLista.objects.filter(clase_alumno__clase__carrera=carrera).aggregate(Avg('calificacion'))['calificacion__avg'] or 0
    tasa_asistencia = AlumnoLista.objects.filter(clase_alumno__clase__carrera=carrera, calificacion='A').count() / AlumnoLista.objects.filter(clase_alumno__clase__carrera=carrera).count() if AlumnoLista.objects.filter(clase_alumno__clase__carrera=carrera).count() > 0 else 0
    distribucion_genero = alumnos.values('genero').annotate(count=Count('genero'))

    # Crear el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_carrera_{carrera.nombre}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    subtitle_style = ParagraphStyle(name='Subtitle', fontSize=14, leading=16, spaceAfter=10)
    normal_style = styles['Normal']

    elements.append(Paragraph(f'Reporte de Carrera: {carrera.nombre}', title_style))
    elements.append(Spacer(1, 12))

    # Promedio de Calificaciones
    elements.append(Paragraph('Promedio de Calificaciones', subtitle_style))
    elements.append(Paragraph(f'{promedio_calificaciones:.2f}', normal_style))
    elements.append(Spacer(1, 12))

    # Tasa de Asistencia
    elements.append(Paragraph('Tasa de Asistencia', subtitle_style))
    elements.append(Paragraph(f'{tasa_asistencia:.2%}', normal_style))
    elements.append(Spacer(1, 12))

    # Distribución de Género
    elements.append(Paragraph('Distribución de Género', subtitle_style))
    data = [['Género', 'Cantidad']]
    for genero in distribucion_genero:
        data.append([genero['genero'], genero['count']])
    table = Table(data, colWidths=[100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    doc.build(elements)
    return response

def generar_reporte_grupo(request, grupo_codigo):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_grupo_{grupo_codigo}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    style_title = styles['Title']
    style_normal = styles['Normal']

    grupo = get_object_or_404(Clase, codigo=grupo_codigo)
    elements.append(Paragraph(f"Reporte de Asistencia del Grupo {grupo.codigo}", style_title))

    asistencias = AlumnoLista.objects.filter(clase_alumno__clase=grupo).select_related('clase_alumno__alumno', 'lista')

    total_asistencias = asistencias.count()
    total_alumnos = ClaseAlumno.objects.filter(clase=grupo).count()
    total_clases = ListaAsistencia.objects.filter(alumnolista__clase_alumno__clase=grupo).distinct().count()

    data = [['Alumno', 'Asistencias', 'Faltas', 'Porcentaje de Asistencia']]
    for alumno in ClaseAlumno.objects.filter(clase=grupo):
        asistencias_alumno = asistencias.filter(clase_alumno=alumno).count()
        faltas_alumno = total_clases - asistencias_alumno
        porcentaje_asistencia = (asistencias_alumno / total_clases) * 100 if total_clases > 0 else 0
        data.append([
            f"{alumno.alumno.nombres} {alumno.alumno.apellidoP} {alumno.alumno.apellidoM}",
            asistencias_alumno,
            faltas_alumno,
            f"{porcentaje_asistencia:.2f}%"
        ])

    table = Table(data, colWidths=[200, 100, 100, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    return response

def reporte_profesor(request):
    if request.method == 'POST':
        profesor_correo = request.session.get('correo')
        if not profesor_correo:
            messages.error(request, "No se pudo identificar al profesor en sesión.")
            return redirect('inicio')

        profesor = Profesor.objects.filter(correo=profesor_correo).first()
        if not profesor:
            messages.error(request, "Profesor no encontrado.")
            return redirect('inicio')

        return redirect('generar_reporte_profesor', profesor_clave=profesor.clave)

    return render(request, 'core/reporte_profesor.html')

def generar_reporte_profesor(request, profesor_clave):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_profesor_{profesor_clave}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    style_title = styles['Title']
    style_normal = styles['Normal']

    profesor = get_object_or_404(Profesor, clave=profesor_clave)
    elements.append(Paragraph(f"Reporte de Asistencia de los Grupos del Profesor {profesor.nombres} {profesor.apellidoP}", style_title))

    grupos = Clase.objects.filter(profesor=profesor)
    for grupo in grupos:
        elements.append(Paragraph(f"Grupo: {grupo.codigo}", style_normal))
        asistencias = AlumnoLista.objects.filter(clase_alumno__clase=grupo).select_related('clase_alumno__alumno', 'lista')

        total_asistencias = asistencias.count()
        total_alumnos = ClaseAlumno.objects.filter(clase=grupo).count()
        total_clases = ListaAsistencia.objects.filter(alumnolista__clase_alumno__clase=grupo).distinct().count()

        data = [['Alumno', 'Asistencias', 'Faltas', 'Porcentaje de Asistencia']]
        for alumno in ClaseAlumno.objects.filter(clase=grupo):
            asistencias_alumno = asistencias.filter(clase_alumno=alumno).count()
            faltas_alumno = total_clases - asistencias_alumno
            porcentaje_asistencia = (asistencias_alumno / total_clases) * 100 if total_clases > 0 else 0
            data.append([
                f"{alumno.alumno.nombres} {alumno.alumno.apellidoP} {alumno.alumno.apellidoM}",
                asistencias_alumno,
                faltas_alumno,
                f"{porcentaje_asistencia:.2f}%"
            ])

        table = Table(data, colWidths=[200, 100, 100, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
        elements.append(Paragraph("<br/>", style_normal))  # Add space between tables

    doc.build(elements)
    return response

def reporte_alumno(request):
    if request.method == 'POST':
        alumno_correo = request.session.get('correo')
        if not alumno_correo:
            messages.error(request, "No se pudo identificar al alumno en sesión.")
            return redirect('inicio')

        alumno = Alumno.objects.filter(correo=alumno_correo).first()
        if not alumno:
            messages.error(request, "Alumno no encontrado.")
            return redirect('inicio')

        return redirect('generar_reporte_alumno', alumno_matricula=alumno.matricula)

    return render(request, 'core/reporte_alumno.html')

def generar_reporte_alumno(request, alumno_matricula):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_alumno_{alumno_matricula}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    style_title = styles['Title']
    style_normal = styles['Normal']

    alumno = get_object_or_404(Alumno, matricula=alumno_matricula)
    elements.append(Paragraph(f"Reporte de Asistencia de los Grupos del Alumno {alumno.nombres} {alumno.apellidoP}", style_title))

    grupos = ClaseAlumno.objects.filter(alumno=alumno).select_related('clase')
    for clase_alumno in grupos:
        grupo = clase_alumno.clase
        elements.append(Paragraph(f"Grupo: {grupo.codigo}", style_normal))
        asistencias = AlumnoLista.objects.filter(clase_alumno=clase_alumno).select_related('lista')

        total_asistencias = asistencias.count()
        total_clases = ListaAsistencia.objects.filter(alumnolista__clase_alumno__clase=grupo).distinct().count()
        faltas_alumno = total_clases - total_asistencias
        porcentaje_asistencia = (total_asistencias / total_clases) * 100 if total_clases > 0 else 0
        porcentaje_faltas = (faltas_alumno / total_clases) * 100 if total_clases > 0 else 0

        data = [
            ['Estadística', 'Valor'],
            ['Total de Asistencias', total_asistencias],
            ['Total de Faltas', faltas_alumno],
            ['Porcentaje de Asistencia', f"{porcentaje_asistencia:.2f}%"],
            ['Porcentaje de Faltas', f"{porcentaje_faltas:.2f}%"],
            ['Fecha', 'Calificación']
        ]
        for asistencia in asistencias:
            data.append([
                asistencia.lista.fecha.strftime('%Y-%m-%d'),
                asistencia.calificacion
            ])

        table = Table(data, colWidths=[200, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
        elements.append(Paragraph("<br/>", style_normal))  # Add space between tables

    doc.build(elements)
    return response

def reporte_lista_asistencia_profesor(request):
    if request.method == 'POST':
        grupo_codigo = request.POST.get('grupo')
        return redirect('generar_lista_asistencia_profesor', grupo_codigo=grupo_codigo)

    profesor_correo = request.session.get('correo')
    grupos = Clase.objects.filter(profesor__correo=profesor_correo)
    return render(request, 'core/reporte_lista_asistencia_profesor.html', {'grupos': grupos})

def generar_lista_asistencia_profesor(request, grupo_codigo):
    grupo = get_object_or_404(Clase, codigo=grupo_codigo)
    alumnos = ClaseAlumno.objects.filter(clase=grupo).select_related('alumno')
    lista_asistencia = AlumnoLista.objects.filter(clase_alumno__clase=grupo).select_related('clase_alumno__alumno', 'lista')

    fechas = lista_asistencia.values_list('lista__fecha', flat=True).distinct()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="lista_asistencia_{grupo_codigo}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    style_title = styles['Title']
    style_normal = styles['Normal']

    elements.append(Paragraph(f"Lista de Asistencia para el Grupo {grupo.codigo}", style_title))

    data = [['Nombre del Alumno'] + [str(fecha) for fecha in fechas]]
    for alumno in alumnos:
        row = [f"{alumno.alumno.nombres} {alumno.alumno.apellidoP} {alumno.alumno.apellidoM}"]
        for fecha in fechas:
            calificacion = ''
            for asistencia in lista_asistencia:
                if asistencia.clase_alumno.alumno == alumno.alumno and asistencia.lista.fecha == fecha:
                    calificacion = asistencia.calificacion
            row.append(calificacion)
        data.append(row)

    table = Table(data, colWidths=[200] + [100] * len(fechas))
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    return response

def listar_asistencias(request, grupo_codigo):
    grupo = get_object_or_404(Clase, codigo=grupo_codigo)
    listas_asistencia = ListaAsistencia.objects.filter(alumnolista__clase_alumno__clase=grupo).distinct()

    context = {
        'grupo': grupo,
        'listas_asistencia': listas_asistencia
    }

    return render(request, 'core/listar_asistencias.html', context)

def editar_asistencia(request, lista_id):
    lista_asistencia = get_object_or_404(ListaAsistencia, idLista=lista_id)
    alumnos_lista = AlumnoLista.objects.filter(lista=lista_asistencia).select_related('clase_alumno__alumno')

    if request.method == 'POST':
        for alumno_lista in alumnos_lista:
            calificacion = request.POST.get(f'calificacion_{alumno_lista.id}')
            alumno_lista.calificacion = calificacion
            alumno_lista.save()
        messages.success(request, 'Asistencia actualizada correctamente.')
        # Obtener el grupo a través de la relación ClaseAlumno
        grupo_codigo = alumnos_lista.first().clase_alumno.clase.codigo
        return redirect('listar_asistencias', grupo_codigo=grupo_codigo)

    context = {
        'lista_asistencia': lista_asistencia,
        'alumnos_lista': alumnos_lista
    }

    return render(request, 'core/editar_asistencia.html', context)

def respaldo_base_datos(request):
    return render(request, 'core/respaldo_base_datos.html')

def descargar_respaldo(request):
    try:
        # Configuración de la base de datos
        db_host = 'localhost'
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "quicklist")
        db_name = os.getenv("DB_NAME", "quicklist")

        # Archivo de respaldo
        backup_file = 'respaldo.sql'

        # Ruta completa a mysqldump
        mysqldump_path = r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqldump.exe"

        # Comando mysqldump
        dump_command = f'"{mysqldump_path}" -h {db_host} -u {db_user} -p{db_password} {db_name} > {backup_file}'

        # Ejecutar el comando mysqldump
        subprocess.run(dump_command, shell=True, check=True)

        # Enviar el archivo como respuesta
        with open(backup_file, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/sql')
            response['Content-Disposition'] = f'attachment; filename={backup_file}'
            return response
    except subprocess.CalledProcessError as e:
        messages.error(request, f"Error al ejecutar mysqldump: {str(e)}")
        return redirect('respaldo_base_datos')
    except Error as e:
        messages.error(request, f"Error al conectarse a la base de datos: {str(e)}")
        return redirect('respaldo_base_datos')
    finally:
        # Eliminar el archivo de respaldo temporal
        if os.path.exists(backup_file):
            os.remove(backup_file)

def cargar_base_datos(request):
    if request.method == 'POST' and request.FILES['archivo']:
        archivo = request.FILES['archivo']
        try:
            # Guardar el archivo temporalmente
            fs = FileSystemStorage()
            filename = fs.save(archivo.name, archivo)
            file_path = fs.path(filename)

            # Conectar a la base de datos
            connection = mysql.connector.connect(
                host='localhost',
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", "quicklist"),
                database=os.getenv("DB_NAME", "quicklist")
            )
            cursor = connection.cursor()

            # Leer y ejecutar el archivo SQL
            with open(file_path, 'r') as f:
                sql = f.read()
                for statement in sql.split(';'):
                    if statement.strip():
                        cursor.execute(statement)

            connection.commit()
            messages.success(request, "Base de datos cargada exitosamente.")
        except Error as e:
            messages.error(request, f"Error al cargar la base de datos: {str(e)}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
            # Eliminar el archivo temporal
            fs.delete(filename)
        return redirect('respaldo_base_datos')
    return render(request, 'core/cargar_base_datos.html')

def alumno_retroalimentacion(request):
    if request.method == 'POST':
        form = RetroalimentacionForm(request.POST)
        if form.is_valid():
            retroalimentacion = form.save(commit=False)
            retroalimentacion.alumno = Alumno.objects.get(correo=request.session['correo'])
            retroalimentacion.save()
            messages.success(request, 'Retroalimentación enviada correctamente.')
            return redirect('alumno_retroalimentacion')
    else:
        form = RetroalimentacionForm()
    return render(request, 'core/alumno_retroalimentacion.html', {'form': form})

def administrador_retroalimentacion(request):
    retroalimentaciones = Retroalimentacion.objects.all()
    return render(request, 'core/administrador_retroalimentacion.html', {'retroalimentaciones': retroalimentaciones})

def generar_reporte_retroalimentacion(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if not fecha_inicio or not fecha_fin:
        messages.error(request, "Por favor, seleccione un rango de fechas válido.")
        return redirect('administrador_retroalimentacion')

    retroalimentaciones = Retroalimentacion.objects.filter(fecha_reporte__range=[fecha_inicio, fecha_fin])
    promedio_calificaciones = retroalimentaciones.aggregate(Avg('calificacion'))['calificacion__avg'] or 0

    # Crear el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_retroalimentacion_{fecha_inicio}_a_{fecha_fin}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    subtitle_style = ParagraphStyle(name='Subtitle', fontSize=14, leading=16, spaceAfter=10)
    normal_style = styles['Normal']

    elements.append(Paragraph(f'Reporte de Retroalimentación del Sistema', title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f'Rango de Fechas: {fecha_inicio} a {fecha_fin}', subtitle_style))
    elements.append(Spacer(1, 12))

    # Promedio de Calificaciones
    elements.append(Paragraph('Promedio de Calificaciones', subtitle_style))
    elements.append(Paragraph(f'{promedio_calificaciones:.2f}', normal_style))
    elements.append(Spacer(1, 12))

    # Retroalimentaciones
    elements.append(Paragraph('Retroalimentaciones', subtitle_style))
    data = [['Alumno', 'Descripción', 'Calificación', 'Fecha']]
    for retroalimentacion in retroalimentaciones:
        data.append([
            f"{retroalimentacion.alumno.nombres} {retroalimentacion.alumno.apellidoP} {retroalimentacion.alumno.apellidoM}",
            retroalimentacion.descripcion,
            retroalimentacion.calificacion,
            retroalimentacion.fecha_reporte.strftime('%Y-%m-%d %H:%M:%S')
        ])
    table = Table(data, colWidths=[150, 250, 50, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    doc.build(elements)
    return response