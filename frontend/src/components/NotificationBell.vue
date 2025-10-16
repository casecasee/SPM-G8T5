<template>
  <div class="notification-bell">
    <!-- Bell Icon Button -->
    <button @click="toggleDropdown" class="bell-button">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25-2 7-2 7h14s-2-1.75-2-7c0-3.87-3.13-7-7-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9 21c0 1.66 1.34 3 3 3s3-1.34 3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
    </button>

    <!-- Dropdown -->
    <div v-if="showDropdown" class="notification-dropdown">
      <div class="notification-header">
        <h3>Notifications</h3>
        <button @click="markAllAsRead" class="mark-all-read">Mark all as read</button>
      </div>

      <div class="notification-list">
        <!-- Loading State -->
        <div v-if="loading" class="loading">
          <p>Loading notifications...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="notifications.length === 0" class="empty-state">
          <p>No notifications yet</p>
        </div>

        <!-- Notification Items -->
        <div
          v-for="notif in notifications"
          :key="notif.id"
          :class="['notification-item', { unread: !notif.is_read }]"
          @click="handleNotificationClick(notif)"
        >
          <div class="notification-icon">
            <i :class="getNotificationIcon(notif.type)"></i>
          </div>
          <div class="notification-content">
            <strong>{{ notif.title }}</strong>
            <p>{{ notif.message }}</p>
            <small>{{ formatTime(notif.created_at) }}</small>
          </div>
        </div>
      </div>

      <div class="notification-footer">
        <button @click="goToSettings" class="settings-link">
          <i class="fas fa-cog"></i> Notification Settings
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import io from 'socket.io-client';

export default {
  name: 'NotificationBell',
  data() {
    return {
      showDropdown: false,
      notifications: [],
      unreadCount: 0,
      loading: false,
      socket: null,
    };
  },
  mounted() {
    this.fetchNotifications();
    this.fetchUnreadCount();
    this.connectWebSocket();
  },
  beforeUnmount() {
    if (this.socket) {
      this.socket.disconnect();
    }
  },
  methods: {
async fetchNotifications() {
  this.loading = true;
  try {
    const employeeId = sessionStorage.getItem('employee_id');
    const response = await fetch('http://localhost:5003/api/notifications?per_page=10', {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Employee-Id': employeeId
      }
    });

    if (response.ok) {
      const data = await response.json();
      this.notifications = data.notifications || [];
      console.log('✅ Fetched notifications:', this.notifications.length);
    } else {
      console.error('❌ Failed to fetch notifications:', response.status);
    }
  } catch (error) {
    console.error('❌ Error fetching notifications:', error);
  } finally {
    this.loading = false;
  }
},

async fetchUnreadCount() {
  try {
    const employeeId = sessionStorage.getItem('employee_id');
    const response = await fetch('http://localhost:5003/api/notifications/unread', {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Employee-Id': employeeId
      }
    });

    if (response.ok) {
      const data = await response.json();
      this.unreadCount = data.unread_count || 0;
      console.log('✅ Unread count:', this.unreadCount);
    }
  } catch (error) {
    console.error('❌ Error fetching unread count:', error);
  }
},

    connectWebSocket() {
      const employeeId = sessionStorage.getItem('employee_id');
      
      if (!employeeId) {
        console.error('No employee_id found');
        return;
      }

      console.log('Connecting to WebSocket with employee_id:', employeeId);

      // Connect to notification service - CORRECTED URL
      this.socket = io('http://localhost:5003', {
        query: { employee_id: employeeId },
        transports: ['websocket', 'polling'],  // Try both transports
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
      });

      this.socket.on('connect', () => {
        console.log('✅ Connected to notifications WebSocket');
      });

      this.socket.on('connected', (data) => {
        console.log('Connected to notifications:', data.message);
      });

      this.socket.on('new_notification', (notification) => {
        console.log('🔔 New notification received:', notification);
        
        // Add to notifications list
        this.notifications.unshift(notification);
        
        // Increment unread count
        this.unreadCount++;
        
        // Show toast notification
        this.showToast(notification);
      });

      this.socket.on('connect_error', (error) => {
        console.error('❌ WebSocket connection error:', error);
      });

      this.socket.on('error', (error) => {
        console.error('❌ WebSocket error:', error);
      });

      this.socket.on('disconnect', () => {
        console.log('⚠️ Disconnected from notifications');
      });
    },

    showToast(notification) {
      // Simple toast notification (you can use a library like vue-toastification)
      const toast = document.createElement('div');
      toast.className = 'toast-notification';
      toast.innerHTML = `
        <strong>${notification.title}</strong>
        <p>${notification.message}</p>
      `;
      document.body.appendChild(toast);

      setTimeout(() => {
        toast.classList.add('show');
      }, 100);

      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
      }, 4000);
    },

    toggleDropdown() {
      this.showDropdown = !this.showDropdown;
      if (this.showDropdown) {
        this.fetchNotifications();
      }
    },

    async handleNotificationClick(notification) {
      // Mark as read
      if (!notification.is_read) {
        await this.markAsRead(notification.id);
      }

      // Navigate to related task/project
      if (notification.related_task_id) {
        this.$router.push(`/tasks/${notification.related_task_id}`);
      } else if (notification.related_project_id) {
        this.$router.push(`/projects/${notification.related_project_id}`);
      }

      this.showDropdown = false;
    },

    async markAsRead(notificationId) {
      try {
        const employeeId = sessionStorage.getItem('employee_id');
        const response = await fetch(`http://localhost:5003/api/notifications/${notificationId}/read`, {
          method: 'PATCH',
          credentials: 'include',
          headers: {
            'X-Employee-Id': employeeId
          }
        });

        if (response.ok) {
          // Update local state
          const notif = this.notifications.find(n => n.id === notificationId);
          if (notif) {
            notif.is_read = true;
            this.unreadCount = Math.max(0, this.unreadCount - 1);
          }
        }
      } catch (error) {
        console.error('Failed to mark notification as read:', error);
      }
    },

    async markAllAsRead() {
      try {
        const employeeId = sessionStorage.getItem('employee_id');
        const response = await fetch('http://localhost:5003/api/notifications/read-all', {
          method: 'PATCH',
          credentials: 'include',
          headers: {
            'X-Employee-Id': employeeId
          }
        });

        if (response.ok) {
          // Update local state
          this.notifications.forEach(n => n.is_read = true);
          this.unreadCount = 0;
        }
      } catch (error) {
        console.error('Failed to mark all as read:', error);
      }
    },

    goToSettings() {
      this.$router.push('/settings/notifications');
      this.showDropdown = false;
    },

    getNotificationIcon(type) {
      const icons = {
        'deadline_7_days': 'fas fa-calendar-alt',
        'deadline_3_days': 'fas fa-calendar-exclamation',
        'deadline_1_day': 'fas fa-clock',
        'overdue_task': 'fas fa-exclamation-triangle',
        'task_assigned': 'fas fa-user-plus',
        'task_status_updated': 'fas fa-exchange-alt',
        'due_date_changed': 'fas fa-calendar-edit',
        'collaborators_changed': 'fas fa-users',
        'priority_updated': 'fas fa-flag',
        'description_updated': 'fas fa-file-text',
        'name_updated': 'fas fa-tag',
        'comments_updated': 'fas fa-comments',
        'mention': 'fas fa-at'
      };
      return icons[type] || 'fas fa-bell';
    },

    formatTime(timestamp) {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      
      return date.toLocaleDateString();
    }
  }
};
</script>

