// Función para redirigir al usuario a la página de cierre de sesión
function logoutUser(logoutUrl) {
    window.location.href = logoutUrl;
}

// Validación del formulario de registro
function validarFormularioRegistro() {
    const form = document.getElementById('form-usuario');
    const nombre = form.nombre.value.trim();
    const correo = form.correo.value.trim();
    const clave = form.clave.value.trim();
    const claveConfirma = form.clave_confirmar.value.trim();
    const tipoUsuario = form.tipo_usuario.value;

    const regexCorreo = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;

    if (!nombre || !correo || !clave || !claveConfirma || !tipoUsuario) {
        alert("Por favor, complete todos los campos.");
        return false;
    }

    if (!regexCorreo.test(correo)) {
        alert("El correo electrónico no es válido.");
        return false;
    }

    if (clave !== claveConfirma) {
        alert("Las contraseñas no coinciden.");
        return false;
    }

    return true;
}