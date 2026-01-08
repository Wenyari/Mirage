import { useNavigate } from 'react-router-dom';
import { ThreeDCubeTitle } from '@/components/landing/ThreeDCubeTitle';
import { RainbowCursor } from '@/components/landing/RainbowCursor';
import { BackgroundExplosions } from '@/components/landing/BackgroundExplosions';
import { Button } from '@/components/ui/button';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-80px)] bg-white w-full py-12 relative overflow-hidden">
      <RainbowCursor />
      <BackgroundExplosions />
      
      {/* 3D Cube Title Area */}
      <div className="scale-[0.6] sm:scale-[0.8] md:scale-100 mb-16 mt-8 z-10">
        <ThreeDCubeTitle />
      </div>
      
      {/* Slogan and Action Area */}
      <div className="text-center space-y-8 max-w-4xl px-4 animate-in fade-in slide-in-from-bottom-8 duration-1000 fill-mode-backwards z-10">
        <div className="space-y-4">
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900">
            灵感无界，视界无限
          </h1>
          <p className="text-xl md:text-2xl text-slate-500 font-medium tracking-wide">
            Inspiration Unbound, Vision Unlimited
          </p>
        </div>
        
        <p className="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          直连全球顶尖 AI 模型，让您的文字即刻化为影像。
        </p>

        <div className="pt-8">
          <Button 
            size="lg" 
            onClick={() => navigate('/playground/video')}
            className="text-lg px-10 py-7 rounded-full shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 bg-[#FF6633] hover:bg-[#e65c2e] text-white font-bold tracking-wide"
          >
            即刻体验
          </Button>
        </div>
      </div>
    </div>
  );
}
