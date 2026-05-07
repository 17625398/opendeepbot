"""
笔录分析API测试脚本
测试所有82个端点的可用性和基本功能
"""

import asyncio
import json
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

import pytest
import httpx

# API基础URL
BASE_URL = "http://localhost:8001/api/v1"


@dataclass
class TestResult:
    """测试结果"""
    endpoint: str
    method: str
    status: str  # 'passed', 'failed', 'skipped'
    response_time: float
    status_code: int = 0
    error_message: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class InterrogationAPITester:
    """笔录分析API测试器"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self.results: List[TestResult] = []
        self.test_case_id = f"test_case_{int(time.time())}"
        self.test_record_id = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> TestResult:
        """发送请求并记录结果"""
        start_time = time.time()
        result = TestResult(
            endpoint=endpoint,
            method=method,
            status='failed',
            response_time=0.0
        )
        
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            result.response_time = time.time() - start_time
            result.status_code = response.status_code
            
            # 2xx 状态码视为成功
            if 200 <= response.status_code < 300:
                result.status = 'passed'
            elif response.status_code == 404:
                # 404 可能是正常的（资源不存在）
                result.status = 'passed'
            else:
                result.status = 'failed'
                result.error_message = f"Unexpected status code: {response.status_code}"
            
        except httpx.ConnectError as e:
            result.status = 'failed'
            result.error_message = f"Connection error: {str(e)}"
        except httpx.TimeoutException as e:
            result.status = 'failed'
            result.error_message = f"Timeout: {str(e)}"
        except Exception as e:
            result.status = 'failed'
            result.error_message = f"Error: {str(e)}"
        
        self.results.append(result)
        return result
    
    # ==================== 案件管理测试 ====================
    
    async def test_get_cases(self):
        """测试获取案件列表"""
        return await self._make_request('GET', '/interrogation/cases')
    
    async def test_get_case(self):
        """测试获取案件详情"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}')
    
    async def test_create_case(self):
        """测试创建案件"""
        data = {
            "case_id": self.test_case_id,
            "title": "测试案件",
            "description": "这是一个测试案件"
        }
        return await self._make_request('POST', '/interrogation/cases', json=data)
    
    async def test_update_case(self):
        """测试更新案件"""
        data = {"title": "更新的测试案件"}
        return await self._make_request('PUT', f'/interrogation/cases/{self.test_case_id}', json=data)
    
    async def test_delete_case(self):
        """测试删除案件"""
        return await self._make_request('DELETE', f'/interrogation/cases/{self.test_case_id}')
    
    async def test_batch_delete_cases(self):
        """测试批量删除案件"""
        data = {"case_ids": [self.test_case_id]}
        return await self._make_request('DELETE', '/interrogation/cases', json=data)
    
    async def test_get_case_stats(self):
        """测试获取案件统计"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}/stats')
    
    async def test_search_cases(self):
        """测试搜索案件"""
        return await self._make_request('GET', '/interrogation/cases/search?query=test')
    
    async def test_get_case_timeline(self):
        """测试获取案件时间线"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}/timeline')
    
    async def test_import_case(self):
        """测试导入案件"""
        data = {"seafile_path": "/test/path"}
        return await self._make_request('POST', '/interrogation/cases/import', json=data)
    
    async def test_export_case(self):
        """测试导出案件"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}/export')
    
    async def test_get_recycle_bin(self):
        """测试获取回收站"""
        return await self._make_request('GET', '/interrogation/cases/recycle-bin')
    
    async def test_restore_case(self):
        """测试恢复案件"""
        return await self._make_request('POST', f'/interrogation/cases/{self.test_case_id}/restore')
    
    async def test_permanent_delete_case(self):
        """测试永久删除案件"""
        return await self._make_request('DELETE', f'/interrogation/cases/{self.test_case_id}/permanent')
    
    # ==================== 笔录管理测试 ====================
    
    async def test_get_records(self):
        """测试获取笔录列表"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}/records')
    
    async def test_get_record(self):
        """测试获取笔录详情"""
        record_id = self.test_record_id or "test_record"
        return await self._make_request('GET', f'/interrogation/records/{record_id}')
    
    async def test_create_record(self):
        """测试创建笔录"""
        data = {
            "case_id": self.test_case_id,
            "interrogator": "测试人员",
            "interviewee": "被询问人",
            "time": datetime.now().isoformat(),
            "location": "测试地点",
            "content": "测试笔录内容"
        }
        return await self._make_request('POST', '/interrogation/records', json=data)
    
    async def test_update_record(self):
        """测试更新笔录"""
        record_id = self.test_record_id or "test_record"
        data = {"content": "更新的笔录内容"}
        return await self._make_request('PUT', f'/interrogation/records/{record_id}', json=data)
    
    async def test_delete_record(self):
        """测试删除笔录"""
        record_id = self.test_record_id or "test_record"
        return await self._make_request('DELETE', f'/interrogation/records/{record_id}')
    
    async def test_batch_delete_records(self):
        """测试批量删除笔录"""
        data = {"record_ids": ["test_record_1", "test_record_2"]}
        return await self._make_request('DELETE', '/interrogation/records', json=data)
    
    async def test_analyze_record(self):
        """测试分析笔录"""
        record_id = self.test_record_id or "test_record"
        return await self._make_request('POST', f'/interrogation/records/{record_id}/analyze')
    
    async def test_batch_analyze_records(self):
        """测试批量分析笔录"""
        data = {
            "case_id": self.test_case_id,
            "records": [],
            "analyze_cross_relations": True
        }
        return await self._make_request('POST', '/interrogation/records/batch-analyze', json=data)
    
    # ==================== 知识库管理测试 ====================
    
    async def test_get_vaults(self):
        """测试获取知识库列表"""
        return await self._make_request('GET', '/interrogation/vaults')
    
    async def test_get_vault(self):
        """测试获取知识库详情"""
        return await self._make_request('GET', '/interrogation/vaults/case_materials')
    
    async def test_create_vault(self):
        """测试创建知识库"""
        data = {"name": "test_vault", "description": "测试知识库"}
        return await self._make_request('POST', '/interrogation/vaults', json=data)
    
    async def test_update_vault(self):
        """测试更新知识库"""
        data = {"description": "更新的描述"}
        return await self._make_request('PUT', '/interrogation/vaults/case_materials', json=data)
    
    async def test_delete_vault(self):
        """测试删除知识库"""
        return await self._make_request('DELETE', '/interrogation/vaults/test_vault')
    
    # ==================== 材料管理测试 ====================
    
    async def test_get_materials(self):
        """测试获取材料列表"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}/materials')
    
    async def test_get_material(self):
        """测试获取材料详情"""
        return await self._make_request('GET', '/interrogation/materials/test_material')
    
    async def test_create_material(self):
        """测试创建材料"""
        data = {
            "name": "测试材料",
            "material_type": "evidence",
            "description": "测试材料描述"
        }
        return await self._make_request('POST', '/interrogation/materials', json=data)
    
    async def test_update_material(self):
        """测试更新材料"""
        data = {"name": "更新的材料名称"}
        return await self._make_request('PUT', '/interrogation/materials/test_material', json=data)
    
    async def test_delete_material(self):
        """测试删除材料"""
        return await self._make_request('DELETE', '/interrogation/materials/test_material')
    
    async def test_batch_update_material_status(self):
        """测试批量更新材料状态"""
        data = {"material_ids": ["mat1", "mat2"], "status": "verified"}
        return await self._make_request('POST', '/interrogation/materials/batch-update-status', json=data)
    
    async def test_batch_delete_materials(self):
        """测试批量删除材料"""
        data = {"material_ids": ["mat1", "mat2"]}
        return await self._make_request('DELETE', '/interrogation/materials/batch', json=data)
    
    # ==================== 导入导出测试 ====================
    
    async def test_export_records(self):
        """测试导出笔录"""
        data = {"record_ids": ["rec1", "rec2"], "format": "zip"}
        return await self._make_request('POST', '/interrogation/export/records', json=data)
    
    async def test_import_records(self):
        """测试导入笔录"""
        return await self._make_request('POST', '/interrogation/import/records')
    
    async def test_export_analysis(self):
        """测试导出分析结果"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}/export-analysis')
    
    async def test_export_markdown(self):
        """测试导出Markdown"""
        data = {"case_id": self.test_case_id, "kb_name": "case_materials"}
        return await self._make_request('POST', '/interrogation/export/markdown', json=data)
    
    async def test_batch_export(self):
        """测试批量导出"""
        data = {"case_ids": [self.test_case_id], "format_type": "zip"}
        return await self._make_request('POST', '/interrogation/export/batch', json=data)
    
    # ==================== AI功能测试 ====================
    
    async def test_ai_analysis(self):
        """测试AI分析"""
        data = {"case_id": self.test_case_id, "analysis_type": "comprehensive"}
        return await self._make_request('POST', '/interrogation/ai/analysis', json=data)
    
    async def test_ai_chat(self):
        """测试AI对话"""
        data = {"case_id": self.test_case_id, "message": "测试消息"}
        return await self._make_request('POST', '/interrogation/ai/chat', json=data)
    
    async def test_ai_summary(self):
        """测试AI摘要"""
        data = {"case_id": self.test_case_id}
        return await self._make_request('POST', '/interrogation/ai/summary', json=data)
    
    async def test_ai_suggestions(self):
        """测试AI建议"""
        data = {"case_id": self.test_case_id}
        return await self._make_request('POST', '/interrogation/ai/suggestions', json=data)
    
    async def test_ai_legal_match(self):
        """测试法律匹配"""
        data = {"case_id": self.test_case_id}
        return await self._make_request('POST', '/interrogation/ai/legal-match', json=data)
    
    async def test_ai_quality_check(self):
        """测试质量检查"""
        data = {"case_id": self.test_case_id}
        return await self._make_request('POST', '/interrogation/ai/quality-check', json=data)
    
    async def test_ai_evidence_chain(self):
        """测试证据链分析"""
        data = {"case_id": self.test_case_id}
        return await self._make_request('POST', '/interrogation/ai/evidence-chain', json=data)
    
    async def test_ai_contradiction_detect(self):
        """测试矛盾检测"""
        data = {"case_id": self.test_case_id}
        return await self._make_request('POST', '/interrogation/ai/contradiction-detect', json=data)
    
    # ==================== 协作功能测试 ====================
    
    async def test_get_collaborators(self):
        """测试获取协作者"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}/collaborators')
    
    async def test_add_collaborator(self):
        """测试添加协作者"""
        data = {"user_id": "user1", "username": "测试用户", "role": "editor"}
        return await self._make_request('POST', f'/interrogation/cases/{self.test_case_id}/collaborators', json=data)
    
    async def test_update_collaborator_role(self):
        """测试更新协作者角色"""
        data = {"role": "viewer"}
        return await self._make_request('PUT', f'/interrogation/cases/{self.test_case_id}/collaborators/user1', json=data)
    
    async def test_remove_collaborator(self):
        """测试移除协作者"""
        return await self._make_request('DELETE', f'/interrogation/cases/{self.test_case_id}/collaborators/user1')
    
    async def test_get_tasks(self):
        """测试获取任务列表"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}/tasks')
    
    async def test_create_task(self):
        """测试创建任务"""
        data = {"title": "测试任务", "description": "任务描述", "assigned_to": "user1"}
        return await self._make_request('POST', f'/interrogation/cases/{self.test_case_id}/tasks', json=data)
    
    async def test_update_task(self):
        """测试更新任务"""
        data = {"status": "in_progress"}
        return await self._make_request('PUT', '/interrogation/tasks/task1', json=data)
    
    async def test_delete_task(self):
        """测试删除任务"""
        return await self._make_request('DELETE', '/interrogation/tasks/task1')
    
    async def test_get_comments(self):
        """测试获取评论"""
        return await self._make_request('GET', f'/interrogation/cases/{self.test_case_id}/comments')
    
    async def test_add_comment(self):
        """测试添加评论"""
        data = {"content": "测试评论", "target_type": "case", "target_id": self.test_case_id}
        return await self._make_request('POST', f'/interrogation/cases/{self.test_case_id}/comments', json=data)
    
    # ==================== 系统监控测试 ====================
    
    async def test_get_system_status(self):
        """测试获取系统状态"""
        return await self._make_request('GET', '/interrogation/system/status')
    
    async def test_get_system_stats(self):
        """测试获取系统统计"""
        return await self._make_request('GET', '/interrogation/system/stats')
    
    async def test_get_system_logs(self):
        """测试获取系统日志"""
        return await self._make_request('GET', '/interrogation/system/logs')
    
    async def test_get_performance_metrics(self):
        """测试获取性能指标"""
        return await self._make_request('GET', '/interrogation/system/performance')
    
    async def test_get_cache_stats(self):
        """测试获取缓存统计"""
        return await self._make_request('GET', '/interrogation/system/cache-stats')
    
    async def test_health_check(self):
        """测试健康检查"""
        return await self._make_request('GET', '/interrogation/system/health')
    
    async def test_clear_cache(self):
        """测试清除缓存"""
        return await self._make_request('POST', '/interrogation/system/clear-cache')
    
    # ==================== 模拟分析测试 ====================
    
    async def test_create_simulation(self):
        """测试创建模拟"""
        data = {"case_id": self.test_case_id, "title": "测试模拟"}
        return await self._make_request('POST', '/interrogation/simulations', json=data)
    
    async def test_get_simulation(self):
        """测试获取模拟"""
        return await self._make_request('GET', '/interrogation/simulations/sim1')
    
    async def test_run_simulation(self):
        """测试运行模拟"""
        return await self._make_request('POST', '/interrogation/simulations/sim1/run')
    
    async def test_get_simulation_results(self):
        """测试获取模拟结果"""
        return await self._make_request('GET', '/interrogation/simulations/sim1/results')
    
    async def test_stop_simulation(self):
        """测试停止模拟"""
        return await self._make_request('POST', '/interrogation/simulations/sim1/stop')
    
    async def test_delete_simulation(self):
        """测试删除模拟"""
        return await self._make_request('DELETE', '/interrogation/simulations/sim1')
    
    # ==================== 运行所有测试 ====================
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("开始测试笔录分析API...")
        print(f"基础URL: {self.base_url}")
        print("-" * 60)
        
        # 案件管理测试
        print("\n📁 案件管理测试:")
        await self.test_get_cases()
        await self.test_create_case()
        await self.test_get_case()
        await self.test_update_case()
        await self.test_get_case_stats()
        await self.test_search_cases()
        await self.test_get_case_timeline()
        await self.test_import_case()
        await self.test_export_case()
        await self.test_get_recycle_bin()
        await self.test_restore_case()
        await self.test_permanent_delete_case()
        await self.test_delete_case()
        await self.test_batch_delete_cases()
        
        # 笔录管理测试
        print("📝 笔录管理测试:")
        await self.test_get_records()
        await self.test_get_record()
        await self.test_create_record()
        await self.test_update_record()
        await self.test_delete_record()
        await self.test_batch_delete_records()
        await self.test_analyze_record()
        await self.test_batch_analyze_records()
        
        # 知识库管理测试
        print("📚 知识库管理测试:")
        await self.test_get_vaults()
        await self.test_get_vault()
        await self.test_create_vault()
        await self.test_update_vault()
        await self.test_delete_vault()
        
        # 材料管理测试
        print("📎 材料管理测试:")
        await self.test_get_materials()
        await self.test_get_material()
        await self.test_create_material()
        await self.test_update_material()
        await self.test_delete_material()
        await self.test_batch_update_material_status()
        await self.test_batch_delete_materials()
        
        # 导入导出测试
        print("📤 导入导出测试:")
        await self.test_export_records()
        await self.test_import_records()
        await self.test_export_analysis()
        await self.test_export_markdown()
        await self.test_batch_export()
        
        # AI功能测试
        print("🤖 AI功能测试:")
        await self.test_ai_analysis()
        await self.test_ai_chat()
        await self.test_ai_summary()
        await self.test_ai_suggestions()
        await self.test_ai_legal_match()
        await self.test_ai_quality_check()
        await self.test_ai_evidence_chain()
        await self.test_ai_contradiction_detect()
        
        # 协作功能测试
        print("👥 协作功能测试:")
        await self.test_get_collaborators()
        await self.test_add_collaborator()
        await self.test_update_collaborator_role()
        await self.test_remove_collaborator()
        await self.test_get_tasks()
        await self.test_create_task()
        await self.test_update_task()
        await self.test_delete_task()
        await self.test_get_comments()
        await self.test_add_comment()
        
        # 系统监控测试
        print("📊 系统监控测试:")
        await self.test_get_system_status()
        await self.test_get_system_stats()
        await self.test_get_system_logs()
        await self.test_get_performance_metrics()
        await self.test_get_cache_stats()
        await self.test_health_check()
        await self.test_clear_cache()
        
        # 模拟分析测试
        print("🎮 模拟分析测试:")
        await self.test_create_simulation()
        await self.test_get_simulation()
        await self.test_run_simulation()
        await self.test_get_simulation_results()
        await self.test_stop_simulation()
        await self.test_delete_simulation()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == 'passed')
        failed = sum(1 for r in self.results if r.status == 'failed')
        skipped = sum(1 for r in self.results if r.status == 'skipped')
        
        avg_response_time = sum(r.response_time for r in self.results) / total if total > 0 else 0
        
        report = {
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'pass_rate': round(passed / total * 100, 2) if total > 0 else 0,
                'avg_response_time_ms': round(avg_response_time * 1000, 2)
            },
            'failed_tests': [
                {
                    'endpoint': r.endpoint,
                    'method': r.method,
                    'status_code': r.status_code,
                    'error': r.error_message
                }
                for r in self.results if r.status == 'failed'
            ],
            'all_results': [
                {
                    'endpoint': r.endpoint,
                    'method': r.method,
                    'status': r.status,
                    'response_time_ms': round(r.response_time * 1000, 2),
                    'status_code': r.status_code
                }
                for r in self.results
            ]
        }
        
        return report


async def main():
    """主函数"""
    async with InterrogationAPITester() as tester:
        report = await tester.run_all_tests()
        
        # 打印报告
        print("\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)
        
        summary = report['summary']
        print(f"\n总测试数: {summary['total']}")
        print(f"通过: {summary['passed']} ✓")
        print(f"失败: {summary['failed']} ✗")
        print(f"跳过: {summary['skipped']} ⊘")
        print(f"通过率: {summary['pass_rate']}%")
        print(f"平均响应时间: {summary['avg_response_time_ms']}ms")
        
        if report['failed_tests']:
            print("\n失败的测试:")
            for test in report['failed_tests']:
                print(f"  - {test['method']} {test['endpoint']}")
                print(f"    状态码: {test['status_code']}")
                print(f"    错误: {test['error']}")
        
        # 保存报告
        report_file = f"interrogation_api_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
