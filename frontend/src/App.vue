<script setup>
import { RouterView, RouterLink, useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <header v-if="route.name !== 'login'" class="navbar">
    <div class="navbar-container">
      <!-- Logo/Brand -->
      <div class="navbar-brand">
        <RouterLink to="/home" class="brand-link">
          <div class="brand-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
              <path d="M9 9h6v6H9z" fill="currentColor"/>
              <path d="M9 3v6M15 3v6M3 9h6M3 15h6" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <span class="brand-text">ALL-IN-ONE</span>
        </RouterLink>
      </div>

      <!-- Navigation Links -->
      <nav class="navbar-nav">
        <RouterLink to="/home" class="nav-link" :class="{ active: route.name === 'home' }">
          <svg class="nav-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2"/>
            <polyline points="9,22 9,12 15,12 15,22" stroke="currentColor" stroke-width="2"/>
          </svg>
          <span class="nav-text">Home</span>
        </RouterLink>
        <RouterLink to="/tasks" class="nav-link" :class="{ active: route.name === 'tasks' }">
          <svg class="nav-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 11l3 3 8-8" stroke="currentColor" stroke-width="2"/>
            <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" stroke="currentColor" stroke-width="2"/>
          </svg>
          <span class="nav-text">Tasks</span>
        </RouterLink>
        <RouterLink to="/projects" class="nav-link" :class="{ active: route.name === 'projects' }">
          <svg class="nav-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2"/>
          </svg>
          <span class="nav-text">Projects</span>
        </RouterLink>
        <RouterLink to="/reports" class="nav-link" :class="{ active: route.name === 'reports' }">
          <svg class="nav-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 20V10M12 20V4M6 20v-6" stroke="currentColor" stroke-width="2"/>
          </svg>
          <span class="nav-text">Reports</span>
        </RouterLink>
      </nav>

      <!-- User Profile -->
      <div class="navbar-user">
        <div class="user-avatar">
          {{ getUserInitials() }}
        </div>
        <div class="user-info">
          <div class="user-name">{{ getUserName() }}</div>
          <div class="user-role">{{ getUserRole() }}</div>
        </div>
        <button class="logout-btn" @click="logout" title="Logout">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="2"/>
            <polyline points="16,17 21,12 16,7" stroke="currentColor" stroke-width="2"/>
            <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="2"/>
          </svg>
        </button>
      </div>
    </div>
  </header>

  <RouterView />
</template>

<script>
export default {
  methods: {
    getUserName() {
      return sessionStorage.getItem('employee_name') || 'User'
    },
    getUserRole() {
      return sessionStorage.getItem('role') || 'Staff'
    },
    getUserInitials() {
      const name = this.getUserName()
      return name.split(' ').map(n => n[0]).join('').toUpperCase()
    },
    logout() {
      sessionStorage.clear()
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
/* ========================================
   Professional Navbar Design
   ======================================== */

.navbar {
  background: var(--color-panel);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  backdrop-filter: blur(10px);
  background-color: rgba(255, 255, 255, 0.95);
}

.navbar-container {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-4);
  gap: var(--space-4);
}

/* ========================================
   Brand Section
   ======================================== */

.navbar-brand {
  display: flex;
  align-items: center;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  text-decoration: none;
  color: var(--color-ink);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-lg);
  transition: all var(--transition-fast);
}

.brand-link:hover {
  color: var(--color-mint);
  transform: translateY(-1px);
}

.brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--color-mint), var(--color-mint-dark));
  color: white;
  transition: all var(--transition-fast);
}

.brand-link:hover .brand-icon {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.brand-text {
  font-size: var(--font-size-xl);
  letter-spacing: -0.025em;
  font-weight: var(--font-weight-bold);
}

/* ========================================
   Navigation Links
   ======================================== */

.navbar-nav {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex: 1;
  justify-content: center;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--color-ink-secondary);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  transition: all var(--transition-fast);
  position: relative;
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--color-ink);
  background-color: var(--color-background);
  transform: translateY(-1px);
}

.nav-link.active {
  color: var(--color-mint);
  background-color: var(--color-mint-light);
  font-weight: var(--font-weight-semibold);
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background-color: var(--color-mint);
  border-radius: 1px;
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-text {
  font-size: var(--font-size-sm);
}

/* ========================================
   User Profile Section
   ======================================== */

.navbar-user {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1);
  border-radius: var(--radius-md);
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  transition: all var(--transition-fast);
}

.navbar-user:hover {
  background-color: var(--color-panel);
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-mint), var(--color-mint-dark));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  line-height: 1;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.user-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-ink);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: var(--font-size-xs);
  color: var(--color-ink-muted);
  text-transform: capitalize;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-sm);
  background-color: transparent;
  color: var(--color-ink-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.logout-btn:hover {
  background-color: var(--color-error);
  color: white;
  transform: scale(1.05);
}

/* ========================================
   Responsive Design
   ======================================== */

@media (max-width: 768px) {
  .navbar-container {
    padding: var(--space-2);
    gap: var(--space-2);
  }
  
  .navbar-nav {
    gap: 0;
  }
  
  .nav-text {
    display: none;
  }
  
  .nav-link {
    padding: var(--space-1);
    min-width: 40px;
    justify-content: center;
  }
  
  .user-info {
    display: none;
  }
  
  .navbar-user {
    padding: var(--space-1);
  }
}

@media (max-width: 480px) {
  .brand-text {
    display: none;
  }
  
  .navbar-nav {
    flex: 1;
    justify-content: space-around;
  }
}

/* ========================================
   Focus States for Accessibility
   ======================================== */

.nav-link:focus,
.brand-link:focus,
.logout-btn:focus {
  outline: 2px solid var(--color-mint);
  outline-offset: 2px;
}

/* ========================================
   Active State Enhancements
   ======================================== */

.nav-link.active {
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

.nav-link.active .nav-icon {
  transform: scale(1.05);
}

/* ========================================
   Subtle Animations
   ======================================== */

.nav-link {
  position: relative;
  overflow: hidden;
}

.nav-link::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.1), transparent);
  transition: left var(--transition-normal);
}

.nav-link:hover::before {
  left: 100%;
}

/* ========================================
   Professional Polish
   ======================================== */

.navbar {
  border-bottom: 1px solid var(--color-border);
}

.brand-icon svg {
  transition: all var(--transition-fast);
}

.brand-link:hover .brand-icon svg {
  transform: rotate(5deg);
}

.nav-icon svg {
  transition: all var(--transition-fast);
}

.nav-link:hover .nav-icon svg {
  transform: scale(1.1);
}

.logout-btn svg {
  transition: all var(--transition-fast);
}

.logout-btn:hover svg {
  transform: translateX(2px);
}
</style>