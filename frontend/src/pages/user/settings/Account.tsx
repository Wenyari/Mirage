import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { useCurrentUser } from '@/hooks/useCurrentUser';
import { userService } from '@/services/user';

export default function Account() {
  const { data: currentUser, refetch } = useCurrentUser();
  const [isLoading, setIsLoading] = useState(false);

  // 用户名修改
  const [showNameForm, setShowNameForm] = useState(false);
  const [name, setName] = useState('');
  const [isUpdatingName, setIsUpdatingName] = useState(false);

  // 密码修改
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);

  useEffect(() => {
    if (currentUser) {
      setName(currentUser.name || '');
    }
  }, [currentUser]);

  const handleUpdateName = async () => {
    if (!name.trim()) {
      toast.error('请输入用户名');
      return;
    }

    if (name.length > 50) {
      toast.error('用户名长度不能超过50个字符');
      return;
    }

    setIsUpdatingName(true);
    try {
      await userService.updateUserInfo({ name: name.trim() });
      await refetch();
      toast.success('用户名更新成功');
      setShowNameForm(false);
    } catch (error: any) {
      console.error('Name update error:', error);
      const errorMessage = error?.response?.data?.msg ||
        error?.response?.data?.message ||
        error?.message ||
        '用户名更新失败，请稍后重试';
      toast.error(errorMessage);
    } finally {
      setIsUpdatingName(false);
    }
  };

  const handleCancelNameChange = () => {
    setName(currentUser?.name || '');
    setShowNameForm(false);
  };

  const handleUpdatePassword = async () => {
    if (!currentPassword) {
      toast.error('请输入当前密码');
      return;
    }

    if (!newPassword) {
      toast.error('请输入新密码');
      return;
    }

    if (newPassword.length < 6) {
      toast.error('新密码长度至少6个字符');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('两次输入的密码不一致');
      return;
    }

    setIsUpdatingPassword(true);
    try {
      await userService.updateUserInfo({
        current_password: currentPassword,
        new_password: newPassword
      });
      toast.success('密码更新成功');

      // 清空表单并隐藏
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowPasswordForm(false);
    } catch (error: any) {
      console.error('Password update error:', error);
      const errorMessage = error?.response?.data?.msg ||
        error?.response?.data?.message ||
        error?.message ||
        '密码输入错误，请重新输入';
      toast.error(errorMessage);
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  const handleCancelPasswordChange = () => {
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setShowPasswordForm(false);
  };

  if (!currentUser) {
    return (
      <div className="flex items-center justify-center p-6">
        <Card className="w-full max-w-3xl p-12 text-center">
          <p className="text-muted-foreground">加载中...</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">账户设置</h1>
      </div>

      <div className="grid gap-6">
        {/* 基本信息 */}
        <Card>
          <CardHeader>
            <CardTitle>基本信息</CardTitle>
            <CardDescription>查看和管理您的账户基本信息</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* 头像区域 */}
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-6 text-center sm:text-left">
              <Avatar className="size-20 sm:size-24">
                <AvatarImage src={currentUser.avatar} alt={currentUser.name || currentUser.email} />
                <AvatarFallback className="text-lg sm:text-xl">
                  {(currentUser.name || currentUser.email || 'U').charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="space-y-2">
                <h3 className="text-lg sm:text-xl font-semibold">{currentUser.name || '未设置用户名'}</h3>
                <p className="text-sm text-muted-foreground break-all">{currentUser.email}</p>
                <div className="flex items-center justify-center sm:justify-start gap-2">
                  <Badge variant="secondary">
                    {currentUser.level === 1 ? 'T1' :
                      currentUser.level === 2 ? 'T2' :
                        currentUser.level === 3 ? 'T3' :
                          currentUser.level === 4 ? 'T4' : 'T5'} 会员
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    注册于: {new Date(currentUser.created_at).toLocaleDateString('zh-CN')}
                  </span>
                </div>
              </div>
            </div>

            <Separator />

            {/* 用户名修改 */}
            <div className="space-y-4">
              <div>
                <Label>用户名</Label>
                <p className="text-sm text-muted-foreground mb-2">
                  设置您的显示名称，最多50个字符
                </p>
                {!showNameForm ? (
                  <Button
                    onClick={() => setShowNameForm(true)}
                    variant="outline"
                    className="w-full sm:w-auto"
                  >
                    修改用户名
                  </Button>
                ) : (
                  <>
                    <div className="flex gap-2 mb-2">
                      <Input
                        id="name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="请输入用户名"
                        maxLength={50}
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleUpdateName}
                        disabled={isUpdatingName}
                      >
                        {isUpdatingName ? '更新中...' : '确认修改'}
                      </Button>
                      <Button
                        onClick={handleCancelNameChange}
                        variant="outline"
                        disabled={isUpdatingName}
                      >
                        取消
                      </Button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 安全设置 */}
        <Card>
          <CardHeader>
            <CardTitle>安全设置</CardTitle>
            <CardDescription>修改您的密码以保护账户安全</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!showPasswordForm ? (
              <Button
                onClick={() => setShowPasswordForm(true)}
                variant="outline"
                className="w-full sm:w-auto"
              >
                修改密码
              </Button>
            ) : (
              <>
                <div className="grid gap-4">
                  <div>
                    <Label htmlFor="current-password">当前密码</Label>
                    <Input
                      id="current-password"
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="请输入当前密码"
                    />
                  </div>
                  <div>
                    <Label htmlFor="new-password">新密码</Label>
                    <Input
                      id="new-password"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="请输入新密码（至少6位）"
                    />
                  </div>
                  <div>
                    <Label htmlFor="confirm-password">确认新密码</Label>
                    <Input
                      id="confirm-password"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="请再次输入新密码"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={handleUpdatePassword}
                    disabled={isUpdatingPassword}
                  >
                    {isUpdatingPassword ? '更新中...' : '确认修改'}
                  </Button>
                  <Button
                    onClick={handleCancelPasswordChange}
                    variant="outline"
                    disabled={isUpdatingPassword}
                  >
                    取消
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* 头像设置提示 */}
        <Card>
          <CardHeader>
            <CardTitle>头像设置</CardTitle>
            <CardDescription>头像上传功能正在开发中</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              头像上传功能将在后续版本中推出，敬请期待。
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}


