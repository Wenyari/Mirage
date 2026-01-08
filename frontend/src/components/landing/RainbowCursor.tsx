import React, { useEffect, useRef } from 'react';

interface Point {
  x: number;
  y: number;
  life: number;
  size: number;
  hue: number;
  vx: number;
  vy: number;
}

export const RainbowCursor: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointsRef = useRef<Point[]>([]);
  const mouseRef = useRef({ x: 0, y: 0 });
  const lastMouseRef = useRef({ x: 0, y: 0 });
  const hueRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', handleMouseMove);
    resize();

    const addPoint = (x: number, y: number) => {
      // Create multiple particles for a denser trail
      for (let i = 0; i < 2; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 2;
        pointsRef.current.push({
          x,
          y,
          life: 1,
          size: Math.random() * 4 + 2,
          hue: hueRef.current + Math.random() * 30, // Color variation
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed
        });
      }
    };

    const animate = () => {
      if (!canvas || !ctx) return;
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Interpolate between last mouse position and current for smooth trails
      const dx = mouseRef.current.x - lastMouseRef.current.x;
      const dy = mouseRef.current.y - lastMouseRef.current.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      
      if (dist > 0) {
        // Add points along the path if mouse moved fast
        const steps = Math.min(dist, 20); // Limit interpolation steps
        for (let i = 0; i < steps; i++) {
          const t = i / steps;
          addPoint(
            lastMouseRef.current.x + dx * t,
            lastMouseRef.current.y + dy * t
          );
        }
        hueRef.current = (hueRef.current + 5) % 360;
      }
      
      lastMouseRef.current = { ...mouseRef.current };

      // Update and draw points
      for (let i = pointsRef.current.length - 1; i >= 0; i--) {
        const point = pointsRef.current[i];
        point.life -= 0.02;
        point.x += point.vx;
        point.y += point.vy;
        
        if (point.life <= 0) {
          pointsRef.current.splice(i, 1);
          continue;
        }

        ctx.beginPath();
        ctx.arc(point.x, point.y, point.size * point.life, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${point.hue}, 100%, 60%, ${point.life})`;
        ctx.fill();
      }

      requestAnimationFrame(animate);
    };

    const animationId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      style={{ mixBlendMode: 'multiply' }} 
    />
  );
};
