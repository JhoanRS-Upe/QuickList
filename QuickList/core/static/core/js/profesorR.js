document.addEventListener('DOMContentLoaded', function () {
    const profesorForm = document.getElementById('profesorForm');
    const formContainer = document.getElementById('form-container');
    const btnAlumno = document.getElementById('btnAlumno');
    const btnProfesor = document.getElementById('btnProfesor');

    // Función para cargar formularios dinámicamente
    function loadForm(url) {
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error al cargar el formulario: ${response.statusText}`);
                }
                return response.text();
            })
            .then(data => {
                formContainer.innerHTML = data; // Inserta el formulario en el contenedor
            })
            .catch(error => {
                console.error('Error:', error);
                formContainer.innerHTML = '<p>Error al cargar el formulario.</p>';
            });
    }

    // Agrega eventos a los botones
    btnAlumno.addEventListener('click', () => loadForm('/registro/alumno/'));
    btnProfesor.addEventListener('click', () => loadForm('/registro/profesor/'));

    profesorForm.addEventListener('submit', function (event) {
        const clave = document.getElementById('clave').value.trim();
        const email = document.getElementById('correo').value.trim();
        const password = document.getElementById('contrasenia').value.trim();
        const confirmPassword = document.getElementById('confirmPassword').value.trim();
        const nombre = document.getElementById('nombres').value.trim();
        const apellidoP = document.getElementById('apellidoP').value.trim();
        const apellidoM = document.getElementById('apellidoM').value.trim();
        const fechaNac = document.getElementById('fechaNac').value.trim();
        const academia = document.getElementById('academia').value.trim();
        const grado = document.getElementById('grado').value.trim();

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const claveRegex = /^[a-zA-Z0-9]+$/;
        const nombreRegex = /^[a-zA-Z\s]+$/;
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

        if (!claveRegex.test(clave)) {
            alert('La clave solo debe contener letras y números.');
            event.preventDefault();
        }

        if (!emailRegex.test(email)) {
            alert('Por favor, introduce un correo electrónico válido.');
            event.preventDefault();
        }

        if (password !== confirmPassword) {
            alert('Las contraseñas no coinciden.');
            event.preventDefault();
        }

        if (password.length < 6) {
            alert('La contraseña debe tener al menos 6 caracteres.');
            event.preventDefault();
        }

        if (!nombreRegex.test(nombre)) {
            alert('El nombre solo debe contener letras y espacios.');
            event.preventDefault();
        }

        if (!nombreRegex.test(apellidoP)) {
            alert('El apellido paterno solo debe contener letras y espacios.');
            event.preventDefault();
        }

        if (!nombreRegex.test(apellidoM)) {
            alert('El apellido materno solo debe contener letras y espacios.');
            event.preventDefault();
        }

        // Validar fecha de nacimiento
        if (!dateRegex.test(fechaNac)) {
            alert('La fecha de nacimiento debe estar en el formato YYYY-MM-DD.');
            event.preventDefault();
        }

        if (academia === "") {
            alert('Por favor, selecciona una academia.');
            event.preventDefault();
        }

        if (grado === "") {
            alert('Por favor, introduce el grado académico.');
            event.preventDefault();
        }
    });
});
