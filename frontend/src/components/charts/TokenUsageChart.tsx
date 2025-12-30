import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ChartDataPoint } from '@/types';

interface TokenUsageChartProps {
  data: ChartDataPoint[];
}

export function TokenUsageChart({ data }: TokenUsageChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Token 消耗趋势</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
              className="text-xs"
            />
            <YAxis
              className="text-xs"
              tickFormatter={(value) => {
                if (value >= 1000) {
                  return `${(value / 1000).toFixed(0)}K`;
                }
                return value;
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              labelFormatter={(value) => {
                const date = new Date(value as string);
                return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`;
              }}
              formatter={(value: number) => [
                value.toLocaleString(),
                'Token 消耗',
              ]}
            />
            <Bar
              dataKey="token_usage"
              fill="hsl(var(--chart-1))"
              radius={[4, 4, 0, 0]}
              name="Token 消耗"
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
