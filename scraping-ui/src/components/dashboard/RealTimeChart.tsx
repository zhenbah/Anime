'use client';

import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

interface ChartData {
  name: string;
  value: number;
}

interface RealTimeChartProps {
  data: ChartData[];
  title: string;
  color?: string;
}

export function RealTimeChart({ data, title, color = '#6366f1' }: RealTimeChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
    };

    resize();
    window.addEventListener('resize', resize);

    const drawChart = () => {
      if (!ctx || !canvas) return;

      const width = canvas.width;
      const height = canvas.height;
      const padding = 20;
      const chartWidth = width - padding * 2;
      const chartHeight = height - padding * 2;

      ctx.clearRect(0, 0, width, height);

      // Draw grid
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
      }

      // Draw line
      if (data.length > 1) {
        const maxValue = Math.max(...data.map(d => d.value), 1);
        const points = data.map((d, i) => ({
          x: padding + (chartWidth / (data.length - 1)) * i,
          y: padding + chartHeight - (d.value / maxValue) * chartHeight,
        }));

        // Gradient fill
        const gradient = ctx.createLinearGradient(0, padding, 0, height - padding);
        gradient.addColorStop(0, color.replace(')', ', 0.3)').replace('rgb', 'rgba'));
        gradient.addColorStop(1, color.replace(')', ', 0)').replace('rgb', 'rgba'));

        ctx.beginPath();
        ctx.moveTo(points[0].x, height - padding);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.lineTo(points[points.length - 1].x, height - padding);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // Line
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Points
        points.forEach(p => {
          ctx.beginPath();
          ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.fill();
        });
      }
    };

    drawChart();
    const interval = setInterval(drawChart, 1000);

    return () => {
      clearInterval(interval);
      window.removeEventListener('resize', resize);
    };
  }, [data, color]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <canvas
          ref={canvasRef}
          className="w-full h-[200px]"
        />
      </CardContent>
    </Card>
  );
}
