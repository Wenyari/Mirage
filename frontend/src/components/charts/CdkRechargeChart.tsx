import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ChartDataPoint } from '@/types';

interface CdkRechargeChartProps {
  data: ChartDataPoint[];
}

export function CdkRechargeChart({ data }: CdkRechargeChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>CDK 兑换积分趋势</CardTitle>
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
                '兑换积分',
              ]}
            />
            <Bar
              dataKey="cdk_recharge"
              fill="hsl(var(--chart-2))"
              radius={[4, 4, 0, 0]}
              name="兑换积分"
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
