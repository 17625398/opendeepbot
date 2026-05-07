"""
笔录分析 Pipeline 集成示例

展示如何将 Context Engineering Skills 集成到现有的 InterrogationPipeline 中，
增强多笔录分析能力。
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 导入现有的 Pipeline 和数据结构
from src.agents.interrogation.interrogation_pipeline import InterrogationPipeline
from src.agents.interrogation.data_structures import InterrogationRecord, AnalysisResult

# 导入 Context Engineering Skills
from src.agents.interrogation.skills import (
    MultiRecordAnalysisSkill,
    EvidenceChainBuilderSkill,
    RecordQualityEvaluatorSkill,
    CrossRecordValidatorSkill,
    QualityLevel,
    ValidationSeverity
)


class EnhancedInterrogationPipeline(InterrogationPipeline):
    """
    增强版笔录分析 Pipeline
    
    在原有 InterrogationPipeline 基础上集成 Context Engineering Skills，
    提供更强大的多笔录分析能力。
    """
    
    def __init__(self, output_dir: str = None, kb_name: str = None):
        """
        初始化增强版 Pipeline
        
        Args:
            output_dir: 输出目录
            kb_name: 法律法规知识库名称
        """
        super().__init__(output_dir=output_dir, kb_name=kb_name)
        
        # 初始化 Context Engineering Skills
        self.multi_record_analyzer = MultiRecordAnalysisSkill()
        self.evidence_chain_builder = EvidenceChainBuilderSkill()
        self.quality_evaluator = RecordQualityEvaluatorSkill()
        self.cross_record_validator = CrossRecordValidatorSkill()
        
        self.logger.info("EnhancedInterrogationPipeline 初始化完成，已集成 Context Engineering Skills")
    
    async def analyze_with_skills(
        self,
        records: List[InterrogationRecord],
        enable_quality_check: bool = True,
        enable_cross_validation: bool = True,
        enable_relation_analysis: bool = True,
        enable_evidence_chain: bool = True,
        stream_callback=None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        使用 Context Engineering Skills 分析多份笔录
        
        Args:
            records: 笔录记录列表
            enable_quality_check: 是否启用质量检查
            enable_cross_validation: 是否启用跨笔录验证
            enable_relation_analysis: 是否启用关联分析
            enable_evidence_chain: 是否启用证据链构建
            stream_callback: 流式输出回调
            progress_callback: 进度回调
            
        Returns:
            综合分析结果
        """
        if not records:
            raise ValueError("笔录列表不能为空")
        
        case_id = records[0].case_id if records else f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"开始使用 Skills 分析案件 {case_id}，共 {len(records)} 份笔录")
        
        # 准备输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(self.output_dir) / f"enhanced_{case_id}_{timestamp}"
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            "case_id": case_id,
            "record_count": len(records),
            "analysis_timestamp": timestamp,
            "skills_enabled": {
                "quality_check": enable_quality_check,
                "cross_validation": enable_cross_validation,
                "relation_analysis": enable_relation_analysis,
                "evidence_chain": enable_evidence_chain
            },
            "quality_reports": [],
            "validation_report": None,
            "relation_graph": None,
            "evidence_chains": [],
            "integrated_analysis": None
        }
        
        # 步骤 1: 笔录质量评估
        if enable_quality_check:
            if progress_callback:
                await progress_callback(10, "正在评估笔录质量...")
            
            self.logger.info("步骤 1: 笔录质量评估")
            quality_reports = []
            
            for i, record in enumerate(records):
                report = await self.quality_evaluator.apply({
                    "record": record.content,
                    "record_id": record.record_id or f"record_{i+1}",
                    "record_type": "interrogation"
                })
                quality_reports.append(report)
                
                # 保存质量报告
                summary = self.quality_evaluator.get_quality_summary(report)
                with open(output_path / f"quality_{report.record_id}.txt", "w", encoding="utf-8") as f:
                    f.write(summary)
            
            results["quality_reports"] = quality_reports
            
            # 统计质量情况
            low_quality = [r for r in quality_reports if r.quality_level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE]]
            if low_quality:
                self.logger.warning(f"发现 {len(low_quality)} 份质量较差的笔录")
            else:
                self.logger.info("所有笔录质量良好")
        
        # 步骤 2: 跨笔录验证
        if enable_cross_validation and len(records) >= 2:
            if progress_callback:
                await progress_callback(30, "正在进行跨笔录验证...")
            
            self.logger.info("步骤 2: 跨笔录验证")
            
            # 转换记录格式
            record_dicts = []
            for record in records:
                record_dicts.append({
                    "id": record.record_id or f"record_{len(record_dicts)+1}",
                    "content": record.content,
                    "metadata": {
                        "interviewee": record.interviewee,
                        "time": str(record.time) if record.time else "",
                        "location": record.location
                    }
                })
            
            validation_report = await self.cross_record_validator.apply({
                "records": record_dicts,
                "focus_entities": [],
                "focus_facts": []
            })
            
            results["validation_report"] = validation_report
            
            # 保存验证报告
            summary = self.cross_record_validator.get_validation_summary(validation_report)
            with open(output_path / "cross_validation_report.txt", "w", encoding="utf-8") as f:
                f.write(summary)
            
            self.logger.info(f"跨笔录验证完成，整体一致性: {validation_report.overall_consistency:.1f}%")
            
            if validation_report.critical_issues:
                self.logger.warning(f"发现 {len(validation_report.critical_issues)} 处严重矛盾")
        
        # 步骤 3: 多笔录关联分析
        if enable_relation_analysis:
            if progress_callback:
                await progress_callback(50, "正在进行关联分析...")
            
            self.logger.info("步骤 3: 多笔录关联分析")
            
            # 转换记录格式
            record_dicts = []
            for record in records:
                record_dicts.append({
                    "id": record.record_id or f"record_{len(record_dicts)+1}",
                    "type": "interrogation",
                    "content": record.content,
                    "timestamp": record.time or datetime.now(),
                    "subject": record.interviewee or "Unknown"
                })
            
            relation_graph = await self.multi_record_analyzer.apply({
                "records": record_dicts,
                "case_id": case_id
            })
            
            results["relation_graph"] = relation_graph
            
            # 保存关联图
            graph_dict = self.multi_record_analyzer.graph_to_dict(relation_graph)
            import json
            with open(output_path / "relation_graph.json", "w", encoding="utf-8") as f:
                json.dump(graph_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"关联分析完成，发现 {len(relation_graph.edges)} 个关联关系")
        
        # 步骤 4: 证据链构建
        if enable_evidence_chain:
            if progress_callback:
                await progress_callback(70, "正在构建证据链...")
            
            self.logger.info("步骤 4: 证据链构建")
            
            # 定义目标事实
            target_facts = [
                "案件基本事实",
                "涉案人员关系",
                "时间线",
                "证据充分性"
            ]
            
            # 转换记录格式
            record_dicts = []
            for record in records:
                record_dicts.append({
                    "id": record.record_id or f"record_{len(record_dicts)+1}",
                    "content": record.content,
                    "metadata": {
                        "type": "interrogation",
                        "subject": record.interviewee
                    }
                })
            
            evidence_chains = await self.evidence_chain_builder.apply({
                "records": record_dicts,
                "target_facts": target_facts,
                "case_id": case_id
            })
            
            results["evidence_chains"] = evidence_chains
            
            # 保存证据链
            import json
            chains_data = []
            for chain in evidence_chains:
                chains_data.append({
                    "target_fact": chain.target_fact,
                    "overall_strength": chain.overall_strength.value,
                    "completeness": chain.completeness,
                    "credibility": chain.credibility,
                    "evidence_count": len(chain.evidences),
                    "gaps": chain.gaps
                })
            
            with open(output_path / "evidence_chains.json", "w", encoding="utf-8") as f:
                json.dump(chains_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"证据链构建完成，共 {len(evidence_chains)} 条证据链")
        
        # 步骤 5: 综合分析
        if progress_callback:
            await progress_callback(90, "正在生成综合分析报告...")
        
        self.logger.info("步骤 5: 生成综合分析报告")
        
        integrated_analysis = self._generate_integrated_report(results, records)
        results["integrated_analysis"] = integrated_analysis
        
        # 保存综合分析报告
        with open(output_path / "integrated_analysis_report.md", "w", encoding="utf-8") as f:
            f.write(integrated_analysis)
        
        if progress_callback:
            await progress_callback(100, "分析完成")
        
        self.logger.info(f"增强分析完成，结果保存在: {output_path}")
        
        return results
    
    def _generate_integrated_report(
        self,
        results: Dict[str, Any],
        records: List[InterrogationRecord]
    ) -> str:
        """生成综合分析报告"""
        lines = [
            "# 案件综合分析报告（增强版）",
            "",
            f"**案件编号**: {results['case_id']}",
            f"**分析时间**: {results['analysis_timestamp']}",
            f"**笔录数量**: {results['record_count']} 份",
            "",
            "## 分析模块",
            "",
            "| 模块 | 状态 |",
            "|------|------|",
        ]
        
        for skill, enabled in results['skills_enabled'].items():
            status = "✅ 已启用" if enabled else "❌ 未启用"
            lines.append(f"| {skill} | {status} |")
        
        lines.extend(["", "---", ""])
        
        # 笔录质量评估
        if results['quality_reports']:
            lines.extend([
                "## 一、笔录质量评估",
                "",
            ])
            
            avg_score = sum(r.overall_score for r in results['quality_reports']) / len(results['quality_reports'])
            lines.append(f"**平均质量得分**: {avg_score:.1f}/100")
            lines.append("")
            
            lines.append("### 各笔录质量详情")
            lines.append("")
            lines.append("| 笔录ID | 质量等级 | 综合得分 | 主要问题 |")
            lines.append("|--------|----------|----------|----------|")
            
            for report in results['quality_reports']:
                issues_count = len(report.risk_flags)
                lines.append(f"| {report.record_id} | {report.quality_level.value} | {report.overall_score} | {issues_count} 个风险 |")
            
            lines.append("")
        
        # 跨笔录验证
        if results['validation_report']:
            report = results['validation_report']
            lines.extend([
                "## 二、跨笔录一致性验证",
                "",
                f"**整体一致性**: {report.overall_consistency:.1f}%",
                "",
                "### 各维度一致性",
                "",
                "| 维度 | 得分 | 问题数 |",
                "|------|------|--------|",
            ])
            
            for cs in report.consistency_scores:
                status = "✓" if cs.score >= 70 else "⚠"
                lines.append(f"| {status} {cs.validation_type.value} | {cs.score:.1f}% | {cs.issue_count} |")
            
            lines.append("")
            
            if report.critical_issues:
                lines.extend([
                    "### 严重问题",
                    "",
                ])
                for issue in report.critical_issues:
                    lines.append(f"- 🔴 {issue.description}")
                lines.append("")
            
            if report.major_issues:
                lines.extend([
                    "### 主要问题",
                    "",
                ])
                for issue in report.major_issues[:5]:
                    lines.append(f"- 🟠 {issue.description}")
                lines.append("")
        
        # 关联分析
        if results['relation_graph']:
            graph = results['relation_graph']
            lines.extend([
                "## 三、笔录关联分析",
                "",
                f"**笔录节点数**: {len(graph.nodes)}",
                f"**关联关系数**: {len(graph.edges)}",
                "",
                "### 关联关系类型分布",
                "",
            ])
            
            from collections import Counter
            relation_types = Counter([e.relation_type.value for e in graph.edges])
            for rel_type, count in relation_types.most_common():
                lines.append(f"- {rel_type}: {count} 个")
            
            lines.append("")
            
            # 时间线
            timeline = graph.get_timeline()
            if timeline:
                lines.extend([
                    "### 事件时间线",
                    "",
                ])
                for item in timeline[:10]:  # 最多显示10个
                    lines.append(f"- [{item['timestamp']}] {item['event']}")
                lines.append("")
        
        # 证据链分析
        if results['evidence_chains']:
            lines.extend([
                "## 四、证据链分析",
                "",
                f"**证据链数量**: {len(results['evidence_chains'])} 条",
                "",
                "### 证据链详情",
                "",
                "| 目标事实 | 强度 | 完整度 | 可信度 | 证据数 |",
                "|----------|------|--------|--------|--------|",
            ])
            
            for chain in results['evidence_chains']:
                lines.append(
                    f"| {chain.target_fact[:20]}... | "
                    f"{chain.overall_strength.value} | "
                    f"{chain.completeness:.0%} | "
                    f"{chain.credibility:.0%} | "
                    f"{len(chain.evidences)} |"
                )
            
            lines.append("")
            
            # 证据缺口
            total_gaps = sum(len(c.gaps) for c in results['evidence_chains'])
            if total_gaps > 0:
                lines.extend([
                    f"### 证据缺口（共 {total_gaps} 处）",
                    "",
                ])
                for chain in results['evidence_chains']:
                    if chain.gaps:
                        lines.append(f"**{chain.target_fact}**:")
                        for gap in chain.gaps:
                            lines.append(f"- ⚠ {gap}")
                        lines.append("")
        
        # 综合建议
        lines.extend([
            "## 五、综合建议",
            "",
        ])
        
        recommendations = []
        
        # 基于质量评估的建议
        if results['quality_reports']:
            low_quality = [r for r in results['quality_reports'] if r.quality_level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE]]
            if low_quality:
                recommendations.append(f"有 {len(low_quality)} 份笔录质量较差，建议补充完善")
        
        # 基于一致性验证的建议
        if results['validation_report']:
            report = results['validation_report']
            if report.critical_issues:
                recommendations.append(f"存在 {len(report.critical_issues)} 处严重矛盾，需要立即核实")
            if report.major_issues:
                recommendations.append(f"存在 {len(report.major_issues)} 处主要矛盾，建议进一步调查")
        
        # 基于证据链的建议
        if results['evidence_chains']:
            weak_chains = [c for c in results['evidence_chains'] if c.overall_strength.value == "weak"]
            if weak_chains:
                recommendations.append(f"有 {len(weak_chains)} 条证据链强度较弱，建议补充证据")
        
        if not recommendations:
            recommendations.append("当前证据材料较为完整，建议进入下一程序")
        
        recommendations.append("建议结合现场勘查、物证检验等其他证据综合判断")
        
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        lines.extend([
            "",
            "---",
            "",
            "*本报告由增强版笔录分析系统生成，集成了 Context Engineering Skills*",
        ])
        
        return '\n'.join(lines)


