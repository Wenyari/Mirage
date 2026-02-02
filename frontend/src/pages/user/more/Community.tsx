import { Card } from '@/components/ui/card';
import { USER_NAVIGATION } from '@/config/user-navigation';
import qqJpg from '@/assets/qq.jpg';

export default function Community() {
  return (
    <div className="container mx-auto max-w-4xl py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{USER_NAVIGATION.MORE.children.COMMUNITY.label}</h1>
        <p className="text-muted-foreground mt-2">加入我们的官方社群，获取最新资讯，与志同道合的朋友交流心得。</p>
      </div>

      <div className="grid gap-6 md:grid-cols-1">
        <Card className="flex flex-col items-center justify-center p-8 text-center">
          <h2 className="text-2xl font-semibold mb-4">官方QQ交流群</h2>
          <p className="mb-6 text-muted-foreground">扫码加入QQ群，参与讨论，获取技术支持</p>
          <div className="relative mb-6 rounded-lg border bg-white p-4 shadow-sm">
            <img
              src={qqJpg}
              alt="QQ Group QR Code"
              className="h-auto w-full max-w-[300px] object-contain"
            />
          </div>
          <p className="text-sm text-muted-foreground">如果无法扫码，请搜索群号加入我们</p>
        </Card>
      </div>
    </div>
  );
}
