"""
智能案件多笔录分析技能演示

展示如何使用 Context Engineering Skills 进行笔录分析：
1. 笔录质量评估
2. 多笔录关联分析
3. 跨笔录验证
4. 证据链构建
5. 人员组织架构图分析
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 把项目根目录加入 sys.path，确保能 import src
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.agents.interrogation.skills import (
    MultiRecordAnalysisSkill,
    EvidenceChainBuilderSkill,
    RecordQualityEvaluatorSkill,
    CrossRecordValidatorSkill,
    OrganizationChartAnalyzerSkill,
    QualityLevel,
    EvidenceType,
    ValidationSeverity,
    OrganizationType,
    RoleType
)


# 示例笔录数据 - 简单案件
SAMPLE_RECORDS = [
    {
        "id": "record_001",
        "type": "讯问笔录",
        "subject": "张三",
        "content": """
讯问时间：2024年1月15日 14:30
讯问地点：市公安局讯问室
讯问人：李警官、王警官
被讯问人：张三

问：你的基本情况？
答：我叫张三，男，35岁，住在阳光小区3号楼。

问：你知道为什么被讯问吗？
答：知道，关于1月10日晚上在商业区发生的事情。

问：请详细描述当晚的情况。
答：那天晚上8点左右，我和李四在商业区的一家餐厅吃饭。我们谈了一些生意上的事情。
大约9点半，我们离开餐厅，在停车场遇到了王五。当时王五和李四发生了争执，
我看到他们推搡了几下，然后王五倒在地上。我当时站在旁边，没有参与。

问：你确定是晚上8点吗？
答：是的，我记得很清楚，因为我们约好了8点见面。

问：现场还有其他人吗？
答：好像还有几个人在附近，但我记不清了。

问：你之前认识王五吗？
答：不认识，我是第一次见他。

问：你以上说的是实话吗？
答：是实话。我已经看过笔录，和我说的相符。
被讯问人签名：张三
日期：2024年1月15日
""",
        "timestamp": datetime(2024, 1, 15, 14, 30)
    },
    {
        "id": "record_002",
        "type": "讯问笔录",
        "subject": "李四",
        "content": """
讯问时间：2024年1月15日 16:00
讯问地点：市公安局讯问室
讯问人：李警官、赵警官
被讯问人：李四

问：你的基本情况？
答：我叫李四，男，38岁，住在绿城花园。

问：请描述1月10日晚上的情况。
答：那天晚上我和张三在商业区吃饭，大概晚上7点半左右见面的。
吃完饭后，我们在停车场遇到了王五。王五突然冲过来骂我，说我欠他钱。
我当时很气愤，就推了他一下，但他自己滑倒了。张三一直在旁边看着，没有动手。

问：具体时间？
答：见面是7点半，离开餐厅大概是9点左右。

问：你和王五什么关系？
答：之前做生意欠了他一些钱，大概有5万元。

问：现场还有谁？
答：就我们三个人，没有其他人。

问：张三有没有动手？
答：没有，张三就是站在旁边。

问：你确定是7点半见面吗？
答：是的，我记得是7点半。

问：你以上说的是实话吗？
答：是实话。我已经核对过笔录，没有问题。
被讯问人签名：李四
日期：2024年1月15日
""",
        "timestamp": datetime(2024, 1, 15, 16, 0)
    },
    {
        "id": "record_003",
        "type": "询问笔录",
        "subject": "王五",
        "content": """
询问时间：2024年1月16日 10:00
询问地点：市人民医院
询问人：陈警官
被询问人：王五

问：你的基本情况？
答：我叫王五，男，40岁，住在商业区附近。

问：请描述1月10日晚上发生的事情。
答：那天晚上9点多，我在商业区停车场等李四。他欠我钱，一直不还。
我看到李四和一个男的（后来知道叫张三）从餐厅出来，就走过去找他要钱。
结果李四突然推了我一下，我摔倒在地，头撞到了地上的石头。
那个张三也过来帮李四，两个人一起打我。

问：你确定是9点多吗？
答：是的，我看了一下手机，是9点15分左右。

问：张三有没有动手？
答：有，他过来拉住我的胳膊，让李四合打我。

问：你认识张三吗？
答：不认识，第一次见。

