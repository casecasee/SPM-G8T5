
<script setup>
import { RouterView, RouterLink, useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <header v-if="route.name !== 'login'" class="site-nav">
    <RouterLink to="/home">Home</RouterLink>
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
