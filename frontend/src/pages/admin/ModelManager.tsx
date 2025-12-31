import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PlatformConfigsTable } from '@/components/tables/PlatformConfigsTable';
import { MembershipConfigCards } from '@/components/admin/MembershipConfigCards';

export default function ModelManager() {
  const [activeTab, setActiveTab] = useState('platforms');

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">平台配置管理</h1>
        <p className="mt-2 text-muted-foreground">
          管理平台的等级权限、计费配置和会员等级设置
        </p>
      </div>

      {/* Tab 导航 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="platforms">平台配置</TabsTrigger>
          <TabsTrigger value="membership">会员等级</TabsTrigger>
        </TabsList>

        {/* Tab 1: 平台配置列表 */}
        <TabsContent value="platforms" className="space-y-4 mt-6">
          <PlatformConfigsTable />
        </TabsContent>

        {/* Tab 2: 会员等级配置 */}
        <TabsContent value="membership" className="space-y-4 mt-6">
          <MembershipConfigCards />
        </TabsContent>
      </Tabs>
    </div>
  );
}
