<script setup lang="ts">
import { useScoringStore } from "../stores/scoring";

const store = useScoringStore();
</script>

<template>
  <div class="p-5 space-y-5">
    <div>
      <h2 class="text-sm font-semibold text-white/80 mb-2">시나리오 프리셋</h2>
      <div class="grid grid-cols-1 gap-1.5">
        <button
          v-for="p in store.presets"
          :key="p.id"
          @click="store.applyPreset(p.id)"
          class="text-left text-xs px-3 py-2 rounded-md transition border"
          :class="store.activePresetId === p.id
            ? 'bg-blue-500/20 border-blue-400/50 text-white'
            : 'bg-white/5 border-white/10 hover:bg-white/10 text-white/80'"
          :title="p.description"
        >
          <div class="font-medium">{{ p.label }}</div>
          <div class="text-white/40 mt-0.5">{{ p.description }}</div>
        </button>
      </div>
    </div>

    <div>
      <div class="flex items-baseline justify-between mb-1">
        <h2 class="text-sm font-semibold text-white/80">가중치 조절</h2>
        <button @click="store.resetWeights()" class="text-xs text-white/40 hover:text-white/70 underline">기본값</button>
      </div>
      <p class="text-xs text-white/40 mb-3">슬라이더 → 즉시 재계산</p>

      <div class="space-y-3.5">
        <div v-for="f in store.factors" :key="f.key" class="space-y-1">
          <div class="flex justify-between items-baseline">
            <label class="text-xs font-medium flex items-center gap-1">
              <span>{{ f.label }}</span>
              <span class="text-white/30">{{ f.direction === 'lower_is_better' ? '↓' : '↑' }}</span>
              <span v-if="f.isMotie" class="text-[10px] px-1 py-0.5 bg-blue-500/20 text-blue-300 rounded" title="산업부 산하 공공기관 데이터">산업부</span>
            </label>
            <span class="text-xs tabular-nums font-mono text-blue-300">
              {{ Math.round((store.weights[f.key] / store.weightSum) * 100) }}%
            </span>
          </div>
          <input type="range" min="0" max="40" step="1"
            :value="store.weights[f.key]"
            @input="store.setWeight(f.key, Number(($event.target as HTMLInputElement).value))"
            class="w-full accent-blue-400" />
          <p class="text-[10px] text-white/40">{{ f.desc }}</p>
        </div>
      </div>
    </div>

    <div class="pt-4 border-t border-white/10">
      <h3 class="text-sm font-semibold text-white/80 mb-2">Top 10 후보지</h3>
      <ol class="space-y-1">
        <li v-for="(r, i) in store.topN" :key="r.name"
          class="flex items-center justify-between text-sm py-1.5 px-2 rounded hover:bg-white/5 cursor-pointer transition"
          :class="store.compareSet.has(r.name) ? 'bg-blue-500/15 ring-1 ring-blue-400/40' : ''"
          @click="store.toggleCompare(r.name)"
          :title="store.compareSet.has(r.name) ? '비교에서 제거' : '비교에 추가 (최대 3개)'">
          <span class="flex items-center gap-2">
            <span class="text-white/40 text-xs w-6 text-right tabular-nums">{{ i + 1 }}.</span>
            <span>{{ r.name }}</span>
            <span v-if="r.is_population_decline" class="text-[10px] px-1 py-0.5 bg-amber-500/20 text-amber-300 rounded" title="인구감소지역">감소</span>
            <span v-if="r.is_metropolitan" class="text-[10px] px-1 py-0.5 bg-purple-500/20 text-purple-300 rounded" title="수도권">수도권</span>
          </span>
          <span class="text-blue-300 text-xs tabular-nums font-mono">{{ r.score.toFixed(3) }}</span>
        </li>
      </ol>
      <p class="text-xs text-white/30 mt-2">클릭 → 비교 모드 (최대 3개)</p>
    </div>

    <div class="pt-4 border-t border-white/10">
      <h3 class="text-sm font-semibold text-white/80 mb-2">
        비수도권 Top 10
        <span class="text-[10px] px-1 py-0.5 bg-emerald-500/20 text-emerald-300 rounded ml-1">지역균형</span>
      </h3>
      <ol class="space-y-0.5">
        <li v-for="(r, i) in store.topNonMetropolitan" :key="`nm-${r.name}`"
          class="flex items-center justify-between text-xs py-1 px-2">
          <span class="flex items-center gap-2">
            <span class="text-white/40 w-5 text-right tabular-nums">{{ i + 1 }}.</span>
            <span>{{ r.name }}</span>
          </span>
          <span class="text-emerald-300 tabular-nums font-mono">{{ r.score.toFixed(3) }}</span>
        </li>
      </ol>
    </div>
  </div>
</template>
