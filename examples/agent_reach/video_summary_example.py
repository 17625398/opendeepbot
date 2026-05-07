"""
视频字幕提取与总结示例 - Agent Reach VideoSubtitleSkill 使用示例

演示如何使用 VideoSubtitleSkill 提取 YouTube 和 B站视频字幕，
并进行内容总结和分析。适用于视频内容分析、学习笔记生成等场景。

依赖:
    - yt-dlp: pip install yt-dlp

运行:
    python examples/agent_reach/video_summary_example.py
"""

import asyncio
from typing import Optional, Dict, Any

from src.agents.skills import (
    load_skill,
    get_registry,
    VideoSubtitleSkill,
)


async def example_youtube_subtitle_extraction():
    """示例1: 提取 YouTube 视频字幕"""
    print("=" * 60)
    print("示例1: 提取 YouTube 视频字幕")
    print("=" * 60)
    
    skill = load_skill("video_subtitle")
    if not skill:
        print("错误: VideoSubtitleSkill 未注册")
        return
    
    # 示例 YouTube URL - 使用一个教育类视频
    # 注意: 请替换为实际存在的、有字幕的视频 URL
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"正在提取字幕: {url}")
    print("语言: 中文 (zh-CN)")
    
    result = skill.extract_youtube_subtitle(
        url=url,
        language='zh-CN',
        include_auto=True,
        use_cache=True
    )
    
    if result.success:
        data = result.data
        print(f"\n✅ 字幕提取成功!")
        print(f"   视频标题: {data['title']}")
        print(f"   上传者: {data['uploader']}")
        print(f"   时长: {data['duration']} 秒")
        print(f"   观看次数: {data['view_count']}")
        print(f"   是否有字幕: {data['has_subtitles']}")
        print(f"   语言: {data['language']}")
        
        if data['has_subtitles'] and data['subtitle_text']:
            print(f"\n字幕内容 (前800字符):")
            print("-" * 60)
            subtitle_preview = data['subtitle_text'][:800]
            print(subtitle_preview)
            if len(data['subtitle_text']) > 800:
                print(f"\n... (还有 {len(data['subtitle_text']) - 800} 字符)")
            print("-" * 60)
        else:
            print("\n⚠️ 该视频没有可用字幕")
            print(f"可用字幕语言: {data['available_subtitles']}")
            print(f"可用自动字幕: {data['available_auto_captions']}")
    else:
        print(f"❌ 字幕提取失败: {result.error}")
    
    print()


async def example_bilibili_subtitle_extraction():
    """示例2: 提取 B站视频字幕"""
    print("=" * 60)
    print("示例2: 提取 B站视频字幕")
    print("=" * 60)
    
    skill = load_skill("video_subtitle")
    if not skill:
        print("错误: VideoSubtitleSkill 未注册")
        return
    
    # 示例 B站 URL
    # 注意: 请替换为实际存在的视频 URL
    url = "https://www.bilibili.com/video/BV1GJ411x7h7"
    
    print(f"正在提取字幕: {url}")
    print("语言: 中文 (zh-CN)")
    
    result = skill.extract_bilibili_subtitle(
        url=url,
        language='zh-CN',
        use_cache=True
    )
    
    if result.success:
        data = result.data
        print(f"\n✅ 字幕提取成功!")
        print(f"   视频标题: {data['title']}")
        print(f"   上传者: {data['uploader']}")
        print(f"   时长: {data['duration']} 秒")
        print(f"   是否有字幕: {data['has_subtitles']}")
        
        if data['has_subtitles'] and data['subtitle_text']:
            print(f"\n字幕内容 (前600字符):")
            print("-" * 60)
            subtitle_preview = data['subtitle_text'][:600]
            print(subtitle_preview)
            if len(data['subtitle_text']) > 600:
                print(f"\n... (还有 {len(data['subtitle_text']) - 600} 字符)")
            print("-" * 60)
        else:
            print("\n⚠️ 该视频没有可用字幕")
    else:
        print(f"❌ 字幕提取失败: {result.error}")
    
    print()


async def example_video_content_analysis():
    """示例3: 视频内容分析工作流"""
    print("=" * 60)
    print("示例3: 视频内容分析工作流")
    print("=" * 60)
    
    skill = load_skill("video_subtitle")
    if not skill:
        print("错误: VideoSubtitleSkill 未注册")
        return
    
    # 模拟一个视频分析工作流
    video_urls = [
        {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "platform": "youtube", "name": "示例视频1"},
    ]
    
    print("开始视频内容分析工作流...")
    print(f"目标: 分析 {len(video_urls)} 个视频\n")
    
    analysis_results = []
    
    for video_info in video_urls:
        print(f"📹 分析视频: {video_info['name']}")
        print(f"   URL: {video_info['url']}")
        print(f"   平台: {video_info['platform']}")
        
        if video_info['platform'] == 'youtube':
            result = skill.extract_youtube_subtitle(
                url=video_info['url'],
                language='zh-CN',
                include_auto=True
            )
        else:
            result = skill.extract_bilibili_subtitle(
                url=video_info['url'],
                language='zh-CN'
            )
        
        if result.success:
            data = result.data
            
            # 简单的内容分析
            subtitle_text = data.get('subtitle_text', '')
            word_count = len(subtitle_text.split()) if subtitle_text else 0
            char_count = len(subtitle_text) if subtitle_text else 0
            
            analysis = {
                'name': video_info['name'],
                'title': data['title'],
                'uploader': data['uploader'],
                'duration': data['duration'],
                'has_subtitles': data['has_subtitles'],
                'word_count': word_count,
                'char_count': char_count,
                'platform': video_info['platform']
            }
            analysis_results.append(analysis)
            
            print(f"   ✅ 分析完成")
            print(f"      字数: {word_count}")
            print(f"      字符数: {char_count}")
            print(f"      有时长: {data['duration']} 秒")
        else:
            print(f"   ❌ 分析失败: {result.error}")
        
        print()
    
    # 输出汇总
    print("📊 分析汇总:")
    print("-" * 60)
    for result in analysis_results:
        print(f"\n🎬 {result['name']}")
        print(f"   标题: {result['title'][:60]}...")
        print(f"   上传者: {result['uploader']}")
        print(f"   字幕字数: {result['word_count']}")
        print(f"   视频时长: {result['duration']} 秒")
    
    print("\n✅ 视频内容分析工作流完成!")
    print()


