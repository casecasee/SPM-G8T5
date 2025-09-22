<template>
  <div class="login-wrapper">
    <div class="login-container">
      
      <!-- Left: Login form -->
      <div class="login-left">
        <header class="top-nav">
          <div class="logo">ALL-IN-ONE</div>
        </header>

        <div class="login-form">
            <h2 class="title">LOGIN</h2>
            <p class="subtitle">Enter your credentials to continue</p>
          <!-- Login Form -->
          <form @submit.prevent="handleLogin">
            <div class="form-group">
              <label>Email</label>
              <input type="text" v-model="email" placeholder="Enter your email" />
            </div>

            <div class="form-group">
              <label>Password</label>
              <input type="password" v-model="password" placeholder="Enter your password" />
            </div>

            <div v-if="errorMessage" class="error-msg">
              {{ errorMessage }}
            </div>

            <div class="button-wrapper">
              <button type="submit" class="btn-primary">Login</button>
            </div>
          </form>

          <div class="extra-links">
            <a href="#" @click.prevent="handleReset">Forgot password?</a>
          </div>
        </div>
      </div>

      <!-- Right: Image + Text -->
      <div class="login-right">
        <div class="image-text-wrapper">
          <img src="./image.png" alt="Illustration" />
          <p class="image-text">
            Manage tasks. Track deadlines. Collaborate smarter.
          </p>
        </div>
      </div>

    </div>  

    <footer class="footer">
      © 2025 All-In-One. All rights reserved.
    </footer>
  </div>
</template>

<script>
export default {
  name: "LoginPage",
  data() {
    return {
      email: "",
      password: "",
      errorMessage: "",
    };
  },
  methods: {
    async handleLogin() {
      try {
        const response = await fetch("http://localhost:5000/employee", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: this.email, password: this.password }),
        });

        const data = await response.json();

        if (response.ok) {
          sessionStorage.setItem("employee_id", data.employee_id);
          sessionStorage.setItem("role", data.role);
          this.$router.push("/home");
        } else {
          this.errorMessage = data.error || "Login failed";
        }
      } catch (err) {
        this.errorMessage = "Server error. Please try again later.";
      }
    },
    handleReset() {
      alert("Redirect to reset password page (implement later)");
    },
  },
};
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600&family=Inter:wght@400;600&display=swap');

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
               Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
}

.login-wrapper {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  flex-direction: column;
  align-items: center;
  background-color: rgba(176,196,222, 0.5);
}

.login-container {
  display: flex;
  flex: 1;
  width: 90%;
  margin-top: 10px;
  max-width: 1000px;
  min-height: 600px;
  background: rgba(255,255,255,0.85);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}

.login-header {
  text-align: center;
  margin-bottom: 24px; 
}

/* Left: Login form */
.login-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 40px;
}

.top-nav {
  display: flex;
  justify-content: center;
  align-items: center;
}

.top-nav .logo {
  font-family: 'Poppins', sans-serif;
  font-weight: 600;
  font-size: 2rem;
  color: #032A42;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.login-form {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
  align-items: left;
}

.login-form .title {
  font-family: 'Poppins', sans-serif;
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: #032A42;
}

.login-form .subtitle {
  font-size: 1rem;
  color: #4b5563;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  font-size: 0.85rem;
  color: #032A42;
  margin-bottom: 6px;
  display: block;
}

.form-group input {
  font-family: 'Inter', sans-serif;
  width: 100%;
  padding: 10px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.95rem;
  background: #fff;
  color: #032A42;
}

.form-group input:focus {
  outline: none;
  border-color: #F0D486;
  box-shadow: 0 0 0 2px rgba(240,212,134,0.25);
}

.button-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
.btn-primary {
  font-family: 'Inter', sans-serif;
  background: #F0D486;
  color: #032A42;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  padding: 12px;
  width: 60%;
  max-width: 250px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #B3B26F;
  color: #fff;
}

.extra-links {
  margin-top: 16px;
  text-align: center;
}

.extra-links a {
  font-size: 0.85rem;
  color: #032A42;
  text-decoration: none;
}

.extra-links a:hover {
  color: #F0D486;
}

.error-msg {
  color: #d9534f;
  margin-top: 16px;
  font-size: 0.9rem;
}

.footer {
  text-align: center;
  padding: 10px;
  font-size: 0.8rem;
  color: #032A42;
}

/* Right: Image + Text */
.login-right {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(255,255,255,0.85);
  padding: 40px;
}

.image-text-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 350px;
}

.image-text-wrapper img {
  width: 400px; 
  height: auto;
  object-fit: contain;
  margin-bottom: 20px;
  background-color: rgba(255,255,255,0);
}

.image-text {
  font-size: 20px;
  color: #032A42;
  font-weight: 700;
  line-height: 1.4;
}
</style>