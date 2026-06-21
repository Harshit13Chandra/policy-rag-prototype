import { apiFetch, setAccessToken } from "./api.js";

const loginForm = document.getElementById("login-form");
if (loginForm) {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("registered") === "true") {
        const successAlert = document.createElement("div");
        successAlert.className = "alert alert-success";
        successAlert.role = "alert";
        successAlert.textContent = "Registration successful, please log in.";
        loginForm.parentElement.insertBefore(successAlert, loginForm);
    }

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const submitBtn = document.getElementById("login-submit");
        const errorAlert = document.getElementById("login-error");
        
        submitBtn.disabled = true;
        errorAlert.classList.add("d-none");
        errorAlert.textContent = "";
        
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;
        
        try {
            const response = await apiFetch("/auth/login", {
                method: "POST",
                body: JSON.stringify({ email, password })
            });
            
            setAccessToken(response.access_token);
            window.location.href = "chat.html";
        } catch (error) {
            errorAlert.textContent = error.message;
            errorAlert.classList.remove("d-none");
            submitBtn.disabled = false;
        }
    });
}

const registerForm = document.getElementById("register-form");
if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const submitBtn = document.getElementById("register-submit");
        const errorAlert = document.getElementById("register-error");
        
        submitBtn.disabled = true;
        errorAlert.classList.add("d-none");
        errorAlert.textContent = "";
        
        const fullName = document.getElementById("register-fullname").value.trim() || null;
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;
        const confirmPassword = document.getElementById("register-confirm-password").value;
        
        if (password.length < 10) {
            errorAlert.textContent = "Password must be at least 10 characters";
            errorAlert.classList.remove("d-none");
            submitBtn.disabled = false;
            return;
        }
        
        if (password !== confirmPassword) {
            errorAlert.textContent = "Passwords do not match";
            errorAlert.classList.remove("d-none");
            submitBtn.disabled = false;
            return;
        }
        
        try {
            await apiFetch("/auth/register", {
                method: "POST",
                body: JSON.stringify({
                    email,
                    password,
                    full_name: fullName
                })
            });
            
            window.location.href = "login.html?registered=true";
        } catch (error) {
            errorAlert.textContent = error.message;
            errorAlert.classList.remove("d-none");
            submitBtn.disabled = false;
        }
    });
}
