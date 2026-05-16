<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { RadarChart } from "echarts/charts";
import { TooltipComponent, LegendComponent, TitleComponent } from "echarts/components";
import { useScoringStore } from "../stores/scoring";

use([CanvasRenderer, RadarChart, TooltipComponent, LegendComponent, TitleComponent]);

const store = useScoringStore();

const COLORS = ["#60a5fa", "#34d399", "#fbbf24"];

const radarOption = computed(() => ({
  backgroundColor: "transparent",
  title: { text: "요인별 점수 비교 (정규화)", left: 16, top: 8, textStyle: { color: "#e6ecff", fontSize: 14 } },
  tooltip: {},
  legend: { right: 16, top: 10, textStyle: { color: "#e6ecff" } },
  radar: {
    indicator: store.factors.map((f) => ({ name: f.label, max: 1 })),
    splitLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
    splitArea: { areaStyle: { color: ["rgba(255,255,255,0.02)", "rgba(255,255,255,0.04)"] } },
    axisLine: { lineStyle: { color: "rgba(255,255,255,0.18)" } },
    axisName: { color: "#e6ecff" },
  },
  series: [
    {
      type: "radar",
      data: store.compared.map((r, i) => ({
        name: r.name,
        value: store.factors.map((f) => r.componentScores[f.key]),
        lineStyle: { color: COLORS[i], width: 2 },
        areaStyle: { color: COLORS[i], opacity: 0.18 },
        itemStyle: { color: COLORS[i] },
      })),
    },
  ],
}));
</script>

<template>
  <div v-if="store.compared.length === 0" class="absolute inset-0 flex items-center justify-center text-center p-8">
    <div class="max-w-md">
      <div class="text-4xl mb-3">🆚</div>
      <h3 class="text-lg font-semibold mb-2">비교할 후보지를 골라줘</h3>
      <p class="text-sm text-white/50">왼쪽 Top 10 목록 또는 지도 위 마커를 클릭하면 비교에 추가돼 (최대 3개).</p>
    </div>
  </div>

  <div v-else class="absolute inset-0 overflow-y-auto p-4 space-y-4">
    <div class="bg-[#0d1628] rounded-lg border border-white/10 h-[500px]">
      <v-chart :option="radarOption" autoresize />
    </div>

    <div class="bg-[#0d1628] rounded-lg border border-white/10 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-white/5">
          <tr>
            <th class="text-left px-4 py-3 text-white/60 font-medium">항목</th>
            <th
              v-for="(r, i) in store.compared"
              :key="r.name"
              class="text-right px-4 py-3 font-semibold"
              :style="{ color: ['#60a5fa', '#34d399', '#fbbf24'][i] }"
            >
              {{ r.name }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr class="border-t border-white/10">
            <td class="px-4 py-2.5 text-white/70">종합점수</td>
            <td v-for="r in store.compared" :key="r.name" class="text-right px-4 py-2.5 tabular-nums font-mono">
              {{ r.score.toFixed(3) }}
            </td>
          </tr>
          <tr class="border-t border-white/10">
            <td class="px-4 py-2.5 text-white/70">순위</td>
            <td v-for="r in store.compared" :key="r.name" class="text-right px-4 py-2.5 tabular-nums">
              #{{ r.rank }}
            </td>
          </tr>
          <tr v-for="f in store.factors" :key="f.key" class="border-t border-white/10">
            <td class="px-4 py-2.5 text-white/70">{{ f.label }} <span class="text-white/30 text-xs ml-1">({{ f.unit }})</span></td>
            <td v-for="r in store.compared" :key="r.name" class="text-right px-4 py-2.5 tabular-nums font-mono">
              {{ f.key === 'companies' ? r.factors[f.key].toLocaleString() : r.factors[f.key].toLocaleString(undefined, { maximumFractionDigits: 2 }) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <button
      @click="store.compareSet = new Set()"
      class="px-4 py-2 text-sm bg-white/5 hover:bg-white/10 rounded-md transition border border-white/10"
    >
      비교 초기화
    </button>
  </div>
</template>