问：你的伤势？
答：头部受伤，缝了5针，还有轻微脑震荡。

问：现场还有其他人吗？
答：好像还有几个人在远处看着，但没有过来帮忙。

问：你以上说的是实话吗？
答：是实话。我已经看过笔录，没有问题。
被询问人签名：王五
日期：2024年1月16日
""",
        "timestamp": datetime(2024, 1, 16, 10, 0)
    },
    {
        "id": "record_004",
        "type": "证人笔录",
        "subject": "赵六",
        "content": """
询问时间：2024年1月16日 15:00
询问地点：市公安局
询问人：李警官
证人：赵六

问：你的基本情况？
答：我叫赵六，是商业区停车场的保安。

问：请描述1月10日晚上你看到的情况。
答：那天晚上9点左右，我在停车场巡逻。看到两个人从餐厅出来，
然后另一个人走过来，三个人说了几句话，就开始推搡。
其中一个人倒在地上，另外两个人站在旁边。我没有看清谁先动的手。

问：你能认出那三个人吗？
答：能认出倒在地上的人（王五），另外两个不太确定。

问：现场还有其他人吗？
答：当时停车场还有几辆车，但距离比较远。

问：你确定是9点左右吗？
答：是的，我当时看了表，是9点10分左右。

问：你以上说的是实话吗？
答：是实话。我已经核对过笔录，没有问题。
证人签名：赵六
日期：2024年1月16日
""",
        "timestamp": datetime(2024, 1, 16, 15, 0)
    }
]


# 示例笔录数据 - 团伙犯罪案件（用于组织架构图分析）
GANG_CASE_RECORDS = [
    {
        "id": "gang_record_001",
        "type": "讯问笔录",
        "subject": "老大",
        "content": """
讯问时间：2024年2月1日 10:00
被讯问人：刘大

问：交代你的问题。
答：我是这个团伙的头目，负责组织所有的盗窃活动。
我的手下有张三、李四、王五三个人。
张三和李四是核心成员，负责踩点和实施盗窃。
王五是外围人员，负责销赃。

问：你们是怎么分工的？
答：我负责统筹安排，决定什么时候行动，偷什么地方。
张三和李四听我指挥，他们具体去偷。
偷到的东西交给王五，他负责卖掉分钱。

问：你们一共偷了多少次？
答：大概十几次吧，具体记不清了。
""",
        "timestamp": datetime(2024, 2, 1, 10, 0)
    },
    {
        "id": "gang_record_002",
        "type": "讯问笔录",
        "subject": "核心成员1",
        "content": """
讯问时间：2024年2月1日 14:00
被讯问人：张三

问：交代你的问题。
答：我是跟着刘大干的，他是我们的老大。
我和李四都是他的手下，负责去偷东西。
刘大让我们去哪里偷，我们就去哪里。
偷到的东西都交给王五处理。

问：你和李四怎么分工？
答：我们两个人配合，我负责望风，李四负责动手。
有时候反过来，但一般都是这样分工。

问：王五是做什么的？
答：王五是负责卖东西的，他不参与偷，只负责销赃。
他是刘大的亲戚，所以刘大信任他。
""",
        "timestamp": datetime(2024, 2, 1, 14, 0)
    },
    {
        "id": "gang_record_003",
        "type": "讯问笔录",
        "subject": "核心成员2",
        "content": """
讯问时间：2024年2月1日 16:00
被讯问人：李四

问：交代你的问题。
答：我是团伙成员，听刘大的指挥。
我和张三一起负责实施盗窃。
刘大是我们的头目，我们都听他的。

问：你们听谁的？
答：听刘大的，他是老大。
张三和我是搭档，我们一起干活。
王五负责卖东西，他不跟我们去偷。

问：还有其他人吗？
答：还有一个叫赵六的，他是外围人员，
有时候帮我们望风，但不参与分赃，拿固定的钱。
""",
        "timestamp": datetime(2024, 2, 1, 16, 0)
    },
    {
        "id": "gang_record_004",
        "type": "讯问笔录",
        "subject": "销赃人员",
        "content": """
讯问时间：2024年2月2日 09:00
被讯问人：王五

问：交代你的问题。
答：我是刘大的表弟，负责帮他们卖偷来的东西。
刘大是老大，张三和李四是他的手下，负责去偷。
我不参与偷，只负责销赃。

