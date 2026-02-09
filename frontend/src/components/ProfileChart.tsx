import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import {
  ComposedChart,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Customized,
  BarChart,
  Bar,
  ReferenceLine,
} from "recharts";
import type { ProfilePoint, BinResult } from "../lib/api";

interface ProfileChartProps {
  points: ProfilePoint[];
  bins: BinResult[];
}

/* ── Helpers ─────────────────────────────────────────────────────── */

const tooltipStyle = {
  backgroundColor: "#181B23",
  border: "1px solid #2A2E37",
  borderRadius: "8px",
  color: "#E0E0E0",
  fontSize: "12px",
};

function formatStation(val: number): string {
  const whole = Math.floor(val);
  const frac = val - whole;
  if (frac < 0.005) return String(whole);
  return `${whole}+${(frac * 20).toFixed(0)}`;
}

/** Build sorted unique station ticks from bin boundaries */
function buildStationTicks(bins: BinResult[]): number[] {
  const set = new Set<number>();
  for (const b of bins) {
    set.add(b.station_start);
    set.add(b.station_end);
  }
  return Array.from(set).sort((a, b) => a - b);
}

/** Compute tight Y domain from a set of points with padding */
function computeYDomain(
  pts: ProfilePoint[],
  paddingPct = 0.15,
  minPad = 0.5,
): [number, number] {
  if (pts.length === 0) return [0, 1];
  let lo = Infinity;
  let hi = -Infinity;
  for (const p of pts) {
    if (p.elevation_greide < lo) lo = p.elevation_greide;
    if (p.elevation_terrain < lo) lo = p.elevation_terrain;
    if (p.elevation_greide > hi) hi = p.elevation_greide;
    if (p.elevation_terrain > hi) hi = p.elevation_terrain;
  }
  const range = hi - lo;
  const pad = Math.max(range * paddingPct, minPad);
  return [lo - pad, hi + pad];
}

/* ── Cut/Fill area overlay (SVG paths between the two lines) ──── */

function CutFillAreas({
  xAxisMap,
  yAxisMap,
  points,
}: {
  xAxisMap?: Record<string, { scale: (v: number) => number }>;
  yAxisMap?: Record<string, { scale: (v: number) => number }>;
  points: ProfilePoint[];
}) {
  if (!xAxisMap || !yAxisMap || points.length < 2) return null;

  const xAxis = Object.values(xAxisMap)[0];
  const yAxis = Object.values(yAxisMap)[0];
  if (!xAxis || !yAxis) return null;

  const paths: { d: string; color: string }[] = [];

  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i];
    const p1 = points[i + 1];

    const d0 = p0.elevation_greide - p0.elevation_terrain;
    const d1 = p1.elevation_greide - p1.elevation_terrain;

    const x0px = xAxis.scale(p0.station);
    const x1px = xAxis.scale(p1.station);
    if (isNaN(x0px) || isNaN(x1px)) continue;

    if (d0 * d1 < 0) {
      // Lines cross
      const t = d0 / (d0 - d1);
      const xMid = p0.station + t * (p1.station - p0.station);
      const yMid =
        p0.elevation_greide +
        t * (p1.elevation_greide - p0.elevation_greide);
      const xMidPx = xAxis.scale(xMid);
      const yMidPx = yAxis.scale(yMid);

      const g0 = yAxis.scale(p0.elevation_greide);
      const t0 = yAxis.scale(p0.elevation_terrain);
      paths.push({
        d: `M${x0px},${g0} L${xMidPx},${yMidPx} L${x0px},${t0} Z`,
        color: d0 > 0 ? "rgba(34,197,94,0.6)" : "rgba(239,68,68,0.6)",
      });

      const g1 = yAxis.scale(p1.elevation_greide);
      const t1 = yAxis.scale(p1.elevation_terrain);
      paths.push({
        d: `M${xMidPx},${yMidPx} L${x1px},${g1} L${x1px},${t1} Z`,
        color: d1 > 0 ? "rgba(34,197,94,0.6)" : "rgba(239,68,68,0.6)",
      });
    } else {
      const g0 = yAxis.scale(p0.elevation_greide);
      const t0 = yAxis.scale(p0.elevation_terrain);
      const g1 = yAxis.scale(p1.elevation_greide);
      const t1 = yAxis.scale(p1.elevation_terrain);
      const avg = (d0 + d1) / 2;
      paths.push({
        d: `M${x0px},${g0} L${x1px},${g1} L${x1px},${t1} L${x0px},${t0} Z`,
        color: avg >= 0 ? "rgba(34,197,94,0.6)" : "rgba(239,68,68,0.6)",
      });
    }
  }

  return (
    <g>
      {paths.map((p, i) => (
        <path key={i} d={p.d} fill={p.color} stroke="none" />
      ))}
    </g>
  );
}

