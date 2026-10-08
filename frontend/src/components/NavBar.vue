<template>
  <header ref="root" class="navbar" :class="{ 'navbar--collapsed': collapsed || hideLargeTitle }">
    <div class="navbar-bar">
      <div class="navbar-leading">
        <button v-if="back" type="button" class="navbar-back" @click="goBack">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M15 5l-7 7 7 7" />
          </svg>
          <span>返回</span>
        </button>
      </div>
      <div class="navbar-compact-title">{{ compactTitle || title }}</div>
      <div class="navbar-trailing">
        <slot name="right" />
      </div>
    </div>
    <h1 class="navbar-large-title">{{ title }}</h1>
  </header>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps<{
  title: string
  compactTitle?: string
  back?: boolean
  /** 页面自带大标题展示（如海报头部卡片）时，隐藏导航栏大标题，仅保留紧凑标题 */
  hideLargeTitle?: boolean
}>()

const COLLAPSE_THRESHOLD = 40

const router = useRouter()
const root = ref<HTMLElement | null>(null)
const collapsed = ref(false)

let scrollTarget: HTMLElement | Window = window

function onScroll() {
  const scrollTop = scrollTarget instanceof HTMLElement ? scrollTarget.scrollTop : window.scrollY
  collapsed.value = scrollTop > COLLAPSE_THRESHOLD
}

function findScrollTarget(): HTMLElement | Window {
  let el = root.value?.parentElement ?? null
  while (el) {
    const { overflowY } = window.getComputedStyle(el)
    if (overflowY === 'auto' || overflowY === 'scroll') {
      return el
    }
    el = el.parentElement
  }
  return window
}

function goBack() {
  router.back()
}

onMounted(() => {
  scrollTarget = findScrollTarget()
  scrollTarget.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})

onBeforeUnmount(() => {
  scrollTarget.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  padding-top: calc(env(safe-area-inset-top) + 6px);
  background: transparent;
  border-bottom: 0.5px solid transparent;
  -webkit-backdrop-filter: blur(15px) saturate(180%);
  backdrop-filter: blur(15px) saturate(180%);
  transition:
    background-color 240ms ease,
    border-color 240ms ease;
}

.navbar--collapsed {
  background: var(--blur-bg);
  border-bottom-color: var(--separator);
}

.navbar-bar {
  display: grid;
  grid-template-columns: minmax(56px, 1fr) auto minmax(56px, 1fr);
  align-items: center;
  height: 44px;
  padding: 0 8px;
}

.navbar-leading {
  justify-self: start;
  min-width: 0;
}

.navbar-trailing {
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.navbar-back {
  display: inline-flex;
  align-items: center;
  gap: 1px;
  height: 44px;
  padding: 0 8px 0 2px;
  margin-left: 8px;
  color: var(--accent);
  font-size: 17px;
  line-height: 1;
}

.navbar-back svg {
  width: 13px;
  height: 13px;
  margin-left: -6px;
}

.navbar-compact-title {
  max-width: 60vw;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 17px;
  font-weight: 600;
  opacity: 0;
  transition: opacity 240ms ease;
}

.navbar--collapsed .navbar-compact-title {
  opacity: 1;
}

.navbar-large-title {
  margin: 0;
  padding: 0 16px 6px;
  max-height: 44px;
  overflow: hidden;
  font-size: 34px;
  font-weight: 700;
  line-height: 44px;
  letter-spacing: 0.2px;
  transition:
    max-height 240ms ease,
    padding 240ms ease,
    opacity 240ms ease;
}

.navbar--collapsed .navbar-large-title {
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  opacity: 0;
}
</style>
