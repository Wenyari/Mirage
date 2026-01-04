import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ModelConfigsTable } from '@/components/tables/ModelConfigsTable';
import { MembershipConfigCards } from '@/components/admin/MembershipConfigCards';

export default function ModelConfigManager() {
  const [activeTab, setActiveTab] = useState('models');

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">模型配置管理</h1>
        <p className="mt-2 text-muted-foreground">
          管理模型的等级权限、计费配置和会员等级设置
        </p>
      </div>

      {/* Tab 导航 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="models">模型配置</TabsTrigger>
          <TabsTrigger value="membership">会员等级</TabsTrigger>
        </TabsList>

        {/* Tab 1: 模型配置列表 */}
        <TabsContent value="models" className="space-y-4 mt-6">
          <ModelConfigsTable />
        </TabsContent>

        {/* Tab 2: 会员等级配置 */}
        <TabsContent value="membership" className="space-y-4 mt-6">
          <MembershipConfigCards />
        </TabsContent>
      </Tabs>
    </div>
  );
}
