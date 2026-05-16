<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useScoringStore } from "./stores/scoring";
import MapView from "./components/MapView.vue";
import WeightPanel from "./components/WeightPanel.vue";
import Dashboard from "./components/Dashboard.vue";
import CompareView from "./components/CompareView.vue";

const store = useScoringStore();
const tab = ref<"map" | "dashboard" | "compare">("map");

onMounted(() => {
  void store.load();
});
</script>

<template>
  <div class="flex flex-col h-full bg-[#0b1220] text-[#e6ecff]">
    <header class="flex items-center justify-between px-6 py-3 border-b border-white/10 bg-[#0e1830]">
      <div>
        <h1 class="text-lg font-semibold tracking-tight">🗺️ 데이터센터 최적입지 — V2</h1>
        <p class="text-xs text-white/50">V1 (2022) 분석을 인터랙티브 웹앱으로 — 가중치를 조절하면 즉시 재계산</p>
      </div>
      <nav class="flex gap-1 bg-white/5 rounded-lg p-1 text-sm">
        <button
          v-for="t in (['map','dashboard','compare'] as const)"
          :key="t"
          class="px-3 py-1.5 rounded-md transition"
          :class="tab === t ? 'bg-white/15 text-white' : 'text-white/60 hover:text-white'"
          @click="tab = t"
        >
          {{ t === 'map' ? '🗺️ 지도' : t === 'dashboard' ? '📊 대시보드' : '🆚 비교' }}
          <span v-if="t === 'compare' && store.compareSet.size > 0" class="ml-1 text-xs px-1.5 py-0.5 bg-blue-500/30 rounded">
            {{ store.compareSet.size }}
          </span>
        </button>
      </nav>
    </header>

    <div v-if="store.error" class="m-6 p-4 bg-red-500/20 border border-red-500/40 rounded text-sm">
      ❌ 데이터 로드 실패: {{ store.error }}
      <p class="mt-2 text-white/70">
        <code>analysis/build_scores.py</code> 를 먼저 실행했는지 확인해줘.
      </p>
    </div>

    <div v-else-if="!store.loaded" class="flex-1 flex items-center justify-center text-white/40">
      데이터 불러오는 중...
    </div>

    <main v-else class="flex-1 flex overflow-hidden">
      <aside class="w-80 shrink-0 border-r border-white/10 overflow-y-auto bg-[#0d1628]">
        <WeightPanel />
      </aside>

      <section class="flex-1 relative overflow-hidden">
        <KeepAlive>
          <MapView v-if="tab === 'map'" key="map" />
        </KeepAlive>
        <Dashboard v-if="tab === 'dashboard'" />
        <CompareView v-if="tab === 'compare'" />
      </section>
    </main>
  </div>
</template>
