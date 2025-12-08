'use client';

import { useEffect, useRef } from 'react';

export const ParticleCursor = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: Particle[] = [];
    let mouseX = 0;
    let mouseY = 0;
    
    // Store current theme colors (updated dynamically)
    const themeColors = {
      primary: '#7c3aed',    // Default purple fallback
      foreground: '#1f2937'  // Default dark fallback
    };

    const updateColors = () => {
      // Create a temp element to compute the actual color from CSS variables
      const temp = document.createElement('div');
      document.body.appendChild(temp);
      
      temp.style.color = 'hsl(var(--primary))';
      const computedPrimary = getComputedStyle(temp).color;
      
      temp.style.color = 'hsl(var(--foreground))';
      const computedForeground = getComputedStyle(temp).color;
      
      document.body.removeChild(temp);
      
      if (computedPrimary && computedPrimary !== '') {
        themeColors.primary = computedPrimary;
      }
      if (computedForeground && computedForeground !== '') {
        themeColors.foreground = computedForeground;
      }
    };

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      updateColors();
    };

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // Update colors when theme changes (class attribute on html element)
    const observer = new MutationObserver(() => {
      updateColors();
      // Update existing particles to new theme colors
      particles.forEach(p => {
        p.updateColor(themeColors.primary, themeColors.foreground);
      });
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class', 'data-theme'] });

    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      
      // Spawn "pop" burst with current theme colors
      for (let i = 0; i < 3; i++) {
        particles.push(new Particle(mouseX, mouseY, themeColors.primary, themeColors.foreground));
      }
    };

    window.addEventListener('mousemove', handleMouseMove);

    class Particle {
      x: number;
      y: number;
      size: number;
      speedX: number;
      speedY: number;
      color: string;
      colorType: 'primary' | 'foreground';
      life: number;
      decay: number;

      constructor(x: number, y: number, primary: string, foreground: string) {
        this.x = x;
        this.y = y;
        // Start larger for "pop"
        this.size = Math.random() * 6 + 2; 
        // Burst velocity
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 2 + 1;
        this.speedX = Math.cos(angle) * speed;
        this.speedY = Math.sin(angle) * speed;
        
        // Randomly pick primary or foreground, and store which type
        this.colorType = Math.random() > 0.5 ? 'primary' : 'foreground';
        this.color = this.colorType === 'primary' ? primary : foreground;
        
        this.life = 1.0;
        this.decay = Math.random() * 0.03 + 0.02;
      }

      updateColor(primary: string, foreground: string) {
        // Update color based on the stored type
        this.color = this.colorType === 'primary' ? primary : foreground;
      }

      update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.speedX *= 0.95; // Friction
        this.speedY *= 0.95;
        this.life -= this.decay;
        if (this.size > 0.2) this.size -= 0.1; // Shrink
      }

      draw() {
        if (!ctx) return;
        
        ctx.save();
        ctx.globalAlpha = this.life;
        ctx.translate(this.x, this.y);
        
        // Create radial gradient for 3D sphere look
        const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, this.size);
        
        // Use computed colors (already in rgb format)
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
        gradient.addColorStop(0.4, this.color);
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)'); // Fade out edge

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(0, 0, this.size, 0, Math.PI * 2);
        ctx.fill();
        
        // Add a "shine" or glow
        ctx.shadowBlur = 15;
        ctx.shadowColor = this.color;
        
        ctx.restore();
      }
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();

        if (particles[i].life <= 0 || particles[i].size <= 0.2) {
          particles.splice(i, 1);
          i--;
        }
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
      observer.disconnect();
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-50"
      style={{ mixBlendMode: 'normal' }} 
    />
  );
};