async def example_subtitle_summary_generation():
    """示例4: 基于字幕生成内容总结"""
    print("=" * 60)
    print("示例4: 基于字幕生成内容总结")
    print("=" * 60)
    
    skill = load_skill("video_subtitle")
    if not skill:
        print("错误: VideoSubtitleSkill 未注册")
        return
    
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"提取并分析视频: {url}\n")
    
    result = skill.extract_youtube_subtitle(
        url=url,
        language='en',
        include_auto=True
    )
    
    if result.success and result.data.get('has_subtitles'):
        data = result.data
        subtitle_text = data['subtitle_text']
        
        print(f"✅ 字幕提取成功!")
        print(f"   视频: {data['title']}")
        print(f"   字幕长度: {len(subtitle_text)} 字符\n")
        
        # 简单的内容总结（基于段落分割）
        print("📝 内容结构分析:")
        print("-" * 60)
        
        # 分割成段落
        paragraphs = [p.strip() for p in subtitle_text.split('\n\n') if p.strip()]
        
        print(f"段落数量: {len(paragraphs)}")
        
        if paragraphs:
            print(f"\n前3个段落预览:")
            for i, para in enumerate(paragraphs[:3], 1):
                preview = para[:150] + "..." if len(para) > 150 else para
                print(f"\n段落 {i}:")
                print(f"  {preview}")
        
        # 关键词提取（简单实现）
        print(f"\n🔑 高频词汇 (前10个):")
        words = subtitle_text.lower().split()
        word_freq = {}
        for word in words:
            # 简单的过滤
            if len(word) > 3 and word.isalpha():
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        for word, freq in top_words:
            print(f"   - {word}: {freq} 次")
        
    else:
        print(f"❌ 无法提取字幕: {result.error if not result.success else '无可用字幕'}")
    
    print()


async def example_generic_execute_interface():
    """示例5: 使用通用 execute 接口"""
    print("=" * 60)
    print("示例5: 使用通用 execute 接口")
    print("=" * 60)
    
    skill = load_skill("video_subtitle")
    if not skill:
        print("错误: VideoSubtitleSkill 未注册")
        return
    
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"使用 execute 接口提取字幕: {url}")
    
    # 使用通用接口
    result = skill.execute(
        url=url,
        platform='youtube',
        language='en',
        include_auto=True
    )
    
    if result.success:
        data = result.data
        print(f"\n✅ 执行成功!")
        print(f"   标题: {data['title']}")
        print(f"   上传者: {data['uploader']}")
        print(f"   是否有字幕: {data['has_subtitles']}")
        
        if data['has_subtitles']:
            print(f"\n字幕预览 (前400字符):")
            print("-" * 60)
            print(data['subtitle_text'][:400])
            print("-" * 60)
    else:
        print(f"❌ 执行失败: {result.error}")
    
    print()


async def example_multi_language_support():
    """示例6: 多语言字幕支持"""
    print("=" * 60)
    print("示例6: 多语言字幕支持")
    print("=" * 60)
    
    skill = load_skill("video_subtitle")
    if not skill:
        print("错误: VideoSubtitleSkill 未注册")
        return
    
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # 尝试多种语言
    languages = ['zh-CN', 'en', 'ja', 'ko']
    
    print(f"检查视频的多语言字幕: {url}\n")
    
    for lang in languages:
        print(f"🌐 尝试语言: {lang}")
        
        result = skill.extract_youtube_subtitle(
            url=url,
            language=lang,
            include_auto=True
        )
        
        if result.success:
            data = result.data
            if data['has_subtitles']:
                print(f"   ✅ 找到字幕")
                print(f"      可用字幕: {data['available_subtitles'][:5]}")
                print(f"      自动字幕: {data['available_auto_captions'][:5]}")
            else:
                print(f"   ⚠️ 无此语言字幕")
        else:
            print(f"   ❌ 提取失败: {result.error}")
        
        print()


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 60)
    print("Agent Reach - VideoSubtitleSkill 使用示例")
    print("=" * 60 + "\n")
    
    # 检查技能是否已注册
    registry = get_registry()
    print(f"技能注册表统计: {registry.get_stats()}\n")
    
    # 检查 yt-dlp 是否安装
    try:
        import subprocess
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ yt-dlp 已安装，版本: {result.stdout.strip()}\n")
        else:
            print("⚠️ yt-dlp 可能未正确安装\n")
    except FileNotFoundError:
        print("⚠️ yt-dlp 未安装，请运行: pip install yt-dlp\n")
    
    # 运行示例
    await example_youtube_subtitle_extraction()
    await example_bilibili_subtitle_extraction()
    await example_video_content_analysis()
    await example_subtitle_summary_generation()
    await example_generic_execute_interface()
    await example_multi_language_support()
    
    print("=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
