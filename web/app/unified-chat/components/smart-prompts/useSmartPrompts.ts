/**
 * useSmartPrompts Hook
 * ====================
 *
 * 智能问题生成逻辑 Hook
 * 根据页面内容自动生成相关问题建议
 */

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import type {
  SmartPrompt,
  PageContext,
  PromptGenerationConfig,
  QuestionTemplate,
  QuestionType,
} from "./types";

/** 问题模板库 */
const questionTemplates: QuestionTemplate[] = [
  {
    type: "summary",
    zh: [
      "总结一下这篇文章的主要内容",
      "这篇文章的核心观点是什么",
      "请简要概括这段内容",
      "这篇文章主要讲了什么",
      "提炼一下文章的关键信息",
    ],
    en: [
      "Summarize the main content of this article",
      "What are the core arguments of this article",
      "Briefly summarize this content",
      "What is this article mainly about",
      "Extract the key information from this article",
    ],
  },
  {
    type: "explanation",
    zh: [
      "解释一下{keyword}这个概念",
      "{keyword}是什么意思",
      "请详细说明{keyword}的含义",
      "如何理解{keyword}",
      "{keyword}的定义是什么",
    ],
    en: [
      "Explain the concept of {keyword}",
      "What does {keyword} mean",
      "Please elaborate on the meaning of {keyword}",
      "How to understand {keyword}",
      "What is the definition of {keyword}",
    ],
  },
  {
    type: "comparison",
    zh: [
      "这篇文章和传统观点有什么不同",
      "{keyword}和{keyword2}有什么区别",
      "对比一下文中提到的不同观点",
      "这种方法和之前的方法相比有什么优势",
      "这篇文章与其他同类文章有何异同",
    ],
    en: [
      "How does this article differ from traditional views",
      "What is the difference between {keyword} and {keyword2}",
      "Compare the different viewpoints mentioned in the article",
      "What are the advantages of this method compared to previous ones",
      "How is this article similar to or different from other articles on this topic",
    ],
  },
  {
    type: "application",
    zh: [
      "如何在实际中应用{keyword}",
      "请举例说明{keyword}的实际应用",
      "这个概念在实际工作中有哪些应用场景",
      "如何将文中的方法应用到实践中",
      "{keyword}对我们有什么实际意义",
    ],
    en: [
      "How to apply {keyword} in practice",
      "Please give examples of practical applications of {keyword}",
      "What are the practical application scenarios of this concept",
      "How to apply the methods in the article to practice",
      "What practical significance does {keyword} have for us",
    ],
  },
  {
    type: "analysis",
    zh: [
      "分析一下{keyword}的优缺点",
      "这篇文章的论证逻辑是什么",
      "如何评价文中提出的观点",
      "{keyword}存在哪些局限性",
      "请分析一下这个问题的深层原因",
    ],
    en: [
      "Analyze the pros and cons of {keyword}",
      "What is the logical structure of this article's argument",
      "How to evaluate the viewpoints proposed in the article",
      "What are the limitations of {keyword}",
      "Please analyze the underlying causes of this issue",
    ],
  },
  {
    type: "extension",
    zh: [
      "关于{keyword}还有哪些相关内容",
      "如何进一步了解这个话题",
      "与{keyword}相关的概念有哪些",
      "如果要深入研究这个领域，应该从哪些方面入手",
      "这篇文章还可以从哪些角度进行拓展",
    ],
    en: [
      "What other content is related to {keyword}",
      "How to further explore this topic",
      "What concepts are related to {keyword}",
      "If I want to study this field in depth, where should I start",
      "From what other angles can this article be expanded",
    ],
  },
];

/** 类型标签映射 */
const typeLabels: Record<string, { zh: string; en: string; icon: string }> = {
  summary: { zh: "总结", en: "Summary", icon: "FileText" },
  explanation: { zh: "解释", en: "Explanation", icon: "HelpCircle" },
  comparison: { zh: "对比", en: "Comparison", icon: "GitCompare" },
  application: { zh: "应用", en: "Application", icon: "Rocket" },
  analysis: { zh: "分析", en: "Analysis", icon: "BarChart3" },
  extension: { zh: "拓展", en: "Extension", icon: "Expand" },
};

/** 默认配置 */
const defaultConfig: PromptGenerationConfig = {
  count: 5,
  includeSummary: true,
  includeExplanation: true,
  includeComparison: true,
  includeApplication: true,
  language: "zh",
};

/**
 * 从文本中提取关键词
 */
