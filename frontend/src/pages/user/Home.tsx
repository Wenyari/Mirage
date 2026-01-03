import { PlaceholderPage } from '@/components/user/PlaceholderPage';
import { USER_NAVIGATION } from '@/config/user-navigation';

export default function Home() {
  return <PlaceholderPage title={USER_NAVIGATION.HOME.label} description="欢迎来到 Mirage 主页！精彩内容即将呈现。" />;
}
