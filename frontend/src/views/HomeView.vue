<!-- src/views/HomeView.vue -->
<template>
  <main class="home">
    <h1>Welcome to SPM</h1>
    <p>Plan tasks, track deadlines, and ship smarter.</p>
    <p>
      <RouterLink to="/tasks">Go to Tasks</RouterLink>
      &nbsp;•&nbsp;
      <RouterLink to="/reports">View Reports</RouterLink>
    </p>
  </main>
</template>

<script setup></script>

<style scoped>
.home {
  max-width: 960px;
  margin: 3rem auto;
  padding: 0 1rem;
  text-align: center;
}
</style>