function extractKeywords(text: string, maxKeywords: number = 5): string[] {
  if (!text) return [];

  // 常见停用词
  const stopWords = new Set([
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也",
    "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
    "之", "与", "及", "等", "或", "但", "而", "为", "于", "以", "及", "其", "这", "那",
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must",
    "shall", "can", "need", "dare", "ought", "used", "to", "of", "in", "for", "on", "with",
    "at", "by", "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
  ]);

  // 提取中文和英文单词
  const chineseWords = text.match(/[\u4e00-\u9fa5]{2,}/g) || [];
  const englishWords = text.toLowerCase().match(/[a-z]{3,}/g) || [];

  // 统计词频
  const wordFreq = new Map<string, number>();

  [...chineseWords, ...englishWords].forEach((word) => {
    if (!stopWords.has(word) && word.length >= 2) {
      wordFreq.set(word, (wordFreq.get(word) || 0) + 1);
    }
  });

  // 按频率排序并返回前 N 个
  return Array.from(wordFreq.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, maxKeywords)
    .map(([word]) => word);
}

/**
 * 填充模板中的占位符
 */
function fillTemplate(template: string, keywords: string[]): string {
  let result = template;

  // 替换 {keyword}
  if (result.includes("{keyword}") && keywords.length > 0) {
    result = result.replace("{keyword}", keywords[0]);
  }

  // 替换 {keyword2}
  if (result.includes("{keyword2}") && keywords.length > 1) {
    result = result.replace("{keyword2}", keywords[1]);
  } else if (result.includes("{keyword2}")) {
    result = result.replace("{keyword2}", "相关概念");
  }

  return result;
}

/**
 * 生成唯一ID
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 智能提示 Hook
 */
export function useSmartPrompts(
  pageContext: PageContext,
  config: Partial<PromptGenerationConfig> = {}
) {
  const mergedConfig = useMemo(
    () => ({ ...defaultConfig, ...config }),
    [config]
  );

  const [prompts, setPrompts] = useState<SmartPrompt[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [seed, setSeed] = useState(0);

  /**
   * 生成问题提示
   */
  const generatePrompts = useCallback(() => {
    setIsGenerating(true);

    try {
      const { title, summary, content, keywords: providedKeywords } = pageContext;
      const textToAnalyze = title + " " + (summary || "") + " " + (content || "");

      // 提取关键词
      const extractedKeywords = providedKeywords?.length
        ? providedKeywords
        : extractKeywords(textToAnalyze, 5);

      // 根据配置筛选模板
      const enabledTypes: QuestionType[] = [];
      if (mergedConfig.includeSummary) enabledTypes.push("summary");
      if (mergedConfig.includeExplanation) enabledTypes.push("explanation");
      if (mergedConfig.includeComparison) enabledTypes.push("comparison");
      if (mergedConfig.includeApplication) enabledTypes.push("application");

      // 如果没有启用任何类型，默认启用所有
      if (enabledTypes.length === 0) {
        enabledTypes.push("summary", "explanation", "analysis", "extension");
      }

      // 收集所有可用的问题
      const availablePrompts: SmartPrompt[] = [];

      enabledTypes.forEach((type) => {
        const template = questionTemplates.find((t) => t.type === type);
        if (!template) return;

        const templates = template[mergedConfig.language];
        const typeInfo = typeLabels[type];

        templates.forEach((text) => {
          const filledText = fillTemplate(text, extractedKeywords);
          availablePrompts.push({
            id: generateId(),
            text: filledText,
            type,
            label: typeInfo[mergedConfig.language],
            icon: typeInfo.icon,
            confidence: Math.random() * 0.3 + 0.7, // 模拟置信度
          });
        });
      });

      // 随机打乱并选择前 N 个
      const shuffled = availablePrompts.sort(() => 0.5 - Math.random());
      const selected = shuffled.slice(0, mergedConfig.count);

      // 如果没有生成足够的问题，添加默认问题
      if (selected.length < mergedConfig.count) {
        const defaults: SmartPrompt[] = [
          {
            id: generateId(),
            text: mergedConfig.language === "zh" ? "总结一下这篇文章" : "Summarize this article",
            type: "summary",
            label: typeLabels.summary[mergedConfig.language],
            icon: typeLabels.summary.icon,
            confidence: 0.9,
          },
          {
            id: generateId(),
            text: mergedConfig.language === "zh" ? "这篇文章有什么亮点" : "What are the highlights of this article",
            type: "analysis",
            label: typeLabels.analysis[mergedConfig.language],
            icon: typeLabels.analysis.icon,
            confidence: 0.85,
          },
        ];
        selected.push(...defaults.slice(0, mergedConfig.count - selected.length));
      }

      setPrompts(selected);
    } finally {
      setIsGenerating(false);
    }
  }, [pageContext, mergedConfig]);

  /**
   * 刷新问题
   */
  const refreshPrompts = useCallback(() => {
    setSeed((prev) => prev + 1);
  }, []);

  // 当依赖变化时重新生成 - 修复无限循环
  // 使用 useRef 来避免 generatePrompts 变化导致的无限循环
  const generatePromptsRef = useRef(generatePrompts);
  generatePromptsRef.current = generatePrompts;
  
  useEffect(() => {
    // 使用 ref 来避免依赖项变化
    generatePromptsRef.current();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seed, pageContext, mergedConfig]);

  return {
    prompts,
    isGenerating,
    refreshPrompts,
    regenerate: generatePrompts,
  };
}

export default useSmartPrompts;