/* ── Main export ──────────────────────────────────────────────── */

export function ProfileChart({ points, bins }: ProfileChartProps) {
  const [activeStrip, setActiveStrip] = useState(0);
  const stationTicks = useMemo(() => buildStationTicks(bins), [bins]);

  const barData = useMemo(
    () =>
      bins.map((b) => ({
        label: `${formatStation(b.station_start)}–${formatStation(b.station_end)}`,
        aterro: b.fill,
        corte: -b.cut,
      })),
    [bins],
  );

  // Difference data
  const diffData = useMemo(
    () =>
      points.map((p) => {
        const diff = p.elevation_greide - p.elevation_terrain;
        return {
          station: p.station,
          diff,
          aterro: diff > 0 ? diff : 0,
          corte: diff < 0 ? diff : 0,
        };
      }),
    [points],
  );

  const yDomain = useMemo(() => computeYDomain(points), [points]);

  const diffYDomain = useMemo((): [number, number] => {
    if (diffData.length === 0) return [-1, 1];
    let lo = 0;
    let hi = 0;
    for (const d of diffData) {
      if (d.diff < lo) lo = d.diff;
      if (d.diff > hi) hi = d.diff;
    }
    const absMax = Math.max(Math.abs(lo), Math.abs(hi), 0.01);
    const pad = absMax * 0.2;
    return [-(absMax + pad), absMax + pad];
  }, [diffData]);

  // Per-strip data: slice profile points for each bin
  const stripCharts = useMemo(() => {
    return bins.map((bin) => {
      const pts = points.filter(
        (p) => p.station >= bin.station_start - 0.01 && p.station <= bin.station_end + 0.01,
      );
      const ptsWithMin = pts.map(p => ({
        ...p,
        minElev: Math.min(p.elevation_greide, p.elevation_terrain),
      }));
      // Extremely tight Y domain — padding only 5% or 0.005m minimum
      const domain = computeYDomain(pts, 0.05, 0.005);
      // Build ticks every 1 whole station (e.g. 1000, 1001, 1002)
      const stripTicks: number[] = [];
      for (let s = Math.ceil(bin.station_start); s <= bin.station_end + 0.001; s += 1.0) {
        stripTicks.push(s);
      }
      return { bin, pts: ptsWithMin, domain, stripTicks };
    });
  }, [bins, points]);

  if (points.length === 0) return null;

  return (
    <div className="space-y-4">
      {/* ── 1. Full Profile ────────────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-4">
        <h3 className="text-sm font-semibold mb-3">Perfil Longitudinal — Visão Geral</h3>
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart
            data={points}
            margin={{ top: 10, right: 20, bottom: 10, left: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2E37" />
            <XAxis
              dataKey="station"
              type="number"
              domain={["dataMin", "dataMax"]}
              ticks={stationTicks}
              tickFormatter={formatStation}
              tick={{ fill: "#9CA3AF", fontSize: 11 }}
              label={{
                value: "Estaca",
                position: "insideBottom",
                offset: -5,
                fill: "#9CA3AF",
                fontSize: 12,
              }}
            />
            <YAxis
              type="number"
              domain={yDomain}
              tickFormatter={(v: number) => v.toFixed(1)}
              tick={{ fill: "#9CA3AF", fontSize: 11 }}
              label={{
                value: "Cota (m)",
                angle: -90,
                position: "insideLeft",
                offset: 10,
                fill: "#9CA3AF",
                fontSize: 12,
              }}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              labelFormatter={(v) => `Estaca ${formatStation(v as number)}`}
              formatter={(value, name) => [
                ((value as number) ?? 0).toFixed(4),
                name === "elevation_greide" ? "Greide" : "Terreno",
              ]}
            />
            <Legend
              formatter={(v: string) =>
                v === "elevation_greide" ? "Greide (VT)" : "Terreno (PF)"
              }
            />
            {/* Vertical reference lines at bin boundaries */}
            {stationTicks.map((s) => (
              <ReferenceLine
                key={s}
                x={s}
                stroke="#3B3F4A"
                strokeDasharray="4 4"
                strokeWidth={0.8}
              />
            ))}
            <Customized
              component={(props: Record<string, unknown>) => (
                <CutFillAreas
                  xAxisMap={
                    props.xAxisMap as Record<
                      string,
                      { scale: (v: number) => number }
                    >
                  }
                  yAxisMap={
                    props.yAxisMap as Record<
                      string,
                      { scale: (v: number) => number }
                    >
                  }
                  points={points}
                />
              )}
            />
            <Line
              type="linear"
              dataKey="elevation_greide"
              stroke="#E07B3D"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="linear"
              dataKey="elevation_terrain"
              stroke="#60A5FA"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* ── 2. Per-strip profile (exaggerated Y, single with nav) ── */}
      {stripCharts.length > 0 && stripCharts[activeStrip]?.pts.length >= 2 && (() => {
        const { bin, pts, domain, stripTicks } = stripCharts[activeStrip];
        const label = `${formatStation(bin.station_start)} – ${formatStation(bin.station_end)}`;
        return (
          <div className="bg-surface border border-border rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold">
                  Perfil por Faixa — Escala Vertical Exagerada
                </h3>
                <p className="text-xs text-muted-foreground">
                  Escala Y independente para evidenciar corte/aterro
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveStrip((i) => Math.max(0, i - 1))}
                  disabled={activeStrip === 0}
                  className="p-1.5 rounded-lg border border-border hover:bg-surface-hover disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft size={16} />
                </button>
                <span className="text-xs font-medium min-w-[120px] text-center">
                  {label}
                </span>
                <button
                  onClick={() => setActiveStrip((i) => Math.min(stripCharts.length - 1, i + 1))}
                  disabled={activeStrip === stripCharts.length - 1}
                  className="p-1.5 rounded-lg border border-border hover:bg-surface-hover disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronRight size={16} />
                </button>
                <span className="text-[10px] text-muted-foreground ml-1">
                  {activeStrip + 1}/{stripCharts.length}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-center gap-4 mb-3">
              {bin.fill > 0 && (
                <span className="text-xs text-success font-medium">
                  +{bin.fill.toFixed(4)} m² aterro
                </span>
              )}
              {bin.cut > 0 && (
                <span className="text-xs text-danger font-medium">
                  −{bin.cut.toFixed(4)} m² corte
                </span>
              )}
            </div>
            <ResponsiveContainer width="100%" height={700}>
              <ComposedChart
                data={pts}
                margin={{ top: 10, right: 20, bottom: 10, left: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#2A2E37" />
                <XAxis
                  dataKey="station"
                  type="number"
                  domain={[bin.station_start, bin.station_end]}
                  ticks={stripTicks}
                  tickFormatter={formatStation}
                  tick={{ fill: "#9CA3AF", fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  domain={domain}
                  tickFormatter={(v: number) => v.toFixed(3)}
                  tick={{ fill: "#9CA3AF", fontSize: 11 }}
                  width={80}
                  label={{
                    value: "Cota (m)",
                    angle: -90,
                    position: "insideLeft",
                    offset: 20,
                    fill: "#9CA3AF",
                    fontSize: 12,
                  }}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null;
                    const items = payload.filter(
                      (e) => !(e.name as string)?.startsWith("_"),
                    );
                    return (
                      <div style={{ ...tooltipStyle, padding: "8px 12px" }}>
                        <p style={{ margin: "0 0 4px", fontWeight: 600 }}>
                          Estaca {formatStation(label as number)}
                        </p>
                        {items.map((e, i) => (
                          <p key={i} style={{ margin: 0, color: e.color }}>
                            {e.dataKey === "elevation_greide"
                              ? "Greide"
                              : "Terreno"}
                            : {(e.value as number).toFixed(4)}
                          </p>
                        ))}
                      </div>
                    );
                  }}
                />
                <Legend
                  formatter={(v: string) =>
                    v === "elevation_greide" ? "Greide (VT)" : "Terreno (PF)"
                  }
                />
                {/* Station reference lines at each tick */}
                {stripTicks.map((s) => (
                  <ReferenceLine
                    key={s}
                    x={s}
                    stroke="#3B3F4A"
                    strokeDasharray="4 4"
                    strokeWidth={0.5}
                  />
                ))}
                {/* Filled areas: green=aterro, red=corte, mask=background */}
                <Area
                  type="linear"
                  dataKey="elevation_greide"
                  name="_areaG"
                  stroke="none"
                  fill="#22C55E"
                  fillOpacity={1}
                  baseValue={domain[0]}
                  isAnimationActive={false}
                  legendType="none"
                />
                <Area
                  type="linear"
                  dataKey="elevation_terrain"
                  name="_areaT"
                  stroke="none"
                  fill="#EF4444"
                  fillOpacity={1}
                  baseValue={domain[0]}
                  isAnimationActive={false}
                  legendType="none"
                />
                <Area
                  type="linear"
                  dataKey="minElev"
                  name="_mask"
                  stroke="none"
                  fill="#181B23"
                  fillOpacity={1}
                  baseValue={domain[0]}
                  isAnimationActive={false}
                  legendType="none"
                />
                <Line
                  type="linear"
                  dataKey="elevation_greide"
                  stroke="#E07B3D"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="linear"
                  dataKey="elevation_terrain"
                  stroke="#60A5FA"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        );
      })()}

      {/* ── 3. Difference chart ───────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-4">
        <h3 className="text-sm font-semibold mb-1">
          Diferença Greide − Terreno
        </h3>
        <p className="text-xs text-muted-foreground mb-3">
          Positivo = aterro (verde) · Negativo = corte (vermelho)
        </p>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart
            data={diffData}
            margin={{ top: 10, right: 20, bottom: 10, left: 10 }}
          >
            <defs>
              <linearGradient id="gradAterro" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22C55E" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#22C55E" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="gradCorte" x1="0" y1="1" x2="0" y2="0">
                <stop offset="0%" stopColor="#EF4444" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#EF4444" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2E37" />
            <XAxis
              dataKey="station"
              type="number"
              domain={["dataMin", "dataMax"]}
              ticks={stationTicks}
              tickFormatter={formatStation}
              tick={{ fill: "#9CA3AF", fontSize: 11 }}
              label={{
                value: "Estaca",
                position: "insideBottom",
                offset: -5,
                fill: "#9CA3AF",
                fontSize: 12,
              }}
            />
            <YAxis
              type="number"
              domain={diffYDomain}
              tick={{ fill: "#9CA3AF", fontSize: 11 }}
              label={{
                value: "Δ Cota (m)",
                angle: -90,
                position: "insideLeft",
                offset: 10,
                fill: "#9CA3AF",
                fontSize: 12,
              }}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              labelFormatter={(v) => `Estaca ${formatStation(v as number)}`}
              formatter={(value, name) => [
                ((value as number) ?? 0).toFixed(4) + " m",
                name === "aterro" ? "Aterro" : "Corte",
              ]}
            />
            {/* Bin boundary reference lines */}
            {stationTicks.map((s) => (
              <ReferenceLine
                key={s}
                x={s}
                stroke="#3B3F4A"
                strokeDasharray="4 4"
                strokeWidth={0.8}
              />
            ))}
            <ReferenceLine y={0} stroke="#6B7280" strokeWidth={1.5} />
            <Area
              type="linear"
              dataKey="aterro"
              stroke="#22C55E"
              strokeWidth={1.5}
              fill="url(#gradAterro)"
              isAnimationActive={false}
              baseValue={0}
            />
            <Area
              type="linear"
              dataKey="corte"
              stroke="#EF4444"
              strokeWidth={1.5}
              fill="url(#gradCorte)"
              isAnimationActive={false}
              baseValue={0}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* ── 4. Bar chart per strip ────────────────────────── */}
      <div className="bg-surface border border-border rounded-xl p-4">
        <h3 className="text-sm font-semibold mb-3">
          Corte / Aterro por Faixa
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={barData}
            margin={{ top: 10, right: 20, bottom: 10, left: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2E37" />
            <XAxis
              dataKey="label"
              tick={{ fill: "#9CA3AF", fontSize: 10 }}
              interval={0}
            />
            <YAxis
              tick={{ fill: "#9CA3AF", fontSize: 11 }}
              label={{
                value: "Área (m²)",
                angle: -90,
                position: "insideLeft",
                offset: 10,
                fill: "#9CA3AF",
                fontSize: 12,
              }}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value, name) => [
                Math.abs((value as number) ?? 0).toFixed(4) + " m²",
                name === "aterro" ? "Aterro" : "Corte",
              ]}
            />
            <Legend
              formatter={(v: string) => (v === "aterro" ? "Aterro" : "Corte")}
            />
            <ReferenceLine y={0} stroke="#6B7280" />
            <Bar dataKey="aterro" fill="#22C55E" radius={[3, 3, 0, 0]} />
            <Bar dataKey="corte" fill="#EF4444" radius={[0, 0, 3, 3]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
