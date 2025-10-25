<template>
  <div class="notification-settings">
    <div class="settings-header">
      <h2>Notification Settings</h2>
      <button @click="goBack" class="back-button">
        <i class="fas fa-arrow-left"></i> Back
      </button>
    </div>

    <div class="settings-content">
      <!-- Deadline Reminders Section -->
      <div class="settings-section">
        <h3>Deadline Reminders</h3>
        <p class="section-description">
          Choose how many days before a deadline you want to be notified.
        </p>
        
        <div class="reminder-days-section">
          <label class="section-label">Reminder Days:</label>
          
          <!-- Base Days Display (always visible) -->
          <div class="base-days-display">
            <label class="base-days-label">Base Days (always included):</label>
            <div class="base-days-pills">
              <span v-for="day in baseDays" :key="day" class="base-day-pill">
                {{ day }} day{{ day > 1 ? 's' : '' }}
              </span>
            </div>
          </div>

          <!-- Additional Days Input (only in custom mode) -->
          <div v-if="isCustomMode" class="additional-days-section">
            <label class="additional-days-label">Additional Days:</label>
            <div class="additional-days-input">
              <input 
                v-model="additionalDaysInput" 
                type="text" 
                placeholder="e.g., 14,10,5"
                class="days-input additional-input"
                @input="validateAdditionalDays"
              />
              <button @click="addAdditionalDays" class="add-days-button" :disabled="!isValidAdditionalInput">
                <i class="fas fa-plus"></i> Add Days
              </button>
            </div>
            <small class="input-help">
              Enter comma-separated numbers to add more reminder days (e.g., 14,10,5)
            </small>
          </div>

          <!-- Regular Input (when not in custom mode) -->
          <div v-else class="regular-days-input">
            <input 
              v-model="reminderDaysInput" 
              type="text" 
              placeholder="e.g., 7,3,1 or 14,7,3,1"
              class="days-input"
              @input="validateDaysInput"
            />
            <small class="input-help">
              Enter comma-separated numbers (e.g., 7,3,1 for 7 days, 3 days, and 1 day before deadline)
            </small>
          </div>

          <!-- Added Days Display (only show additional days, not base days) -->
          <div v-if="isCustomMode && additionalDays.length > 0" class="added-days-display">
            <label class="added-days-label">Added Days:</label>
            <div class="added-days-pills">
              <span v-for="day in additionalDays" :key="day" class="added-day-pill">
                {{ day }} day{{ day > 1 ? 's' : '' }}
              </span>
            </div>
          </div>
          
          <!-- Quick Presets -->
          <div class="preset-buttons">
            <button 
              v-for="preset in presets" 
              :key="preset.name"
              @click="applyPreset(preset.days)"
              class="preset-button"
              :class="{ active: isPresetActive(preset.days) }"
            >
              {{ preset.name }}
            </button>
          </div>
        
        </div>
      </div>

      <!-- Save Button -->
      <div class="save-section">
        <button 
          @click="saveSettings" 
          class="save-button"
          :disabled="!isValidInput || saving"
        >
          <i v-if="saving" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-save"></i>
          {{ saving ? 'Saving...' : 'Save Settings' }}
        </button>
        
        <div v-if="saveMessage" class="save-message" :class="{ success: saveSuccess, error: !saveSuccess }">
          {{ saveMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NotificationSettings',
  data() {
    return {
      preferences: {
        deadline_reminders: true,
        task_status_updates: true,
        due_date_changes: true,
        deadline_reminder_days: "7,3,1"
      },
      reminderDaysInput: "7,3,1",
      additionalDaysInput: "",
      parsedDays: [7, 3, 1],
      additionalDays: [],
      baseDays: [7, 3, 1], // Base days that cannot be removed
      isCustomMode: false,
      saving: false,
      saveMessage: '',
      saveSuccess: false,
      presets: [
        { name: 'Default (7,3,1)', days: [7, 3, 1] },
        { name: 'Custom', days: [] }
      ]
    }
  },
  computed: {
    isValidInput() {
      return this.parsedDays.length > 0 && this.parsedDays.every(day => day > 0 && day <= 365)
    },
    isValidAdditionalInput() {
      if (!this.additionalDaysInput.trim()) return false
      const days = this.additionalDaysInput.split(',').map(d => parseInt(d.trim())).filter(d => !isNaN(d) && d > 0 && d <= 365)
      return days.length > 0
    },
    combinedDays() {
      if (!this.isCustomMode) return this.parsedDays
      const allDays = [...new Set([...this.baseDays, ...this.additionalDays])]
      return allDays.sort((a, b) => b - a)
    }
  },
  async mounted() {
    await this.loadPreferences()
  },
  methods: {
    async loadPreferences() {
      try {
        const employeeId = sessionStorage.getItem('employee_id')
        const response = await fetch('http://localhost:5003/api/preferences', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'X-Employee-Id': employeeId
          }
        })

        if (response.ok) {
          const data = await response.json()
          this.preferences = data
          
          // Parse saved reminder days
          const savedDaysStr = data.deadline_reminder_days || "7,3,1"
          const savedDays = savedDaysStr.split(',').map(d => parseInt(d.trim())).filter(d => !isNaN(d) && d > 0).sort((a, b) => b - a)
          
          // Check if saved days match the default preset
          const defaultDays = [7, 3, 1]
          const matchesDefault = JSON.stringify(savedDays) === JSON.stringify(defaultDays)
          
          if (matchesDefault) {
            // Use default preset
            this.isCustomMode = false
            this.reminderDaysInput = "7,3,1"
            this.additionalDaysInput = ""
            this.additionalDays = []
            this.parseDaysInput()
          } else {
            // Switch to custom mode and extract additional days
            this.isCustomMode = true
            this.reminderDaysInput = savedDaysStr
            
            // Extract additional days (days that are not in base days)
            const additionalDays = savedDays.filter(day => !this.baseDays.includes(day))
            this.additionalDays = additionalDays
            this.additionalDaysInput = additionalDays.join(',')
            
            // Set parsed days to saved days for validation
            this.parsedDays = savedDays
          }
        }
      } catch (error) {
        console.error('Error loading preferences:', error)
        this.showMessage('Error loading settings', false)
      }
    },

    validateDaysInput() {
      this.parseDaysInput()
    },

    parseDaysInput() {
      try {
        const inputDays = this.reminderDaysInput
          .split(',')
          .map(d => parseInt(d.trim()))
          .filter(d => !isNaN(d) && d > 0)
        
        this.parsedDays = inputDays.sort((a, b) => b - a) // Sort descending (largest first)
      } catch (error) {
        this.parsedDays = []
      }
    },

    validateAdditionalDays() {
      // This method is called on input change for additional days
      // Validation happens in the computed property isValidAdditionalInput
    },

    addAdditionalDays() {
      if (!this.isValidAdditionalInput) return
      
      const newDays = this.additionalDaysInput
        .split(',')
        .map(d => parseInt(d.trim()))
        .filter(d => !isNaN(d) && d > 0 && d <= 365)
      
      // Add new days to existing additional days
      this.additionalDays = [...new Set([...this.additionalDays, ...newDays])].sort((a, b) => b - a)
      
      // Clear the input
      this.additionalDaysInput = ""
      
      // Update the main reminder days input for saving
      this.updateReminderDaysForSaving()
    },

    updateReminderDaysForSaving() {
      if (this.isCustomMode) {
        this.reminderDaysInput = this.combinedDays.join(',')
      }
    },

    applyPreset(days) {
      if (days.length === 0) {
        // Custom preset - enable custom mode
        this.isCustomMode = true
        this.additionalDaysInput = ""
        this.additionalDays = []
        this.updateReminderDaysForSaving()
        return
      }
      
      // Regular preset - disable custom mode and set the days
      this.isCustomMode = false
      this.reminderDaysInput = days.join(',')
      this.additionalDaysInput = ""
      this.additionalDays = []
      this.parseDaysInput()
    },

    isPresetActive(days) {
      if (days.length === 0) {
        // Custom preset is active when in custom mode
        return this.isCustomMode
      }
      // Regular preset is active when not in custom mode and days match
      return !this.isCustomMode && JSON.stringify(days.sort((a, b) => b - a)) === JSON.stringify(this.parsedDays.sort((a, b) => b - a))
    },

    async saveSettings() {
      if (!this.isValidInput) {
        this.showMessage('Please enter valid reminder days', false)
        return
      }

      this.saving = true
      this.saveMessage = ''

      try {
        const employeeId = sessionStorage.getItem('employee_id')
        
        // Use combined days if in custom mode, otherwise use parsed days
        const daysToSave = this.isCustomMode ? this.combinedDays : this.parsedDays
        
        const payload = {
          ...this.preferences,
          deadline_reminder_days: daysToSave.join(',')
        }

        const response = await fetch('http://localhost:5003/api/preferences', {
          method: 'PUT',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'X-Employee-Id': employeeId
          },
          body: JSON.stringify(payload)
        })

        if (response.ok) {
          this.showMessage('Settings saved successfully!', true)
        } else {
          this.showMessage('Error saving settings', false)
        }
      } catch (error) {
        console.error('Error saving preferences:', error)
        this.showMessage('Error saving settings', false)
      } finally {
        this.saving = false
      }
    },

    showMessage(message, success) {
      this.saveMessage = message
      this.saveSuccess = success
      setTimeout(() => {
        this.saveMessage = ''
      }, 3000)
    },

    goBack() {
      this.$router.go(-1)
    }
  }
}
</script>

