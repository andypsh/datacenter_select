<script setup lang="ts">
import { useScoringStore } from "../stores/scoring";

const store = useScoringStore();
</script>

<template>
  <div class="p-5 space-y-5">
    <div>
      <h2 class="text-sm font-semibold text-white/80 mb-1">가중치 조절</h2>
      <p class="text-xs text-white/40">슬라이더를 움직이면 즉시 점수와 지도가 갱신돼.</p>
    </div>

    <div class="space-y-4">
      <div v-for="f in store.factors" :key="f.key" class="space-y-1.5">
        <div class="flex justify-between items-baseline">
          <label class="text-sm font-medium">
            {{ f.label }}
            <span class="text-white/40 text-xs ml-1">{{ f.direction === 'lower_is_better' ? '↓ 좋음' : '↑ 좋음' }}</span>
          </label>
          <span class="text-sm tabular-nums font-mono text-blue-300">
            {{ Math.round((store.weights[f.key] / store.weightSum) * 100) }}%
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="50"
          step="1"
          :value="store.weights[f.key]"
          @input="store.setWeight(f.key, Number(($event.target as HTMLInputElement).value))"
          class="w-full accent-blue-400"
        />
        <p class="text-xs text-white/40">{{ f.desc }}</p>
      </div>
    </div>

    <button
      @click="store.resetWeights()"
      class="w-full px-3 py-2 text-sm bg-white/5 hover:bg-white/10 rounded-md transition border border-white/10"
    >
      기본값으로 초기화
    </button>

    <div class="pt-4 border-t border-white/10">
      <h3 class="text-sm font-semibold text-white/80 mb-2">Top 10 후보지</h3>
      <ol class="space-y-1">
        <li
          v-for="(r, i) in store.topN"
          :key="r.name"
          class="flex items-center justify-between text-sm py-1.5 px-2 rounded hover:bg-white/5 cursor-pointer transition"
          :class="store.compareSet.has(r.name) ? 'bg-blue-500/15 ring-1 ring-blue-400/40' : ''"
          @click="store.toggleCompare(r.name)"
          :title="store.compareSet.has(r.name) ? '비교에서 제거' : '비교에 추가 (최대 3개)'"
        >
          <span class="flex items-center gap-2">
            <span class="text-white/40 text-xs w-6 text-right tabular-nums">{{ i + 1 }}.</span>
            <span>{{ r.name }}</span>
          </span>
          <span class="text-blue-300 text-xs tabular-nums font-mono">{{ r.score.toFixed(3) }}</span>
        </li>
      </ol>
      <p class="text-xs text-white/30 mt-2">클릭해서 비교 모드에 추가 (최대 3개)</p>
    </div>
  </div>
</template>
