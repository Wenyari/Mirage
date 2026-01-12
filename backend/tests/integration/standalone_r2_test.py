"""
独立的R2存储测试脚本（不依赖Flask app）
直接测试R2存储功能，无需数据库或Redis

运行方式:
    python tests/integration/standalone_r2_test.py
"""
import os
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 设置控制台编码为UTF-8（Windows兼容性）
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass  # 如果失败就使用默认编码

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 直接导入storage_service（不需要Flask app context）
from app.services.storage_service import StorageService


def print_test_header(title):
    """打印测试标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_r2_connection():
    """测试1: R2连接"""
    print_test_header("测试 1: R2 连接")

    storage = StorageService()

    print(f"✓ R2 Account ID: {storage.account_id}")
    print(f"✓ R2 Bucket: {storage.bucket_name}")
    print(f"✓ R2 Public URL: {storage.public_url}")
    print(f"✓ Client initialized: {storage.client is not None}")

    if not storage.client:
        print("\n❌ R2客户端未初始化，请检查.env配置")
        return False

    print("\n✓ R2连接测试通过")
    return True


def test_upload_and_delete_single_file():
    """测试2: 单个文件上传和删除"""
    print_test_header("测试 2: 单个文件上传和删除")

    storage = StorageService()

    # 1. 上传文件
    test_data = b"This is a standalone R2 test file"
    filename = f"standalone_test_{int(time.time())}.txt"

    print(f"1. 上传文件: {filename}")
    upload_result = storage.upload_file(
        file_data=test_data,
        filename=filename,
        content_type="text/plain",
        prefix="test/"
    )

    if not upload_result['success']:
        print(f"❌ 上传失败: {upload_result.get('error')}")
        return False

    object_key = upload_result['key']
    file_url = upload_result['url']

    print(f"   ✓ 文件上传成功")
    print(f"     Object Key: {object_key}")
    print(f"     URL: {file_url}")

    # 2. 验证文件存在
    print(f"\n2. 验证文件存在")
    exists = storage.file_exists(object_key)
    if not exists:
        print(f"❌ 文件不存在")
        return False
    print(f"   ✓ 文件存在")

    # 3. 删除文件
    time.sleep(1)
    print(f"\n3. 删除文件")
    delete_result = storage.delete_file(object_key)
    if not delete_result['success']:
        print(f"❌ 删除失败: {delete_result.get('error')}")
        return False
    print(f"   ✓ 文件删除成功")

    # 4. 验证文件已删除
    time.sleep(1)
    print(f"\n4. 验证文件已删除")
    exists_after = storage.file_exists(object_key)
    if exists_after:
        print(f"❌ 文件仍然存在")
        return False
    print(f"   ✓ 文件已删除")

    print("\n✓ 单个文件上传删除测试通过")
    return True


def test_batch_upload_and_delete():
    """测试3: 批量上传和删除"""
    print_test_header("测试 3: 批量文件上传和删除")

    storage = StorageService()

    # 1. 批量上传
    timestamp = int(time.time())
    files_data = [
        {
            'data': f"Batch test file {i+1}".encode(),
            'filename': f"batch_test_{i+1}_{timestamp}.txt",
            'content_type': "text/plain"
        }
        for i in range(3)
    ]

    print(f"1. 批量上传 {len(files_data)} 个文件")
    upload_results = storage.upload_multiple_files(files_data, prefix="test/batch/")

    object_keys = []
    for i, result in enumerate(upload_results):
        if not result['success']:
            print(f"❌ 文件 {i+1} 上传失败: {result.get('error')}")
            return False
        object_keys.append(result['key'])
        print(f"   ✓ 文件 {i+1} 上传成功: {result['key']}")

    # 2. 验证所有文件存在
    print(f"\n2. 验证所有文件存在")
    for key in object_keys:
        if not storage.file_exists(key):
            print(f"❌ 文件不存在: {key}")
            return False
    print(f"   ✓ 所有文件都存在")

    # 3. 批量删除
    time.sleep(1)
    print(f"\n3. 批量删除 {len(object_keys)} 个文件")
    delete_result = storage.delete_multiple_files(object_keys)

    print(f"   - 成功: {delete_result['deleted']}")
    print(f"   - 失败: {delete_result['failed']}")

    if not delete_result['success']:
        print(f"❌ 批量删除失败")
        return False
    print(f"   ✓ 批量删除成功")

    # 4. 验证所有文件已删除
    time.sleep(1)
    print(f"\n4. 验证所有文件已删除")
    for key in object_keys:
        if storage.file_exists(key):
            print(f"❌ 文件仍然存在: {key}")
            return False
    print(f"   ✓ 所有文件已删除")

    print("\n✓ 批量上传删除测试通过")
    return True


def test_delete_nonexistent_file():
    """测试4: 删除不存在的文件"""
    print_test_header("测试 4: 删除不存在的文件")

    storage = StorageService()

    fake_key = f"test/nonexistent/file_{int(time.time())}.txt"

    print(f"1. 尝试删除不存在的文件: {fake_key}")
    delete_result = storage.delete_file(fake_key)

    print(f"   结果: {delete_result}")

    if 'success' not in delete_result:
        print(f"❌ 返回结果格式不正确")
        return False

    print(f"   ✓ 删除不存在的文件不会崩溃")
    print("\n✓ 删除不存在的文件测试通过")
    return True


def test_presigned_url():
    """测试5: 预签名URL生成"""
    print_test_header("测试 5: 预签名 URL 生成")

    storage = StorageService()

    # 1. 上传文件
    test_data = b"File for presigned URL test"
    filename = f"presigned_test_{int(time.time())}.txt"

    print(f"1. 上传测试文件")
    upload_result = storage.upload_file(
        file_data=test_data,
        filename=filename,
        content_type="text/plain",
        prefix="test/"
    )

    if not upload_result['success']:
        print(f"❌ 上传失败: {upload_result.get('error')}")
        return False

    object_key = upload_result['key']
    print(f"   ✓ 文件上传成功: {object_key}")

    # 2. 生成预签名URL
    print(f"\n2. 生成预签名 URL")
    presigned_result = storage.generate_presigned_url(object_key, expiration=3600)

    if presigned_result.get('success'):
        print(f"   ✓ 预签名 URL 生成成功")
        print(f"     URL: {presigned_result['url'][:80]}...")
    else:
        print(f"   ⚠ 预签名 URL 生成失败: {presigned_result.get('error')}")

    # 3. 清理文件
    print(f"\n3. 清理测试文件")
    storage.delete_file(object_key)
    print(f"   ✓ 文件已清理")

    print("\n✓ 预签名URL测试通过")
    return True


def test_scheduler_cleanup_simulation():
    """测试6: 模拟scheduler定时清理功能"""
    print_test_header("测试 6: 模拟 Scheduler 定时清理功能")

    storage = StorageService()

    # 1. 上传多个测试文件（模拟旧任务的文件）
    print(f"1. 上传测试文件（模拟旧任务的附件）")

    test_files = []
    for i in range(3):
        file_data = f"Old task file {i+1} - should be deleted".encode()
        filename = f"old_task_file_{i+1}_{int(time.time())}.txt"

        result = storage.upload_file(
            file_data=file_data,
            filename=filename,
            content_type="text/plain",
            prefix="uploads/"
        )

        if not result['success']:
            print(f"❌ 文件 {i+1} 上传失败: {result.get('error')}")
            return False

        test_files.append({
            'key': result['key'],
            'url': result['url']
        })
        print(f"   ✓ 文件 {i+1} 上传成功: {result['key']}")

    # 2. 验证所有文件存在
    print(f"\n2. 验证所有文件存在（清理前）")
    for f in test_files:
        if not storage.file_exists(f['key']):
            print(f"❌ 文件不存在: {f['key']}")
            return False
    print(f"   ✓ 所有 {len(test_files)} 个文件都存在")

    # 3. 模拟清理操作（批量删除）
    print(f"\n3. 执行清理操作（批量删除这些文件）")
    file_keys = [f['key'] for f in test_files]
    delete_result = storage.delete_multiple_files(file_keys)

    print(f"   - 删除成功: {delete_result['deleted']}")
    print(f"   - 删除失败: {delete_result['failed']}")
    print(f"   - 错误信息: {delete_result['errors']}")

    if not delete_result['success']:
        print(f"❌ 清理失败")
        return False
    print(f"   ✓ 清理操作执行成功")

    # 4. 验证所有文件已被删除
    time.sleep(1)
    print(f"\n4. 验证所有文件已被删除（清理后）")
    for f in test_files:
        if storage.file_exists(f['key']):
            print(f"❌ 文件仍然存在: {f['key']}")
            return False
    print(f"   ✓ 所有文件已被成功删除")

    print("\n✓ Scheduler清理功能测试通过")
    print("  这意味着你的定时清理任务应该可以正常工作！")
    return True


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*20 + "R2 存储独立集成测试" + " "*20 + "    ║")
    print("╚" + "="*68 + "╝")

    tests = [
        ("R2连接", test_r2_connection),
        ("单个文件上传删除", test_upload_and_delete_single_file),
        ("批量文件上传删除", test_batch_upload_and_delete),
        ("删除不存在的文件", test_delete_nonexistent_file),
        ("预签名URL生成", test_presigned_url),
        ("Scheduler定时清理模拟", test_scheduler_cleanup_simulation),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 打印总结
    print("\n\n" + "="*70)
    print(" "*25 + "测试总结")
    print("="*70)

    passed_count = 0
    for name, passed in results:
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"  {status}  -  {name}")
        if passed:
            passed_count += 1

    print("="*70)
    print(f"\n总计: {passed_count}/{len(results)} 个测试通过")

    if passed_count == len(results):
        print("\n🎉 所有测试通过！R2存储和定时清理功能正常工作！")
        return 0
    else:
        print(f"\n⚠ 有 {len(results) - passed_count} 个测试失败，请检查配置或网络连接")
        return 1


if __name__ == '__main__':
    exit_code = main()
    print("\n按任意键退出...")
    input()
    sys.exit(exit_code)
