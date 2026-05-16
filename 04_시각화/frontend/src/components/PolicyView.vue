<script setup lang="ts">
import { computed } from "vue";
import { useScoringStore } from "../stores/scoring";

const store = useScoringStore();

const top3 = computed(() => store.topN.slice(0, 3));
const declineTop3 = computed(() =>
  [...store.scored]
    .filter((r) => r.is_population_decline)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3),
);

const recommendations = computed(() => [
  {
    id: 1,
    title: "수도권 데이터센터 신규 허가 총량제 → 비수도권 분산 유인",
    body: `현재 가중치 기준 Top 10 중 수도권 비중 ${
      Math.round((store.topN.filter((r) => r.is_metropolitan).length / Math.max(store.topN.length, 1)) * 100)
    }%. 송전망 부담 완화를 위해 권역별 총량제 도입 및 비수도권 후보지(${top3.value
      .filter((r) => !r.is_metropolitan).map((r) => r.name).slice(0, 2).join(", ")}) 우선 인허가.`,
    target: "산업통상자원부 · 국토교통부",
  },
  {
    id: 2,
    title: "한전 송전망 확충 우선순위 = 비수도권 Top 후보지",
    body: `KEPCO/KPX 데이터 기반 ${store.topNonMetropolitan.slice(0, 3).map((r) => r.name).join(", ")} 권역에 154kV 변전소·송전선로 확충을 5년 내 추진. 데이터센터 클러스터 조성 선제 인프라.`,
    target: "한국전력공사 · 전력거래소",
  },
  {
    id: 3,
    title: "인구감소지역 데이터센터 입주 인센티브 패키지",
    body: `행안부 지정 인구감소지역 중 입지 점수 상위 ${declineTop3.value.map((r) => r.name).join(", ")}에 (1) 법인세 3년 100% 감면 (2) 전기요금 산업용(을) 적용 (3) 토지비 50% 보조 패키지 적용.`,
    target: "행정안전부 · 기획재정부 · 광역 지자체",
  },
  {
    id: 4,
    title: "RE100 대응 — 재생에너지 인접 데이터센터 클러스터",
    body: "호남(태양광 벨트) · 강원(풍력) 지역에 'RE100 데이터센터 특구' 지정. 발전소 직접 PPA 허용 + 송전 우선 접속권 부여.",
    target: "산업통상자원부 · 한국에너지공단",
  },
  {
    id: 5,
    title: "데이터센터 폐열 활용 의무화 (지역난방 연계)",
    body: "MW급 데이터센터는 폐열의 50% 이상을 지역난방·스마트팜으로 환원 의무화. 지역활력 + 탄소중립 동시 달성.",
    target: "산업통상자원부 · 환경부",
  },
]);
</script>

<template>
  <div class="p-6 overflow-y-auto h-full">
    <div class="max-w-5xl mx-auto space-y-6">
      <header class="border-b border-white/10 pb-4">
        <h2 class="text-xl font-bold">📋 정책 제언</h2>
        <p class="text-sm text-white/60 mt-1">
          현재 가중치 기준 분석 결과로부터 도출된 5가지 정책 제언.
        </p>
      </header>

      <div class="grid grid-cols-3 gap-3">
        <div class="bg-white/5 border border-white/10 rounded-lg p-4">
          <div class="text-xs text-white/50 mb-1">분석 대상</div>
          <div class="text-2xl font-bold">{{ store.regions.length }}개</div>
          <div class="text-xs text-white/40 mt-0.5">전국 시군구</div>
        </div>
        <div class="bg-blue-500/10 border border-blue-400/30 rounded-lg p-4">
          <div class="text-xs text-white/50 mb-1">산업부 산하 데이터</div>
          <div class="text-2xl font-bold text-blue-300">
            {{ store.factors.filter((f) => f.isMotie).length }}/9
          </div>
          <div class="text-xs text-white/40 mt-0.5">지표</div>
        </div>
        <div class="bg-amber-500/10 border border-amber-400/30 rounded-lg p-4">
          <div class="text-xs text-white/50 mb-1">인구감소지역 비율 (Top10)</div>
          <div class="text-2xl font-bold text-amber-300">
            {{ Math.round((store.topN.filter((r) => r.is_population_decline).length / Math.max(store.topN.length, 1)) * 100) }}%
          </div>
          <div class="text-xs text-white/40 mt-0.5">지역균형 잠재력</div>
        </div>
      </div>

      <div class="space-y-3">
        <article v-for="r in recommendations" :key="r.id"
          class="bg-white/5 border border-white/10 rounded-lg p-5 hover:bg-white/10 transition">
          <div class="flex items-start gap-3">
            <div class="text-2xl font-bold text-blue-300 w-8 shrink-0">{{ r.id }}</div>
            <div class="flex-1">
              <h3 class="text-base font-semibold mb-2">{{ r.title }}</h3>
              <p class="text-sm text-white/70 leading-relaxed">{{ r.body }}</p>
              <div class="mt-3 text-xs text-white/40">
                <span class="text-white/50">대상 기관:</span> {{ r.target }}
              </div>
            </div>
          </div>
        </article>
      </div>

      <div class="bg-white/[0.03] border border-white/10 rounded-lg p-5">
        <h3 class="text-sm font-semibold text-white/80 mb-3">📚 활용 데이터 출처</h3>
        <table class="w-full text-xs">
          <thead class="text-white/40">
            <tr>
              <th class="text-left py-1.5 pr-3">지표</th>
              <th class="text-left py-1.5 pr-3">출처 기관</th>
              <th class="text-left py-1.5">산업부 산하</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="f in store.factors" :key="f.key" class="border-t border-white/5">
              <td class="py-1.5 pr-3 font-medium">{{ f.label }}</td>
              <td class="py-1.5 pr-3 text-white/60">{{ f.source }}</td>
              <td class="py-1.5">
                <span v-if="f.isMotie" class="text-[10px] px-1.5 py-0.5 bg-blue-500/20 text-blue-300 rounded">✓</span>
                <span v-else class="text-white/30">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