async def demo_integration():
    """演示集成使用"""
    print("=" * 60)
    print("笔录分析 Pipeline 集成演示")
    print("=" * 60)
    print()
    
    # 创建增强版 Pipeline
    pipeline = EnhancedInterrogationPipeline(
        output_dir="./output/enhanced_analysis",
        kb_name="legal_kb"
    )
    
    # 准备示例笔录
    sample_records = [
        InterrogationRecord(
            case_id="demo_case_001",
            record_id="record_001",
            interviewee="张三",
            interrogator="李警官",
            time=datetime(2024, 1, 15, 14, 30),
            location="市公安局",
            content="""
讯问时间：2024年1月15日 14:30
被讯问人：张三

问：请描述1月10日晚上的情况。
答：那天晚上8点左右，我和李四在商业区的一家餐厅吃饭。
大约9点半，我们离开餐厅，在停车场遇到了王五。
当时王五和李四发生了争执，我看到他们推搡了几下，然后王五倒在地上。
我当时站在旁边，没有参与。

问：你确定是晚上8点吗？
答：是的，我记得很清楚。
""",
            suspected_charge="故意伤害"
        ),
        InterrogationRecord(
            case_id="demo_case_001",
            record_id="record_002",
            interviewee="李四",
            interrogator="王警官",
            time=datetime(2024, 1, 15, 16, 0),
            location="市公安局",
            content="""
讯问时间：2024年1月15日 16:00
被讯问人：李四

问：请描述1月10日晚上的情况。
答：那天晚上我和张三在商业区吃饭，大概晚上7点半左右见面的。
吃完饭后，我们在停车场遇到了王五。王五突然冲过来骂我，说我欠他钱。
我当时很气愤，就推了他一下，但他自己滑倒了。张三一直在旁边看着，没有动手。

问：具体时间？
答：见面是7点半，离开餐厅大概是9点左右。
""",
            suspected_charge="故意伤害"
        ),
        InterrogationRecord(
            case_id="demo_case_001",
            record_id="record_003",
            interviewee="王五",
            interrogator="陈警官",
            time=datetime(2024, 1, 16, 10, 0),
            location="市人民医院",
            content="""
询问时间：2024年1月16日 10:00
被询问人：王五

问：请描述1月10日晚上发生的事情。
答：那天晚上9点多，我在商业区停车场等李四。他欠我钱，一直不还。
我看到李四和一个男的（后来知道叫张三）从餐厅出来，就走过去找他要钱。
结果李四突然推了我一下，我摔倒在地，头撞到了地上的石头。
那个张三也过来帮李四，两个人一起打我。

问：你确定是9点多吗？
答：是的，我看了一下手机，是9点15分左右。

问：张三有没有动手？
答：有，他过来拉住我的胳膊，让李四合打我。
""",
            suspected_charge="故意伤害"
        )
    ]
    
    print(f"准备分析 {len(sample_records)} 份笔录...")
    print()
    
    # 定义进度回调
    async def progress_callback(progress: int, message: str):
        print(f"[{progress:3d}%] {message}")
    
    try:
        # 执行增强分析
        results = await pipeline.analyze_with_skills(
            records=sample_records,
            enable_quality_check=True,
            enable_cross_validation=True,
            enable_relation_analysis=True,
            enable_evidence_chain=True,
            progress_callback=progress_callback
        )
        
        print()
        print("=" * 60)
        print("分析完成！")
        print("=" * 60)
        print()
        
        # 输出关键结果
        print("【笔录质量评估】")
        for report in results['quality_reports']:
            print(f"  - {report.record_id}: {report.quality_level.value} ({report.overall_score}/100)")
        
        print()
        print("【跨笔录一致性】")
        if results['validation_report']:
            report = results['validation_report']
            print(f"  整体一致性: {report.overall_consistency:.1f}%")
            print(f"  严重问题: {len(report.critical_issues)} 处")
            print(f"  主要问题: {len(report.major_issues)} 处")
        
        print()
        print("【证据链分析】")
        for chain in results['evidence_chains']:
            print(f"  - {chain.target_fact[:30]}...: {chain.overall_strength.value}")
        
        print()
        print(f"详细结果已保存到: ./output/enhanced_analysis/")
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        raise


