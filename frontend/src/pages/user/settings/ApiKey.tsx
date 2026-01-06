import { Card } from '@/components/ui/card';

export default function ApiKey() {
  return (
    <div className="flex items-center justify-center p-6">
      <Card className="w-full max-w-3xl p-12 text-center">
        <h2 className="text-xl font-semibold mb-4">API 秘钥</h2>
        <p className="text-muted-foreground">正在开发</p>
      </Card>
    </div>
  );
}


