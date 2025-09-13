<template>
  <div class="tab-content">
    <!-- System Status -->
    <div class="container">
      <div class="text-medium section-header">System Status</div>
      <div class="grid grid-auto">
        <div class="card text-center">
          <div class="text-small text-muted">Authentication</div>
          <div class="text-medium">{{ user ? 'Signed In' : 'Anonymous' }}</div>
          <div class="text-small text-light">{{ user ? user.email : 'Not authenticated' }}</div>
        </div>
        <div class="card text-center">
          <div class="text-small text-muted">Backend Status</div>
          <div class="text-medium">{{ backendStatus }}</div>
          <div class="text-small text-light">API Connection</div>
        </div>
        <div class="card text-center">
          <div class="text-small text-muted">Phase Progress</div>
          <div class="text-medium">{{ phase }}</div>
          <div class="text-small text-light">Current Development Phase</div>
        </div>
      </div>
    </div>

    <!-- User Profile -->
    <div class="container">
      <div class="text-medium section-header">User Profile</div>
      <div v-if="user">
        <div class="text-small"><strong>Email:</strong> {{ user.email }}</div>
        <div class="text-small"><strong>UID:</strong> {{ user.uid.substring(0, 16) }}...</div>
        <div class="text-small"><strong>Display Name:</strong> {{ user.displayName || 'Not set' }}</div>
        <button class="btn" @click="$emit('logout')">Sign Out</button>
      </div>
      <div v-else>
        <div class="text-small text-light">Sign in to access personalized features and secure data storage.</div>
        <button class="btn" @click="$emit('logout')">Sign In</button>
      </div>
    </div>

    <!-- Data Management -->
    <div class="container">
      <div class="text-medium section-header">Data Management</div>
      <div class="flex flex-gap flex-wrap">
        <button class="btn" @click="$emit('show-tab', 'transactions')">Import Data</button>
        <button class="btn">Export Data</button>
        <button class="btn">Clear All Data</button>
        <button class="btn">Reset Categories</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SettingsTab',
  props: {
    user: Object,
    backendStatus: {
      type: String,
      default: 'Checking...'
    },
    phase: {
      type: String,
      default: 'Phase 1'
    }
  },
  emits: ['logout', 'show-tab']
}
</script>