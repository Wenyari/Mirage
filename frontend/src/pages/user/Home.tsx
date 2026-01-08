import { useNavigate } from 'react-router-dom';

import { BackgroundExplosions } from '@/components/landing/BackgroundExplosions';
import { RainbowCursor } from '@/components/landing/RainbowCursor';
import { ThreeDCubeTitle } from '@/components/landing/ThreeDCubeTitle';
import { Button } from '@/components/ui/button';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="relative flex min-h-[calc(100vh-80px)] w-full flex-col items-center justify-center overflow-hidden bg-white py-12">
      <RainbowCursor />
      <BackgroundExplosions />
      
      {/* 3D Cube Title Area */}
      <div className="z-10 mb-16 mt-8 scale-[0.6] sm:scale-[0.8] md:scale-100">
        <ThreeDCubeTitle />
      </div>
      
      {/* Slogan and Action Area */}
      <div className="z-10 max-w-4xl space-y-8 px-4 text-center duration-1000 animate-in fade-in slide-in-from-bottom-8 fill-mode-backwards">
        <div className="space-y-4">
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 md:text-6xl">
            灵感无界，视界无限
          </h1>
          <p className="text-xl font-medium tracking-wide text-slate-500 md:text-2xl">
            Inspiration Unbound, Vision Unlimited
          </p>
        </div>
        
        <p className="mx-auto max-w-2xl text-lg leading-relaxed text-slate-600 md:text-xl">
          直连全球顶尖 AI 模型，让您的文字即刻化为影像。
        </p>

        <div className="pt-8">
          <Button 
            size="lg" 
            onClick={() => navigate('/playground/video')}
            className="rounded-full bg-[#FF6633] px-10 py-7 text-lg font-bold tracking-wide text-white shadow-xl transition-all duration-300 hover:-translate-y-1 hover:bg-[#e65c2e] hover:shadow-2xl"
          >
            即刻体验
          </Button>
        </div>
      </div>
    </div>
  );
}
