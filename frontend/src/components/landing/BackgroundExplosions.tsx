import React, { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  color: string;
  size: number;
}

export const BackgroundExplosions: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    window.addEventListener('resize', resize);
    resize();

    const createExplosion = (x: number, y: number) => {
      // Random particle count
      const particleCount = 30 + Math.random() * 30;
      // Random base color for this explosion
      const baseHue = Math.random() * 360;
      
      for (let i = 0; i < particleCount; i++) {
        const angle = Math.random() * Math.PI * 2;
        // Much slower initial burst for a gentle "blossom" effect
        const speed = Math.random() * 1.5 + 0.2; 
        const hue = baseHue + (Math.random() * 60 - 30); 
        
        particlesRef.current.push({
          x,
          y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 1.0,
          color: `hsla(${hue}, 90%, 65%,`, 
          size: Math.random() * 4 + 2
        });
      }
    };

    // Auto trigger explosions loop
    let timeoutId: NodeJS.Timeout;
    const scheduleExplosion = () => {
      if (document.hidden) {
        timeoutId = setTimeout(scheduleExplosion, 1000);
        return;
      }

      const margin = 100;
      const x = margin + Math.random() * (canvas.width - margin * 2);
      const y = margin + Math.random() * (canvas.height - margin * 2);
      
      createExplosion(x, y);

      // Slower frequency to appreciate the long-lasting effects
      timeoutId = setTimeout(scheduleExplosion, 2000 + Math.random() * 2000);
    };

    scheduleExplosion();

    const animate = () => {
      if (!canvas || !ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = particlesRef.current.length - 1; i >= 0; i--) {
        const p = particlesRef.current[i];
        
        // Very slow decay: lasts about 3-4 seconds
        p.life -= 0.004; 
        p.x += p.vx;
        p.y += p.vy;
        
        // Micro gravity for "floating dust" feel
        p.vy += 0.005;
        // Minimal air resistance to keep them moving gently
        p.vx *= 0.995;
        p.vy *= 0.995;
        
        if (p.life <= 0) {
          particlesRef.current.splice(i, 1);
          continue;
        }

        ctx.beginPath();
        // Fade out size slightly as they die
        ctx.arc(p.x, p.y, p.size * Math.max(0.5, p.life), 0, Math.PI * 2); 
        // Use ease-out curve for opacity so they stay visible longer then fade quickly at end
        // or just linear is fine if life is long enough. 
        // Let's use a smooth fade curve: p.life * p.life
        ctx.fillStyle = `${p.color} ${p.life * p.life})`; 
        ctx.fill();
      }

      requestAnimationFrame(animate);
    };

    const animId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resize);
      clearTimeout(timeoutId);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <canvas 
      ref={canvasRef} 
      className="pointer-events-none fixed inset-0 z-0"
      // Use multiply blend mode to look nice on white background (like ink)
      // or normal. Let's stick to normal for vibrant colors on white, 
      // or multiply for a more "printed" look. Normal is safer for "explosion".
      style={{ opacity: 0.8 }} 
    />
  );
};
