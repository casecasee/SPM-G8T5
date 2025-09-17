
<!-- src/App.vue -->
<script setup>
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <header class="site-nav">
    <RouterLink to="/">Home</RouterLink>
    <RouterLink to="/tasks">Tasks</RouterLink>
    <RouterLink to="/reports">Reports</RouterLink>
  </header>

  <RouterView />
</template>

<style scoped>
.site-nav {
  display: flex;
  gap: 1rem;
  padding: 1rem 2rem;
  border-bottom: 1px solid #2a2a2a;
}
a { text-decoration: none; }
a.router-link-exact-active { font-weight: 700; }
</style>