问：你和刘大什么关系？
答：他是我表哥，所以我帮他做事。
他信得过我，让我管钱。

问：还有谁参与？
答：还有一个叫赵六的，他是外围人员，
有时候帮忙望风，但不是核心成员。
""",
        "timestamp": datetime(2024, 2, 2, 9, 0)
    },
    {
        "id": "gang_record_005",
        "type": "讯问笔录",
        "subject": "外围人员",
        "content": """
讯问时间：2024年2月2日 11:00
被讯问人：赵六

问：交代你的问题。
答：我认识刘大，他是老大。
我有时候帮他们望风，但不是正式成员。
张三和李四是核心成员，他们负责偷。
王五是刘大的亲戚，负责卖东西。

问：你拿多少钱？
答：我每次望风拿固定的500元，不参与分赃。
我不是核心成员，只是外围帮忙的。
""",
        "timestamp": datetime(2024, 2, 2, 11, 0)
    }
]


async def demo_quality_evaluation():
    """演示笔录质量评估"""
    print("=" * 60)
    print("演示 1: 笔录质量评估")
    print("=" * 60)
    
    evaluator = RecordQualityEvaluatorSkill()
    
    for record in SAMPLE_RECORDS:
        print(f"\n评估笔录: {record['id']} ({record['type']} - {record['subject']})")
        print("-" * 40)
        
        result = await evaluator.apply({
            "record": record["content"],
            "record_id": record["id"],
            "record_type": record["type"]
        })
        
        print(f"综合得分: {result.overall_score}/100")
        print(f"质量等级: {result.quality_level.value}")
        
        print("\n各维度得分:")
        for ds in result.dimension_scores:
            print(f"  - {ds.dimension.value}: {ds.score:.1f}/100")
        
        if result.missing_elements:
            print(f"\n缺失要素: {', '.join(result.missing_elements)}")
        
        if result.risk_flags:
            print(f"\n风险标记 ({len(result.risk_flags)}):")
            for risk in result.risk_flags[:3]:
                print(f"  ⚠ {risk}")
        
        if result.improvement_suggestions:
            print(f"\n改进建议:")
            for i, suggestion in enumerate(result.improvement_suggestions[:3], 1):
                print(f"  {i}. {suggestion}")
    
    print("\n")


async def demo_multi_record_analysis():
    """演示多笔录关联分析"""
    print("=" * 60)
    print("演示 2: 多笔录关联分析")
    print("=" * 60)
    
    analyzer = MultiRecordAnalysisSkill()
    
    result = await analyzer.apply({
        "records": SAMPLE_RECORDS,
        "case_id": "case_2024_001"
    })
    
    print(f"\n案件 ID: {result.case_id}")
    print(f"笔录数量: {len(result.nodes)}")
    print(f"关联关系: {len(result.edges)}")
    
    print("\n笔录节点:")
    for node in result.nodes.values():
        print(f"  - {node.record_id}: {node.record_type}（{node.person_name}）")
        print(f"    时间: {node.record_time.isoformat()}")
        print(f"    提取事实: {len(node.key_facts)}")
        if node.mentioned_persons:
            print(f"    涉及人员: {', '.join(node.mentioned_persons)}")
    
    print("\n关联关系:")
    for e in result.edges:
        print(f"  - {e.from_record} -> {e.to_record}")
        print(f"    类型: {e.relation_type}")
        print(f"    强度: {e.strength:.2f}")
        if e.description:
            print(f"    描述: {e.description}")
    
    print("\n时间线:")
    timeline = result.get_chronological_order()
    for rid in timeline:
        n = result.nodes[rid]
        print(f"  [{n.record_time.isoformat()}] {rid}: {n.person_name} - {n.record_type}")
    
    print("\n矛盾点:")
    contradictions = result.find_contradictions()
    if contradictions:
        for i, c in enumerate(contradictions, 1):
            print(f"  {i}. {c.description}")
    else:
        print("  未发现明显矛盾")
    
    print("\n")


async def demo_cross_record_validation():
    """演示跨笔录验证"""
    print("=" * 60)
    print("演示 3: 跨笔录验证")
    print("=" * 60)
    
    validator = CrossRecordValidatorSkill()
    
    result = await validator.apply({
        "records": SAMPLE_RECORDS,
        "focus_entities": ["张三", "李四", "王五"],
        "focus_facts": ["见面时间", "离开时间", "是否动手"]
    })
    
    print(f"\n涉及笔录: {', '.join(result.record_ids)}")
    print(f"整体一致性: {result.overall_consistency:.1f}%")
    
    print("\n各维度一致性:")
    for cs in result.consistency_scores:
        status = "✓" if cs.score >= 70 else "⚠"
        print(f"  {status} {cs.validation_type.value}: {cs.score:.1f}% ({cs.issue_count} 个问题)")
    
    if result.critical_issues:
        print(f"\n严重问题 ({len(result.critical_issues)}):")
        for issue in result.critical_issues:
            print(f"  🔴 {issue.description}")
            if issue.suggested_resolution:
                print(f"      建议: {issue.suggested_resolution}")
    
    if result.major_issues:
        print(f"\n主要问题 ({len(result.major_issues)}):")
        for issue in result.major_issues:
            print(f"  🟠 {issue.description}")
    
    if result.consistent_facts:
        print(f"\n一致事实 ({len(result.consistent_facts)}):")
        for fact in result.consistent_facts[:5]:
            print(f"  ✓ {fact['fact']}: {str(fact['value'])[:50]}")
    
    if result.inconsistent_facts:
        print(f"\n不一致事实 ({len(result.inconsistent_facts)}):")
        for fact in result.inconsistent_facts[:5]:
            print(f"  ✗ {fact['fact']} ({fact['severity']})")
    
    if result.recommendations:
        print(f"\n建议:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
    
    print("\n")


async def demo_evidence_chain_building():
    """演示证据链构建"""
    print("=" * 60)
    print("演示 4: 证据链构建")
    print("=" * 60)
    
    builder = EvidenceChainBuilderSkill()
    
    target_facts = [
        "张三是否参与斗殴",
        "李四是否推搡王五",
        "事件发生的具体时间",
        "王五的伤势情况"
    ]
    
    result = await builder.apply({
        "records": SAMPLE_RECORDS,
        "target_facts": target_facts,
        "case_id": "case_2024_001"
    })
    
    print(f"\n构建证据链数量: {len(result)}")
    
    for i, chain in enumerate(result, 1):
        print(f"\n证据链 {i}: {chain.target_fact}")
        print("-" * 40)
        print(f"整体强度: {chain.overall_strength.value}")
        print(f"完整度: {chain.completeness:.1%}")
        print(f"可信度: {chain.credibility:.1%}")
        
        print(f"\n包含证据 ({len(chain.evidences)}):")
        for j, evidence in enumerate(chain.evidences, 1):
            print(f"  {j}. [{evidence.evidence_type.value}] {evidence.source_record}")
            print(f"      内容: {evidence.content[:60]}...")
            print(f"      可信度: {evidence.credibility_score:.1f}/100")
        
        print(f"\n证据链评估:")
        print(f"  - 充分性: {chain.sufficiency:.1f}/100")
        print(f"  - 一致性: {chain.consistency:.1f}/100")
        
        if chain.gaps:
            print(f"\n证据缺口 ({len(chain.gaps)}):")
            for gap in chain.gaps:
                print(f"  ⚠ {gap}")
        
        if chain.recommendations:
            print(f"\n建议:")
            for rec in chain.recommendations:
                print(f"  • {rec}")
    
    print("\n")


async def demo_organization_chart_analysis():
    """演示人员组织架构图分析"""
    print("=" * 60)
    print("演示 5: 人员组织架构图分析")
    print("=" * 60)
    
    analyzer = OrganizationChartAnalyzerSkill()
    
    result = await analyzer.apply({
        "records": GANG_CASE_RECORDS,
        "case_id": "gang_case_2024_001",
        "org_type": OrganizationType.CRIMINAL_GANG,
        "focus_persons": ["刘大", "张三", "李四", "王五", "赵六"]
    })
    
    print(f"\n案件 ID: {result.case_id}")
    print(f"组织类型: {result.org_type.value}")
    print(f"成员总数: {result.member_count}")
    print(f"组织层级: {result.max_level + 1} 层")
    print(f"关系总数: {len(result.relations)}")
    
    print("\n层级分布:")
    for level in result.levels:
        print(f"  层级 {level.level}: {len(level.members)} 人 - {level.description}")
        for member in level.members:
            role_emoji = {
                RoleType.LEADER: "👑",
                RoleType.CORE_MEMBER: "⭐",
                RoleType.MEMBER: "👤",
                RoleType.SUBORDINATE: "🔽",
                RoleType.COLLABORATOR: "🤝",
                RoleType.OUTSIDER: "👁",
                RoleType.VICTIM: "😢",
                RoleType.WITNESS: "👀"
            }.get(member.role, "•")
            print(f"    {role_emoji} {member.name} ({member.role.value})")
    
    print("\n核心成员:")
    for member in result.core_members:
        print(f"  • {member.name} ({member.role.value})")
        # 显示下属
        subordinates = result.get_subordinates(member.member_id)
        if subordinates:
            print(f"    └─ 下属: {', '.join([s.name for s in subordinates])}")
    
    print("\n关系类型分布:")
    from collections import Counter
    relation_counts = Counter([r.relation_type.value for r in result.relations])
    for rel_type, count in relation_counts.most_common():
        print(f"  • {rel_type}: {count}")
    
    print("\n关键关系:")
    for relation in result.relations:
        if relation.strength > 0.5:
            source = result.members.get(relation.source_id)
            target = result.members.get(relation.target_id)
            if source and target:
                print(f"  • {source.name} -> {target.name}: {relation.relation_type.value} (强度: {relation.strength:.2f})")
    
    print("\n组织架构摘要:")
    summary = analyzer.get_organization_summary(result)
    print(summary)
    
    print("\n文本层级结构:")
    text_hierarchy = analyzer.generate_text_hierarchy(result)
    print(text_hierarchy)
    
    print("\nMermaid 图表代码:")
    mermaid_code = analyzer.generate_mermaid_chart(result)
    print(mermaid_code)
    
    print("\n")


async def demo_integrated_analysis():
    """演示综合分析"""
    print("=" * 60)
    print("演示 6: 综合分析报告")
    print("=" * 60)
    
    # 创建所有技能实例
    evaluator = RecordQualityEvaluatorSkill()
    analyzer = MultiRecordAnalysisSkill()
    validator = CrossRecordValidatorSkill()
    builder = EvidenceChainBuilderSkill()
    org_analyzer = OrganizationChartAnalyzerSkill()
    
    print("\n正在执行综合分析...")
    print("-" * 40)
    
    # 并行执行所有分析
    quality_results = []
    for record in SAMPLE_RECORDS:
        result = await evaluator.apply({
            "record": record["content"],
            "record_id": record["id"]
        })
        quality_results.append(result)
    
    relation_graph = await analyzer.apply({
        "records": SAMPLE_RECORDS,
        "case_id": "case_2024_001"
    })
    
    validation_report = await validator.apply({
        "records": SAMPLE_RECORDS,
        "focus_entities": ["张三", "李四", "王五"]
    })
    
    evidence_chains = await builder.apply({
        "records": SAMPLE_RECORDS,
        "target_facts": ["张三是否参与斗殴", "李四是否推搡王五"],
        "case_id": "case_2024_001"
    })
    
    # 组织架构分析（使用团伙案例）
    org_chart = await org_analyzer.apply({
        "records": GANG_CASE_RECORDS,
        "case_id": "gang_case_2024_001",
        "org_type": OrganizationType.CRIMINAL_GANG
    })
    
    # 生成综合分析报告
    print("\n" + "=" * 60)
    print("案件综合分析报告")
    print("=" * 60)
    
    print(f"\n案件编号: case_2024_001")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"笔录数量: {len(SAMPLE_RECORDS)}")
    
    # 质量评估汇总
    print("\n【笔录质量评估汇总】")
    avg_score = sum(r.overall_score for r in quality_results) / len(quality_results)
    print(f"平均质量得分: {avg_score:.1f}/100")
    
    low_quality = [r for r in quality_results if r.quality_level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE]]
    if low_quality:
        print(f"⚠ 发现 {len(low_quality)} 份质量较差的笔录")
        for r in low_quality:
            print(f"   - {r.record_id}: {r.quality_level.value}")
    else:
        print("✓ 所有笔录质量良好")
    
    # 关联分析汇总
    print("\n【笔录关联分析汇总】")
    print(f"发现 {len(relation_graph.edges)} 个关联关系")
    
    corroborations = [e for e in relation_graph.edges if e.relation_type == "corroboration"]
    contradictions = [e for e in relation_graph.edges if e.relation_type == "contradiction"]
    
    print(f"  - 相互印证: {len(corroborations)} 处")
    print(f"  - 矛盾冲突: {len(contradictions)} 处")
    
    # 一致性验证汇总
    print("\n【一致性验证汇总】")
    print(f"整体一致性: {validation_report.overall_consistency:.1f}%")
    
    critical = len(validation_report.critical_issues)
    major = len(validation_report.major_issues)
    
    if critical > 0:
        print(f"🔴 严重矛盾: {critical} 处")
    if major > 0:
        print(f"🟠 主要矛盾: {major} 处")
    
    if critical == 0 and major == 0:
        print("✓ 未发现严重或主要矛盾")
    
    # 证据链汇总
    print("\n【证据链分析汇总】")
    print(f"构建证据链: {len(evidence_chains)} 条")
    
    strong_chains = [c for c in evidence_chains if c.overall_strength >= 0.7]
    weak_chains = [c for c in evidence_chains if c.overall_strength < 0.4]
    
    print(f"  - 强证据链: {len(strong_chains)} 条")
    print(f"  - 弱证据链: {len(weak_chains)} 条")
    
    # 组织架构汇总
    print("\n【组织架构分析汇总】")
    print(f"组织类型: {org_chart.org_type.value}")
    print(f"成员总数: {org_chart.member_count}")
    print(f"组织层级: {org_chart.max_level + 1} 层")
    print(f"核心成员: {len(org_chart.core_members)} 人")
    
    # 关键发现
    print("\n【关键发现】")
    findings = []
    
    # 时间矛盾
    time_issues = [i for i in validation_report.issues 
                   if i.validation_type.value == "temporal" and i.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.MAJOR]]
    if time_issues:
        findings.append(f"发现 {len(time_issues)} 处时间描述矛盾")
    
    # 事实矛盾
    fact_issues = [i for i in validation_report.issues 
                   if i.validation_type.value == "factual" and i.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.MAJOR]]
    if fact_issues:
        findings.append(f"发现 {len(fact_issues)} 处事实描述矛盾")
    
    # 证据链缺口
    total_gaps = sum(len(c.gaps) for c in evidence_chains)
    if total_gaps > 0:
        findings.append(f"证据链存在 {total_gaps} 处缺口")
    
    # 组织架构发现
    if org_chart.core_members:
        findings.append(f"识别出 {len(org_chart.core_members)} 名核心成员")
    
    if not findings:
        findings.append("各笔录整体一致性良好")
    
    for i, finding in enumerate(findings, 1):
        print(f"  {i}. {finding}")
    
    # 建议
    print("\n【综合建议】")
    recommendations = []
    
    if time_issues:
        recommendations.append("针对时间矛盾点进行重点核实，调取监控录像确认准确时间")
    
    if fact_issues:
        recommendations.append("对事实描述不一致之处进行补充讯问，澄清疑点")
    
    if total_gaps > 0:
        recommendations.append("补充收集证据，完善证据链")
    
    if org_chart.core_members:
        recommendations.append("针对组织架构中的核心成员进行重点突破")
    
    if not recommendations:
        recommendations.append("当前证据材料较为完整，建议进入下一程序")
    
    recommendations.append("建议结合现场勘查、物证检验等其他证据综合判断")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "=" * 60)
    print("分析完成")
    print("=" * 60)


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("智能案件多笔录分析技能演示")
    print("=" * 60)
    print("\n本演示展示如何使用 Context Engineering Skills 进行：")
    print("  1. 笔录质量评估")
    print("  2. 多笔录关联分析")
    print("  3. 跨笔录一致性验证")
    print("  4. 智能证据链构建")
    print("  5. 人员组织架构图分析")
    print("  6. 综合分析报告生成")
    print("\n")
    
    # 运行所有演示
    await demo_quality_evaluation()
    await demo_multi_record_analysis()
    await demo_cross_record_validation()
    await demo_evidence_chain_building()
    await demo_organization_chart_analysis()
    await demo_integrated_analysis()
    
    print("\n演示结束！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
