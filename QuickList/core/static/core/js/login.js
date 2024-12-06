document.addEventListener('DOMContentLoaded', function () {
    console.log('Interactividad de inicio de sesión lista.');

    const loginForm = document.getElementById('loginForm');

    loginForm.addEventListener('submit', function (event) {
        const emailField = document.getElementById('loginUser');
        const passwordField = document.getElementById('loginPassword');
        const email = emailField.value.trim();
        const password = passwordField.value.trim();

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        // Validación del correo electrónico
        if (!emailRegex.test(email)) {
            alert('Por favor, introduce un correo electrónico válido.');
            event.preventDefault();
        }

        // Validación de la longitud de la contraseña
        if (password.length < 6) {
            alert('La contraseña debe tener al menos 6 caracteres.');
            event.preventDefault();
        }
    });
});
