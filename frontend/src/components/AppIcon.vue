<!-- src/components/AppIcon.vue -->
<template>
  <div 
    :class="['icon-wrapper', sizeClass]" 
    v-html="svgContent"
    :style="{ color: color }"
  />
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'

export default {
  name: 'AppIcon',
  props: {
    name: {
      type: String,
      required: true
    },
    size: {
      type: String,
      default: 'medium',
      validator: value => ['small', 'medium', 'large', 'xl'].includes(value)
    },
    color: {
      type: String,
      default: '#4a4a4a'
    }
  },
  setup(props) {
    const svgContent = ref('')
    
    const loadIcon = async () => {
      try {
        // Clean the icon name - remove 'fi-rr-' prefix if it exists
        const cleanName = props.name.replace(/^fi-rr-/, '')
        const iconName = `fi-rr-${cleanName}`
        
        // Dynamic import of SVG file
        const iconModule = await import(`@/assets/icons/${iconName}.svg?raw`)
        
        // Get the SVG content and clean it up
        let svg = iconModule.default
        
        // Add viewBox if missing
        if (!svg.includes('viewBox')) {
          svg = svg.replace('<svg', '<svg viewBox="0 0 24 24"')
        }
        
        // Remove all stroke attributes and set fill
        svg = svg.replace(/stroke="[^"]*"/g, '')
        svg = svg.replace(/stroke-width="[^"]*"/g, '')
        svg = svg.replace(/fill="[^"]*"/g, 'fill="#4a4a4a"')
        
        // If no fill attribute, add it
        if (!svg.includes('fill=')) {
          svg = svg.replace('<svg', '<svg fill="#4a4a4a"')
        }
        
        svgContent.value = svg
      } catch (error) {
        console.warn(`Icon "${props.name}" not found:`, error)
        // Simple fallback
        svgContent.value = `
          <svg viewBox="0 0 24 24" fill="#4a4a4a">
            <circle cx="12" cy="12" r="2"/>
          </svg>
        `
      }
    }
    
    onMounted(loadIcon)
    watch(() => props.name, loadIcon)
    
    const sizeClass = computed(() => `icon-${props.size}`)
    
    return {
      svgContent,
      sizeClass
    }
  }
}
</script>

<style scoped>
.icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: inherit;
}

.icon-wrapper :deep(svg) {
  width: 1.2rem;
  height: 1.2rem;
  color: inherit;
}

.icon-small {
  width: 1rem;
  height: 1rem;
}

.icon-medium {
  width: 1.5rem;
  height: 1.5rem;
}

.icon-large {
  width: 2rem;
  height: 2rem;
}

.icon-xl {
  width: 3rem;
  height: 3rem;
}
</style>