<style scoped>
.notification-settings {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
}

.settings-header h2 {
  margin: 0;
  color: #032A42;
  font-size: 1.8rem;
}

.back-button {
  background: none;
  border: 1px solid #d1d5db;
  color: #6b7280;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-button:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.settings-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.settings-section h3 {
  margin: 0 0 8px 0;
  color: #032A42;
  font-size: 1.2rem;
}

.section-description {
  color: #6b7280;
  margin: 0 0 20px 0;
  font-size: 0.9rem;
}

.reminder-days-input {
  margin-bottom: 20px;
}

.section-label {
  display: block;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.days-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.days-input:focus {
  outline: none;
  border-color: #337587;
}

.base-days-display {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f0f8fa;
  border: 1px solid #a7d9ed;
  border-radius: 8px;
}

.base-days-label {
  display: block;
  font-weight: 600;
  color: #032A42;
  margin-bottom: 10px;
  font-size: 0.9rem;
}

.base-days-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.base-day-pill {
  background-color: #337587;
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.additional-days-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff8e1;
  border: 1px solid #ffcc02;
  border-radius: 8px;
}

.additional-days-label {
  display: block;
  font-weight: 600;
  color: #e65100;
  margin-bottom: 10px;
  font-size: 0.9rem;
}

.additional-days-input {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
}

.additional-input {
  flex: 1;
}

.add-days-button {
  background-color: #ff9800;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.add-days-button:hover:not(:disabled) {
  background-color: #f57c00;
}

.add-days-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.added-days-display {
  margin-top: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #e8f5e8;
  border: 1px solid #4caf50;
  border-radius: 8px;
}

.added-days-label {
  display: block;
  font-weight: 600;
  color: #2e7d32;
  margin-bottom: 10px;
  font-size: 0.9rem;
}

.added-days-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.added-day-pill {
  background-color: #4caf50;
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.regular-days-input {
  margin-bottom: 20px;
}

.input-help {
  display: block;
  color: #6b7280;
  margin-top: 4px;
  font-size: 0.85rem;
}

.preset-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.preset-button {
  background: white;
  border: 2px solid #d1d5db;
  color: #6b7280;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.preset-button:hover {
  border-color: #9ca3af;
  background: #f9fafb;
}

.preset-button.active {
  background: #337587;
  border-color: #337587;
  color: white;
}


.notification-toggle {
  margin-bottom: 20px;
}

.toggle-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-bottom: 4px;
}

.toggle-input {
  margin-right: 12px;
  transform: scale(1.2);
}

.toggle-text {
  font-weight: 600;
  color: #374151;
}

.toggle-description {
  color: #6b7280;
  margin: 0 0 0 28px;
  font-size: 0.9rem;
}

.save-section {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.save-button {
  background: #337587;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.save-button:hover:not(:disabled) {
  background: #2c5f6f;
}

.save-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.save-message {
  margin-top: 12px;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
}

.save-message.success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.save-message.error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}
</style>