async def demo_comparison():
    """演示传统方法与增强方法的对比"""
    print()
    print("=" * 60)
    print("传统方法 vs 增强方法 对比演示")
    print("=" * 60)
    print()
    
    # 准备示例笔录
    sample_records = [
        InterrogationRecord(
            case_id="compare_case_001",
            record_id="record_001",
            interviewee="嫌疑人A",
            interrogator="警官1",
            time=datetime(2024, 1, 10, 10, 0),
            location="讯问室1",
            content="""
时间：2024年1月10日 10:00
地点：讯问室1

问：交代你的问题。
答：我没有问题，我是被冤枉的。

问：我们有证据显示你参与了盗窃。
答：什么证据？我没有偷东西。

问：1月5日晚上你在哪里？
答：我在家里，一个人。
""",
            suspected_charge="盗窃"
        ),
        InterrogationRecord(
            case_id="compare_case_001",
            record_id="record_002",
            interviewee="嫌疑人B",
            interrogator="警官2",
            time=datetime(2024, 1, 10, 14, 0),
            location="讯问室2",
            content="""
时间：2024年1月10日 14:00
地点：讯问室2

问：交代你的问题。
答：我和A一起参与了盗窃。

问：具体说说。
答：1月5日晚上，我和A去了商场，偷了一些东西。
A负责望风，我负责动手。

问：A知道你要偷东西吗？
答：知道，我们商量好的。
""",
            suspected_charge="盗窃"
        )
    ]
    
    print("传统方法分析：")
    print("  - 分别分析每份笔录")
    print("  - 提取关键信息")
    print("  - 生成单独报告")
    print()
    
    print("增强方法分析（使用 Context Engineering Skills）：")
    print("  - 笔录质量评估（完整性、一致性、可信度、清晰度、合法性）")
    print("  - 跨笔录一致性验证（时间、事实、实体、逻辑、陈述）")
    print("  - 多笔录关联分析（时间线、矛盾点、相互印证）")
    print("  - 智能证据链构建（证据提取、链式组织、缺口识别）")
    print()
    
    # 创建增强版 Pipeline
    pipeline = EnhancedInterrogationPipeline(output_dir="./output/comparison")
    
    print("执行增强分析...")
    print("-" * 40)
    
    results = await pipeline.analyze_with_skills(
        records=sample_records,
        enable_quality_check=True,
        enable_cross_validation=True,
        enable_relation_analysis=True,
        enable_evidence_chain=True
    )
    
    print()
    print("=" * 60)
    print("增强分析关键发现：")
    print("=" * 60)
    
    # 质量评估
    print("\n1. 笔录质量评估：")
    for report in results['quality_reports']:
        print(f"   {report.record_id}:")
        print(f"     - 质量等级: {report.quality_level.value}")
        print(f"     - 综合得分: {report.overall_score}/100")
        if report.risk_flags:
            print(f"     - 风险标记: {len(report.risk_flags)} 个")
    
    # 一致性验证
    if results['validation_report']:
        report = results['validation_report']
        print("\n2. 跨笔录一致性验证：")
        print(f"   - 整体一致性: {report.overall_consistency:.1f}%")
        
        if report.critical_issues:
            print(f"   - 严重矛盾: {len(report.critical_issues)} 处")
            for issue in report.critical_issues:
                print(f"     * {issue.description}")
        
        if report.consistent_facts:
            print(f"   - 一致事实: {len(report.consistent_facts)} 项")
    
    # 关联分析
    if results['relation_graph']:
        graph = results['relation_graph']
        print("\n3. 笔录关联分析：")
        print(f"   - 发现 {len(graph.edges)} 个关联关系")
        
        contradictions = graph.get_contradictions()
        if contradictions:
            print(f"   - 发现 {len(contradictions)} 处矛盾")
    
    # 证据链
    if results['evidence_chains']:
        print("\n4. 证据链分析：")
        for chain in results['evidence_chains']:
            print(f"   - {chain.target_fact}:")
            print(f"     * 强度: {chain.overall_strength.value}")
            print(f"     * 完整度: {chain.completeness:.0%}")
            if chain.gaps:
                print(f"     * 缺口: {len(chain.gaps)} 处")
    
    print()
    print("=" * 60)
    print("对比总结：")
    print("=" * 60)
    print()
    print("传统方法：")
    print("  ✓ 单份笔录分析")
    print("  ✓ 基础信息提取")
    print("  ✗ 无法自动发现笔录间矛盾")
    print("  ✗ 缺乏系统性质量评估")
    print("  ✗ 证据链需要人工构建")
    print()
    print("增强方法（Context Engineering Skills）：")
    print("  ✓ 多维度质量评估")
    print("  ✓ 自动跨笔录一致性验证")
    print("  ✓ 智能矛盾检测")
    print("  ✓ 自动证据链构建")
    print("  ✓ 图结构关系分析")
    print("  ✓ 综合建议生成")


async def main():
    """主函数"""
    # 运行集成演示
    await demo_integration()
    
    # 运行对比演示
    await demo_comparison()
    
    print()
    print("=" * 60)
    print("所有演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
