<template>
  <div class="login-container d-flex justify-content-center align-items-center">
    <div class="login-card shadow p-4">
      <h2 class="title">Work Management Tool</h2>
      <h4 class="subtitle mb-4">Login to your account</h4>

      <form @submit.prevent="handleLogin">
        <div class="mb-3">
          <label for="email" class="form-label">Email</label>
          <input
            type="text"
            id="email"
            v-model="email"
            class="form-control"
            placeholder="Enter your email"
          />
        </div>

        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input
            type="password"
            id="password"
            v-model="password"
            class="form-control"
            placeholder="Enter your password"
          />
        </div>

        <button type="submit" class="btn btn-primary w-100">Login</button>
      </form>

      <div class="mt-3 text-center">
        <a href="#" @click.prevent="handleReset">Forgot Password?</a>
      </div>

      <div v-if="errorMessage" class="error-msg">
        {{ errorMessage }}
      </div>
    </div>
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
        // Store inputs into sessionStorage
        sessionStorage.setItem("email", this.email);
        sessionStorage.setItem("password", this.password);

        const response = await fetch("http://localhost:5000/login", {
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

<style scoped>
/* Ensure full-screen coverage */
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
  background-color: #032A42;
}

.login-container {
  min-height: 100%;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: transparent;
}

.login-card {
  background: #F0F0DC;
  border-radius: 12px;
  max-width: 400px;
  width: 90%;
  text-align: center;
  padding: 2rem;
  box-shadow: 0 8px 20px rgba(0,0,0,0.2);
  transition: transform 0.2s ease-in-out;
}

.login-card:hover {
  transform: translateY(-4px);
}

.title {
  color: #032A42;
  margin-bottom: 0.25rem;
  font-weight: 700;
}

.subtitle {
  color: #032A42;
  font-weight: 400;
  margin-bottom: 1.5rem;
}

.form-control {
  background: #F0F0DC;
  border: 1px solid #B3B26F;
  border-radius: 6px;
  padding: 0.5rem;
}

.form-control:focus {
  border-color: #F0D486;
  box-shadow: 0 0 0 0.2rem rgba(240, 212, 134, 0.25);
  outline: none;
}

.btn-primary {
  background: #F0D486;
  color: #032A42;
  font-weight: 600;
  border: none;
  border-radius: 6px;
}

.btn-primary:hover {
  background: #B3B26F;
  color: #F0F0DC;
}

a {
  color: #032A42;
  text-decoration: none;
}

a:hover {
  color: #F0D486;
  text-decoration: underline;
}

.error-msg {
  color: #d9534f;
  margin-top: 1rem;
  font-weight: 500;
}

@media (max-width: 576px) {
  .login-card {
    padding: 1.5rem;
    border-radius: 10px;
  }

  .title {
    font-size: 1.5rem;
  }

  .subtitle {
    font-size: 1rem;
  }
}
</style>
