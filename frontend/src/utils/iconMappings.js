// src/utils/iconMappings.js
// Map semantic names to your fi-rr icon names

export const iconMappings = {
  // App Navigation
  'dashboard': 'apps',
  'transactions': 'list-check',
  'categories': 'apps-sort',
  'timeline': 'time-half-past',
  'settings': 'settings-sliders',
  
  // User Actions
  'user': 'user',
  'login': 'user',
  'logout': 'power',
  'profile': 'user',
  
  // File Operations
  'upload': 'upload',
  'download': 'download',
  'file': 'file',
  'folder': 'folder',
  
  // Financial
  'money': 'dollar',
  'bank': 'bank',
  'credit-card': 'credit-card',
  'wallet': 'wallet',
  'chart': 'chart-line-up',
  'calculator': 'calculator',
  
  // Actions
  'add': 'plus',
  'edit': 'edit',
  'delete': 'trash',
  'save': 'disk',
  'search': 'search',
  'filter': 'filter',
  
  // Status
  'success': 'check',
  'error': 'cross',
  'warning': 'exclamation',
  'info': 'info',
  
  // Navigation
  'back': 'arrow-left',
  'forward': 'arrow-right',
  'up': 'arrow-up',
  'down': 'arrow-down',
  'close': 'cross',
  'menu': 'menu-burger',
  
  // Add more mappings as needed...
}

// Helper function to get the correct icon name
export const getIconName = (semanticName) => {
  return iconMappings[semanticName] || semanticName
}