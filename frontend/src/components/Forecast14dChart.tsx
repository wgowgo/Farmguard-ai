'use client';

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { riskBarColor } from '@/lib/api';

export interface ForecastPoint {
  date: string;
  avg_risk: number;
  type: 'observed' | 'forecast';
  label?: string;
  rain_forecast_mm?: number;
  pop_max?: number;
  source?: 'kma' | 'model';
}

export default function Forecast14dChart({ data }: { data: ForecastPoint[] }) {
  const formatted = data.map((d) => ({
    ...d,
    shortLabel: d.label || d.date.slice(5),
    isForecast: d.type === 'forecast',
  }));

  const todayIdx = formatted.findIndex((d) => d.type === 'forecast') - 1;

  return (
    <div>
      <div className="flex gap-5 text-xs text-ink-muted mb-4">
        <span className="flex items-center gap-2">
          <span className="w-4 h-0.5 bg-rda-600 rounded" /> 관측
        </span>
        <span className="flex items-center gap-2">
          <span className="w-4 h-0.5 border-t-2 border-dashed border-orange-400" /> 예보
        </span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8ebef" vertical={false} />
          <XAxis dataKey="shortLabel" tick={{ fontSize: 11, fill: '#888888' }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#888888' }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ borderRadius: 6, border: '1px solid #d9dde3', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
            formatter={(v: number, _n, p) => {
              const payload = p?.payload as ForecastPoint;
              const suffix = payload?.type === 'forecast' ? ' (예보)' : '';
              const src = payload?.source === 'kma' ? ', 기상청' : payload?.source === 'model' ? ', 추정' : '';
              const rain = payload?.rain_forecast_mm != null ? `, 강수 ${payload.rain_forecast_mm}mm` : '';
              const pop = payload?.pop_max != null ? `, 강수확률 ${payload.pop_max}%` : '';
              return [`${v}점${suffix}${rain}${pop}${src}`, '위험도'];
            }}
          />
          {todayIdx >= 0 && (
            <ReferenceLine x={formatted[todayIdx]?.shortLabel} stroke="#d9dde3" strokeDasharray="4 4" />
          )}
          <Line
            type="monotone"
            dataKey="avg_risk"
            stroke="#007a3d"
            strokeWidth={2}
            dot={(props) => {
              const { cx, cy, payload } = props;
              const color = riskBarColor(payload.avg_risk);
              const isFc = payload.isForecast;
              return (
                <circle
                  key={payload.date}
                  cx={cx}
                  cy={cy}
                  r={4}
                  fill={isFc ? '#fff' : color}
                  stroke={isFc ? '#f97316' : color}
                  strokeWidth={2}
                />
              );
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
