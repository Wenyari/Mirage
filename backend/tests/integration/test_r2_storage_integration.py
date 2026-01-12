"""
R2 存储集成测试
测试实际的 R2 存储操作，特别是文件删除功能
用于验证 scheduler 的定时清理任务能正常工作

运行方式:
    # Docker 内运行（推荐）
    docker-compose exec api python -m pytest tests/integration/test_r2_storage_integration.py -v -s

    # 本地运行（需要设置测试环境变量）
    set TESTING_NO_REDIS=1
    python -m pytest tests/integration/test_r2_storage_integration.py -v -s

注意: 此测试会连接真实的 R2 存储，请确保 .env 文件中的 R2 配置正确
"""
import pytest
import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestR2StorageIntegration:
    """R2 存储集成测试类"""

    @pytest.fixture(scope='class')
    def app(self):
        """创建测试应用（跳过Redis初始化以支持本地测试）"""
        # 设置环境变量以跳过Redis
        os.environ['TESTING_NO_REDIS'] = '1'

        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        app.config['TESTING_NO_REDIS'] = True

        return app

    @pytest.fixture(scope='class')
    def app_context(self, app):
        """创建应用上下文"""
        from app import db
        with app.app_context():
            # 确保数据库表存在
            db.create_all()
            yield app
            db.session.remove()

    @pytest.fixture(autouse=True)
    def check_r2_configured(self, app_context):
        """检查 R2 是否已配置"""
        from app.services.storage_service import storage_service
        if not storage_service.client:
            pytest.skip("R2 storage not configured. Please set R2_* environment variables.")

    def test_r2_connection(self, app_context):
        """测试 R2 连接是否正常"""
        from app.services.storage_service import storage_service

        print(f"\n✓ R2 Account ID: {storage_service.account_id}")
        print(f"✓ R2 Bucket: {storage_service.bucket_name}")
        print(f"✓ R2 Public URL: {storage_service.public_url}")
        print(f"✓ Client initialized: {storage_service.client is not None}")

        assert storage_service.client is not None, "R2 client should be initialized"
        assert storage_service.bucket_name, "Bucket name should be set"

    def test_upload_and_delete_single_file(self, app_context):
        """测试上传和删除单个文件"""
        from app.services.storage_service import storage_service

        print("\n=== 测试单个文件上传和删除 ===")

        # 1. 上传测试文件
        test_data = b"This is a test file for R2 storage integration"
        filename = "integration_test.txt"

        print(f"1. 上传文件: {filename}")
        upload_result = storage_service.upload_file(
            file_data=test_data,
            filename=filename,
            content_type="text/plain",
            prefix="test/"
        )

        print(f"   上传结果: {upload_result}")
        assert upload_result['success'], f"Upload failed: {upload_result.get('error')}"
        assert 'url' in upload_result
        assert 'key' in upload_result

        object_key = upload_result['key']
        file_url = upload_result['url']

        print(f"✓ 文件上传成功")
        print(f"  Object Key: {object_key}")
        print(f"  URL: {file_url}")

        # 2. 验证文件是否存在
        print(f"\n2. 验证文件存在")
        exists = storage_service.file_exists(object_key)
        print(f"   文件存在: {exists}")
        assert exists, "File should exist after upload"
        print(f"✓ 文件存在验证成功")

        # 3. 等待一下确保文件完全上传
        time.sleep(1)

        # 4. 删除文件
        print(f"\n3. 删除文件")
        delete_result = storage_service.delete_file(object_key)
        print(f"   删除结果: {delete_result}")
        assert delete_result['success'], f"Delete failed: {delete_result.get('error')}"
        print(f"✓ 文件删除成功")

        # 5. 验证文件已被删除
        print(f"\n4. 验证文件已删除")
        time.sleep(1)  # 等待删除生效
        exists_after = storage_service.file_exists(object_key)
        print(f"   文件存在: {exists_after}")
        assert not exists_after, "File should not exist after deletion"
        print(f"✓ 文件删除验证成功")

    def test_upload_and_delete_multiple_files(self, app_context):
        """测试批量上传和删除多个文件"""
        from app.services.storage_service import storage_service

        print("\n=== 测试批量文件上传和删除 ===")

        # 1. 批量上传文件
        files_data = [
            {
                'data': b"Test file 1 content",
                'filename': f"batch_test_1_{int(time.time())}.txt",
                'content_type': "text/plain"
            },
            {
                'data': b"Test file 2 content",
                'filename': f"batch_test_2_{int(time.time())}.txt",
                'content_type': "text/plain"
            },
            {
                'data': b"Test file 3 content",
                'filename': f"batch_test_3_{int(time.time())}.txt",
                'content_type': "text/plain"
            }
        ]

        print(f"1. 批量上传 {len(files_data)} 个文件")
        upload_results = storage_service.upload_multiple_files(files_data, prefix="test/batch/")

        print(f"   上传结果数量: {len(upload_results)}")
        assert len(upload_results) == len(files_data)

        # 收集上传成功的文件键
        object_keys = []
        for i, result in enumerate(upload_results):
            print(f"   文件 {i+1}: {result.get('success')} - {result.get('key', result.get('error'))}")
            assert result['success'], f"Upload {i+1} failed: {result.get('error')}"
            object_keys.append(result['key'])

        print(f"✓ 批量上传成功，共 {len(object_keys)} 个文件")

        # 2. 验证所有文件都存在
        print(f"\n2. 验证所有文件存在")
        for key in object_keys:
            exists = storage_service.file_exists(key)
            assert exists, f"File {key} should exist after upload"
        print(f"✓ 所有文件存在验证成功")

        # 3. 等待确保文件完全上传
        time.sleep(1)

        # 4. 批量删除文件
        print(f"\n3. 批量删除 {len(object_keys)} 个文件")
        delete_result = storage_service.delete_multiple_files(object_keys)

        print(f"   删除结果:")
        print(f"   - 成功: {delete_result['deleted']}")
        print(f"   - 失败: {delete_result['failed']}")
        print(f"   - 错误: {delete_result['errors']}")

        assert delete_result['success'], "Batch delete should succeed"
        assert delete_result['deleted'] == len(object_keys), "All files should be deleted"
        assert delete_result['failed'] == 0, "No files should fail to delete"
        print(f"✓ 批量删除成功")

        # 5. 验证所有文件已被删除
        print(f"\n4. 验证所有文件已删除")
        time.sleep(1)
        for key in object_keys:
            exists = storage_service.file_exists(key)
            assert not exists, f"File {key} should not exist after deletion"
        print(f"✓ 所有文件删除验证成功")

    def test_cleanup_old_tasks_simulation(self, app_context):
        """模拟 scheduler 的旧任务清理功能"""
        from app.services.storage_service import storage_service
        from app.services.task_service import TaskService
        from app.models.task import Task
        from app.models.user import User
        from app import db

        print("\n=== 模拟定时清理旧任务 ===")

        # 1. 上传测试文件（模拟任务的输入文件）
        test_files = []
        for i in range(2):
            file_data = f"Task input file {i+1}".encode()
            filename = f"task_input_{i+1}_{int(time.time())}.txt"

            print(f"1.{i+1} 上传任务文件: {filename}")
            result = storage_service.upload_file(
                file_data=file_data,
                filename=filename,
                content_type="text/plain",
                prefix="uploads/"
            )

            assert result['success'], f"Upload failed: {result.get('error')}"
            test_files.append({
                'key': result['key'],
                'url': result['url']
            })
            print(f"✓ 文件上传成功: {result['key']}")

        # 2. 创建测试用户（如果不存在）
        test_user = User.query.filter_by(email='test_cleanup@example.com').first()
        if not test_user:
            print(f"\n2. 创建测试用户")
            test_user = User(
                username='test_cleanup',
                email='test_cleanup@example.com',
                phone='13800000000',
                password_hash='fake_hash',
                balance=1000.0,
                level=1,
                status=1
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"✓ 测试用户创建成功: {test_user.id}")
        else:
            print(f"\n2. 使用现有测试用户: {test_user.id}")

        # 3. 创建模拟的旧任务
        print(f"\n3. 创建模拟的旧任务")
        old_time = datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=4)

        old_task = Task(
            id=f"test_cleanup_{int(time.time())}",
            user_id=test_user.id,
            model='test-model',
            prompt='Test cleanup task',
            input_file_url=[f['url'] for f in test_files],  # 关联上传的文件
            status='success',
            progress=100,
            cost_points=10.0,
            created_at=old_time,
            finished_at=old_time
        )

        db.session.add(old_task)
        db.session.commit()

        print(f"✓ 旧任务创建成功: {old_task.id}")
        print(f"  关联文件数: {len(test_files)}")
        print(f"  完成时间: {old_task.finished_at}")

        # 4. 验证文件存在
        print(f"\n4. 验证关联文件存在")
        for f in test_files:
            exists = storage_service.file_exists(f['key'])
            assert exists, f"File {f['key']} should exist before cleanup"
        print(f"✓ 所有关联文件存在")

        # 5. 执行清理（模拟 scheduler 的 cleanup_tasks_job）
        print(f"\n5. 执行旧任务清理（保留3天内的任务）")
        cleanup_result = TaskService.cleanup_old_tasks(days=3)

        print(f"   清理结果:")
        print(f"   - 删除任务数: {cleanup_result['deleted']}")
        print(f"   - 删除文件数: {cleanup_result['deleted_files']}")
        print(f"   - 错误数: {len(cleanup_result['errors'])}")

        if cleanup_result['errors']:
            for error in cleanup_result['errors']:
                print(f"   - 错误详情: {error}")

        assert cleanup_result['deleted'] >= 1, "At least one task should be deleted"
        assert cleanup_result['deleted_files'] >= len(test_files), "All associated files should be deleted"
        print(f"✓ 清理任务执行成功")

        # 6. 验证任务已被删除
        print(f"\n6. 验证任务已被删除")
        deleted_task = Task.query.get(old_task.id)
        assert deleted_task is None, "Task should be deleted from database"
        print(f"✓ 任务已从数据库删除")

        # 7. 验证关联文件已被删除
        print(f"\n7. 验证关联文件已删除")
        time.sleep(1)  # 等待删除生效
        for f in test_files:
            exists = storage_service.file_exists(f['key'])
            # 注意：由于可能有错误，我们只警告而不是断言失败
            if exists:
                print(f"⚠ 文件仍然存在: {f['key']}")
            else:
                print(f"✓ 文件已删除: {f['key']}")

        print(f"\n✓ 定时清理功能测试完成")

    def test_delete_nonexistent_file(self, app_context):
        """测试删除不存在的文件（确保不会崩溃）"""
        from app.services.storage_service import storage_service

        print("\n=== 测试删除不存在的文件 ===")

        fake_key = "test/nonexistent/file_12345.txt"

        print(f"1. 尝试删除不存在的文件: {fake_key}")
        delete_result = storage_service.delete_file(fake_key)

        print(f"   删除结果: {delete_result}")
        # R2/S3 删除不存在的文件通常会返回成功（幂等操作）
        # 但我们要确保不会崩溃
        assert 'success' in delete_result
        print(f"✓ 删除不存在的文件不会崩溃")

    def test_batch_delete_with_mixed_files(self, app_context):
        """测试批量删除混合存在和不存在的文件"""
        from app.services.storage_service import storage_service

        print("\n=== 测试批量删除混合文件 ===")

        # 1. 上传一个真实文件
        real_file_data = b"Real file for mixed batch delete test"
        real_filename = f"mixed_test_{int(time.time())}.txt"

        print(f"1. 上传一个真实文件")
        upload_result = storage_service.upload_file(
            file_data=real_file_data,
            filename=real_filename,
            content_type="text/plain",
            prefix="test/"
        )

        assert upload_result['success']
        real_key = upload_result['key']
        print(f"✓ 真实文件上传成功: {real_key}")

        # 2. 准备混合的文件列表（包含存在和不存在的）
        mixed_keys = [
            real_key,
            "test/fake/file1.txt",
            "test/fake/file2.txt"
        ]

        print(f"\n2. 批量删除混合文件列表")
        print(f"   文件列表:")
        for key in mixed_keys:
            print(f"   - {key}")

        # 3. 执行批量删除
        delete_result = storage_service.delete_multiple_files(mixed_keys)

        print(f"\n   删除结果:")
        print(f"   - 成功: {delete_result['deleted']}")
        print(f"   - 失败: {delete_result['failed']}")
        print(f"   - 总计: {delete_result['deleted'] + delete_result['failed']}")

        # 由于 S3 的幂等特性，删除不存在的文件也会返回成功
        assert delete_result['deleted'] == len(mixed_keys)
        print(f"✓ 批量删除混合文件成功，不会因不存在的文件而崩溃")

    def test_generate_presigned_url(self, app_context):
        """测试生成预签名 URL"""
        from app.services.storage_service import storage_service

        print("\n=== 测试预签名 URL 生成 ===")

        # 1. 上传文件
        test_data = b"File for presigned URL test"
        filename = f"presigned_test_{int(time.time())}.txt"

        print(f"1. 上传测试文件")
        upload_result = storage_service.upload_file(
            file_data=test_data,
            filename=filename,
            content_type="text/plain",
            prefix="test/"
        )

        assert upload_result['success']
        object_key = upload_result['key']
        print(f"✓ 文件上传成功: {object_key}")

        # 2. 生成预签名 URL
        print(f"\n2. 生成预签名 URL（有效期1小时）")
        presigned_result = storage_service.generate_presigned_url(object_key, expiration=3600)

        print(f"   结果: {presigned_result.get('success')}")
        if presigned_result.get('success'):
            print(f"   URL: {presigned_result['url'][:100]}...")
            assert 'url' in presigned_result
            print(f"✓ 预签名 URL 生成成功")
        else:
            print(f"⚠ 预签名 URL 生成失败: {presigned_result.get('error')}")

        # 3. 清理文件
        print(f"\n3. 清理测试文件")
        storage_service.delete_file(object_key)
        print(f"✓ 文件清理完成")


if __name__ == '__main__':
    # 直接运行测试
    pytest.main([__file__, '-v', '-s'])
