<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  DataZoomComponent,
} from "echarts/components";
import { useScoringStore } from "../stores/scoring";

use([
  CanvasRenderer,
  BarChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  DataZoomComponent,
]);

const store = useScoringStore();

const topBarOption = computed(() => ({
  backgroundColor: "transparent",
  title: { text: "Top 20 후보지 점수", left: 16, top: 8, textStyle: { color: "#e6ecff", fontSize: 14 } },
  tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
  grid: { left: 80, right: 20, top: 50, bottom: 40 },
  xAxis: { type: "value", axisLabel: { color: "#9aa6c2" }, splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } } },
  yAxis: {
    type: "category",
    inverse: true,
    data: [...store.topN, ...[...store.scored].sort((a, b) => b.score - a.score).slice(10, 20)].map((r) => r.name),
    axisLabel: { color: "#e6ecff" },
  },
  series: [
    {
      type: "bar",
      data: [...store.topN, ...[...store.scored].sort((a, b) => b.score - a.score).slice(10, 20)].map((r) => ({
        value: r.score,
        itemStyle: { color: `hsl(${(r.score * 140).toFixed(0)}, 85%, 55%)` },
      })),
      barWidth: 14,
    },
  ],
}));

const priceVsScoreOption = computed(() => ({
  backgroundColor: "transparent",
  title: { text: "실거래가 vs 종합점수", left: 16, top: 8, textStyle: { color: "#e6ecff", fontSize: 14 } },
  tooltip: {
    trigger: "item",
    formatter: (p: { data: [number, number, string] }) =>
      `${p.data[2]}<br/>거래금액: ${p.data[0].toLocaleString()}만원<br/>점수: ${p.data[1].toFixed(3)}`,
  },
  grid: { left: 60, right: 20, top: 50, bottom: 60 },
  xAxis: {
    type: "value",
    name: "거래금액 (만원)",
    nameTextStyle: { color: "#9aa6c2" },
    axisLabel: { color: "#9aa6c2" },
    splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
  },
  yAxis: {
    type: "value",
    name: "종합점수",
    nameTextStyle: { color: "#9aa6c2" },
    axisLabel: { color: "#9aa6c2" },
    splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
  },
  series: [
    {
      type: "scatter",
      data: store.scored.map((r) => [r.factors.price, r.score, r.name]),
      symbolSize: 9,
      itemStyle: { color: "#60a5fa", opacity: 0.7 },
    },
  ],
}));

const factorAvgOption = computed(() => {
  const top10 = store.topN;
  const bot10 = [...store.scored].sort((a, b) => a.score - b.score).slice(0, 10);
  const avg = (rs: typeof top10, key: keyof typeof top10[number]["componentScores"]) =>
    rs.reduce((s, r) => s + r.componentScores[key], 0) / rs.length;
  return {
    backgroundColor: "transparent",
    title: { text: "요인별 평균 (정규화 점수, Top10 vs Bottom10)", left: 16, top: 8, textStyle: { color: "#e6ecff", fontSize: 14 } },
    tooltip: { trigger: "axis" },
    legend: { right: 16, top: 10, textStyle: { color: "#e6ecff" } },
    grid: { left: 60, right: 20, top: 60, bottom: 40 },
    xAxis: {
      type: "category",
      data: store.factors.map((f) => f.label),
      axisLabel: { color: "#e6ecff", interval: 0 },
    },
    yAxis: { type: "value", max: 1, axisLabel: { color: "#9aa6c2" }, splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } } },
    series: [
      { name: "Top 10", type: "bar", data: store.factors.map((f) => avg(top10, f.key)), itemStyle: { color: "#34d399" } },
      { name: "Bottom 10", type: "bar", data: store.factors.map((f) => avg(bot10, f.key)), itemStyle: { color: "#fb7185" } },
    ],
  };
});
</script>

<template>
  <div class="absolute inset-0 overflow-y-auto p-4 grid grid-cols-1 xl:grid-cols-2 gap-4 auto-rows-min">
    <div class="bg-[#0d1628] rounded-lg border border-white/10 h-[500px]">
      <v-chart :option="topBarOption" autoresize />
    </div>
    <div class="bg-[#0d1628] rounded-lg border border-white/10 h-[500px]">
      <v-chart :option="priceVsScoreOption" autoresize />
    </div>
    <div class="bg-[#0d1628] rounded-lg border border-white/10 h-[400px] xl:col-span-2">
      <v-chart :option="factorAvgOption" autoresize />
    </div>
  </div>
</template>