<style scoped>
.notification-bell {
  position: relative;
}

.bell-button {
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  color: #032A42;
  padding: 8px;
  transition: color 0.2s;
}

.bell-button:hover {
  color: #337587;
}

.badge {
  position: absolute;
  bottom: 0;
  right: 0;
  background: #e74c3c;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
}

.notification-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 380px;
  max-height: 500px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  margin-top: 8px;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.notification-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #032A42;
}

.mark-all-read {
  background: none;
  border: none;
  color: #337587;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.mark-all-read:hover {
  background: #f3f4f6;
}

.notification-list {
  overflow-y: auto;
  max-height: 400px;
}

.loading, .empty-state {
  padding: 32px;
  text-align: center;
  color: #6b7280;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: background 0.2s;
}

.notification-item:hover {
  background: #f9fafb;
}

.notification-item.unread {
  background: #eff6ff;
}

.notification-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  background: #337587;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-content strong {
  display: block;
  font-size: 0.9rem;
  color: #032A42;
  margin-bottom: 4px;
}

.notification-content p {
  margin: 0 0 4px 0;
  font-size: 0.85rem;
  color: #4b5563;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-content small {
  font-size: 0.75rem;
  color: #9ca3af;
}

.notification-footer {
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
}

.settings-link {
  width: 100%;
  background: none;
  border: none;
  color: #337587;
  cursor: pointer;
  padding: 8px;
  text-align: center;
  font-size: 0.9rem;
  border-radius: 4px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.settings-link:hover {
  background: #f3f4f6;
}

/* Toast Notification */
.toast-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 300px;
  max-width: 400px;
  z-index: 9999;
  transform: translateX(450px);
  transition: transform 0.3s ease;
}

.toast-notification.show {
  transform: translateX(0);
}

.toast-notification strong {
  display: block;
  color: #032A42;
  margin-bottom: 4px;
}

.toast-notification p {
  margin: 0;
  color: #4b5563;
  font-size: 0.9rem;
}
</style>