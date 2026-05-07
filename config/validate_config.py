#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置验证脚本
============

验证 agents.yaml 配置是否正确，并检查所有模块是否能正确读取配置。

使用方法:
    python config/validate_config.py

功能:
1. 验证 agents.yaml 文件格式
2. 检查所有模块的配置是否存在
3. 测试配置读取功能
4. 输出验证报告
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_agents_yaml() -> Tuple[bool, List[str]]:
    """
    验证 agents.yaml 文件
    
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    try:
        import yaml
        config_path = project_root / "config" / "agents.yaml"
        
        if not config_path.exists():
            errors.append(f"❌ agents.yaml 文件不存在: {config_path}")
            return False, errors
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            errors.append("❌ agents.yaml 文件为空或格式错误")
            return False, errors
        
        # 检查必需的模块配置
        required_modules = [
            # Agent 模块
            "guide", "solve", "research", "question", "ideagen", "co_writer", "draw",
            "interrogation", "deep_analyze", "deep_audit", "domain_analysis", 
            "public_opinion", "chat", "assistant",
            # 服务层
            "llm", "llm_manager", "config_manager", "lightweight_agent", "autofigure",
            "teaching_planner", "prompt_optimizer", "memsearch", "agent_manager",
            "knowledge_integration",
            # API 层
            "ai_chat", "agents_api", "chatdev", "system_api", "interrogation_api",
            # Knowledge 层
            "knowledge", "extract_numbered_items", "ai_assistant",
            # Nanobot 层
            "nanobot_agent", "nanobot_mcp", "nanobot_deep_analyze",
            # 其他
            "self_improvement", "narrator", "dslighting",
        ]
        
        missing_modules = []
        for module in required_modules:
            if module not in config:
                missing_modules.append(module)
        
        if missing_modules:
            errors.append(f"⚠️  以下模块配置缺失: {', '.join(missing_modules)}")
        
        # 检查每个模块的参数
        for module_name, module_config in config.items():
            if not isinstance(module_config, dict):
                errors.append(f"❌ 模块 '{module_name}' 的配置必须是字典类型")
                continue
            
            # 检查是否有 temperature 和 max_tokens
            if "temperature" not in module_config:
                errors.append(f"⚠️  模块 '{module_name}' 缺少 temperature 配置")
            
            if "max_tokens" not in module_config:
                errors.append(f"⚠️  模块 '{module_name}' 缺少 max_tokens 配置")
        
        if not errors:
            errors.append(f"✅ agents.yaml 格式正确，包含 {len(config)} 个模块配置")
        
        return len([e for e in errors if e.startswith("❌")]) == 0, errors
        
    except ImportError:
        errors.append("❌ 无法导入 yaml 模块，请安装: pip install pyyaml")
        return False, errors
    except Exception as e:
        errors.append(f"❌ 验证失败: {e}")
        return False, errors


def test_config_loading() -> Tuple[bool, List[str]]:
    """
    测试配置读取功能
    
    Returns:
        (是否成功, 测试结果列表)
    """
    results = []
    
    try:
        from src.services.config import get_agent_params
        
        # 测试几个关键模块
        test_modules = [
            "guide", "solve", "interrogation", "llm", "ai_chat", 
            "knowledge", "self_improvement"
        ]
        
        for module in test_modules:
            try:
                params = get_agent_params(module)
                temperature = params.get("temperature")
                max_tokens = params.get("max_tokens")
                
                if temperature is not None and max_tokens is not None:
                    results.append(f"✅ 模块 '{module}': temperature={temperature}, max_tokens={max_tokens}")
                else:
                    results.append(f"⚠️  模块 '{module}': 参数不完整")
            except Exception as e:
                results.append(f"❌ 模块 '{module}': 读取失败 - {e}")
        
        return len([r for r in results if r.startswith("❌")]) == 0, results
        
    except ImportError as e:
        results.append(f"❌ 无法导入配置模块: {e}")
        return False, results
    except Exception as e:
        results.append(f"❌ 测试失败: {e}")
        return False, results


def check_service_files() -> Tuple[bool, List[str]]:
    """
    检查服务文件是否正确使用配置
    
    Returns:
        (是否通过, 检查结果列表)
    """
    results = []
    
    # 检查关键文件是否包含配置读取代码
    service_files = [
        "src/services/llm/config.py",
        "src/services/llm_manager.py",
        "src/services/config_manager.py",
        "src/services/autofigure/paper_parser.py",
        "src/services/teaching_planner/executor.py",
        "src/services/prompt_optimizer/strategies.py",
    ]
    
    for file_path in service_files:
        full_path = project_root / file_path
        if full_path.exists():
            content = full_path.read_text(encoding='utf-8')
            if "get_agent_params" in content or "_get_" in content and "_params" in content:
                results.append(f"✅ {file_path}: 已配置化")
            else:
                results.append(f"⚠️  {file_path}: 可能未配置化")
        else:
            results.append(f"❌ {file_path}: 文件不存在")
    
    return len([r for r in results if r.startswith("❌")]) == 0, results


def print_report(title: str, success: bool, items: List[str]):
    """打印报告"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    for item in items:
        print(f"  {item}")
    status = "✅ 通过" if success else "❌ 失败"
    print(f"\n  状态: {status}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("配置验证工具")
    print("="*60)
    print(f"项目根目录: {project_root}")
    
    all_success = True
    
    # 验证 agents.yaml
    success, errors = validate_agents_yaml()
    print_report("1. 验证 agents.yaml 文件", success, errors)
    all_success = all_success and success
    
    # 测试配置读取
    success, results = test_config_loading()
    print_report("2. 测试配置读取功能", success, results)
    all_success = all_success and success
    
    # 检查服务文件
    success, results = check_service_files()
    print_report("3. 检查服务文件配置化", success, results)
    all_success = all_success and success
    
    # 总结
    print("\n" + "="*60)
    if all_success:
        print("✅ 所有验证通过！配置系统工作正常。")
    else:
        print("❌ 验证未通过，请检查上述错误信息。")
    print("="*60 + "\n")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
