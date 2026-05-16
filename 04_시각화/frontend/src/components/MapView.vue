<script setup lang="ts">
import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useScoringStore } from "../stores/scoring";

const store = useScoringStore();
const container = ref<HTMLDivElement | null>(null);
let map: MapLibreMap | null = null;
const markers: maplibregl.Marker[] = [];

function scoreToColor(score: number): string {
  const hue = score * 140;
  const light = 35 + score * 25;
  return `hsl(${hue.toFixed(0)}, 85%, ${light.toFixed(0)}%)`;
}

function radiusForScore(score: number): number {
  return 8 + score * 22;
}

function renderMarkers(): void {
  if (!map) return;
  for (const m of markers) m.remove();
  markers.length = 0;
  for (const r of store.scored) {
    const el = document.createElement("div");
    el.className = "dc-marker";
    const size = radiusForScore(r.score);
    el.style.cssText = `
      width:${size}px;height:${size}px;border-radius:50%;
      background:${scoreToColor(r.score)};
      opacity:.85;border:1.5px solid rgba(255,255,255,0.35);
      box-shadow:0 0 0 2px rgba(0,0,0,0.25);
      cursor:pointer;transition:transform .15s ease;
    `;
    el.title = `${r.name} (#${r.rank}, ${r.score.toFixed(3)})`;
    el.onmouseenter = () => (el.style.transform = "scale(1.25)");
    el.onmouseleave = () => (el.style.transform = "scale(1)");
    el.onclick = () => store.toggleCompare(r.name);

    if (store.compareSet.has(r.name)) {
      el.style.border = "3px solid #60a5fa";
      el.style.boxShadow = "0 0 0 4px rgba(96,165,250,.35)";
    }

    const popup = new maplibregl.Popup({ offset: size / 2 + 4, closeButton: false }).setHTML(`
      <div style="font:13px Pretendard,sans-serif;color:#0b1220;min-width:160px">
        <div style="font-weight:600;font-size:14px;margin-bottom:4px">${r.name}</div>
        <div style="color:#555">순위 <b>#${r.rank}</b> · 점수 <b>${r.score.toFixed(3)}</b></div>
        <div style="margin-top:6px;font-size:11px;color:#777">클릭해서 비교에 추가</div>
      </div>
    `);

    const marker = new maplibregl.Marker({ element: el })
      .setLngLat([r.lng, r.lat])
      .setPopup(popup)
      .addTo(map);
    markers.push(marker);
  }
}

onMounted(() => {
  if (!container.value) return;
  map = new maplibregl.Map({
    container: container.value,
    style: {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: "© OpenStreetMap contributors",
        },
      },
      layers: [{ id: "osm", type: "raster", source: "osm" }],
    },
    center: [127.7, 36.4],
    zoom: 6.4,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.on("load", () => renderMarkers());
});

watch(() => store.scored, renderMarkers, { deep: true });
watch(() => store.compareSet, renderMarkers, { deep: true });

onBeforeUnmount(() => {
  for (const m of markers) m.remove();
  map?.remove();
});
</script>

<template>
  <div class="relative w-full h-full">
    <div ref="container" class="absolute inset-0" />
    <div class="absolute bottom-4 left-4 bg-[#0d1628]/95 backdrop-blur px-3 py-2 rounded-md text-xs space-y-1 border border-white/10">
      <div class="font-semibold text-white/80">점수 색상</div>
      <div class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-full" :style="{ background: 'hsl(0, 85%, 35%)' }"></span>
        <span class="text-white/60">낮음 (0.0)</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-full" :style="{ background: 'hsl(70, 85%, 50%)' }"></span>
        <span class="text-white/60">중간</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-full" :style="{ background: 'hsl(140, 85%, 60%)' }"></span>
        <span class="text-white/60">높음 (1.0)</span>
      </div>
    </div>
  </div>
</template>
