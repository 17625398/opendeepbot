/**
 * Virtual Scroll Component
 * 虚拟滚动组件 - 用于处理大量数据的高性能渲染
 */

'use client'

import React, { useState, useRef, useEffect, useMemo } from 'react'
import { cn } from '@/lib/utils'

export interface VirtualScrollProps<T = any> {
  // 数据
  items: T[]
  // 每个item高度 (固定高度)
  itemHeight: number
  // 容器高度
  height: number
  // Item渲染组件
  renderItem: (item: T, index: number) => React.ReactNode
  // 容器类名
  className?: string
  // 缓冲区数量 (上下各渲染多少额外item)
  overscan?: number
  // 自定义item高度 (可选)
  getItemHeight?: (item: T, index: number) => number
}

export function VirtualScroll<T>({
  items,
  itemHeight: defaultItemHeight,
  height,
  renderItem,
  className,
  overscan = 3,
  getItemHeight,
}: VirtualScrollProps<T>) {
  const [scrollTop, setScrollTop] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const scrollElementRef = useRef<HTMLDivElement>(null)

  // 计算总高度
  const totalHeight = useMemo(() => {
    if (getItemHeight) {
      return items.reduce((sum, _, index) => sum + getItemHeight(items[index], index), 0)
    }
    return items.length * defaultItemHeight
  }, [items, defaultItemHeight, getItemHeight])

  // 计算可见item的范围
  const { startIndex, endIndex, offsetY } = useMemo(() => {
    let start = 0
    let end = 0
    let offset = 0

    if (getItemHeight) {
      // 动态高度
      let currentHeight = 0
      let index = 0

      // 找到startIndex
      while (index < items.length && currentHeight < scrollTop) {
        const h = getItemHeight(items[index], index)
        currentHeight += h
        index++
      }
      start = Math.max(0, index - overscan)

      // 计算offset
      let totalOffset = 0
      for (let i = 0; i < start; i++) {
        totalOffset += getItemHeight(items[i], i)
      }
      offset = totalOffset

      // 找到endIndex
      while (index < items.length && currentHeight < scrollTop + height) {
        currentHeight += getItemHeight(items[index], index)
        index++
      }
      end = Math.min(items.length, index + overscan)
    } else {
      // 固定高度
      start = Math.floor(scrollTop / defaultItemHeight)
      end = Math.min(items.length, start + Math.ceil(height / defaultItemHeight))
      start = Math.max(0, start - overscan)
      end = Math.min(items.length, end + overscan)
      offset = start * defaultItemHeight
    }

    return { startIndex: start, endIndex: end, offsetY: offset }
  }, [scrollTop, items, defaultItemHeight, height, overscan, getItemHeight])

  // 可见items
  const visibleItems = items.slice(startIndex, endIndex)

  // 滚动处理
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop)
  }

  // 滚动到底部
  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = totalHeight - height
    }
  }

  // 滚动到顶部
  const scrollToTop = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = 0
    }
  }

  // 滚动到指定index
  const scrollToIndex = (index: number) => {
    index = Math.max(0, Math.min(index, items.length - 1))
    let offset = 0

    if (getItemHeight) {
      offset = Array.from({ length: index }).reduce(
        (sum, i) => sum + getItemHeight(items[i], i),
        0
      )
    } else {
      offset = index * defaultItemHeight
    }

    if (containerRef.current) {
      containerRef.current.scrollTop = offset
    }
  }

  return (
    <div
      ref={containerRef}
      className={cn('overflow-auto relative', className)}
      style={{ height }}
      onScroll={handleScroll}
    >
      <div
        ref={scrollElementRef}
        className="relative"
        style={{ height: totalHeight }}
      >
        <div
          className="absolute top-0 left-0 right-0"
          style={{ transform: `translateY(${offsetY}px)` }}
        >
          {visibleItems.map((item, index) => (
            <div
              key={startIndex + index}
              style={{
                height: getItemHeight
                  ? getItemHeight(item, startIndex + index)
                  : defaultItemHeight,
              }}
            >
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
      
      {/* 滚动到按钮 (可选) */}
      <div className="absolute bottom-4 right-4 flex flex-col space-y-2">
        <button
          onClick={scrollToTop}
          className="p-2 bg-primary text-primary-foreground rounded-full shadow-lg hover:opacity-80"
          title="滚动到顶部"
        >
          ↑
        </button>
      </div>
    </div>
  )
}

/**
 * 简化的虚拟列表 (固定高度)
 */
export function VirtualList<T>({
  items,
  itemHeight,
  height,
  renderItem,
  className,
}: {
  items: T[]
  itemHeight: number
  height: number
  renderItem: (item: T, index: number) => React.ReactNode
  className?: string
}) {
  return (
    <VirtualScroll
      items={items}
      itemHeight={itemHeight}
      height={height}
      renderItem={renderItem}
      className={className}
      overscan={5}
    />
  )
}

/**
 * 虚拟文本列表 (用于长文本分段渲染)
 */
export interface VirtualTextProps {
  text: string
  height: number
  charPerLine?: number
  lineHeigheight?: number
  className?: string
}

export function VirtualText({
  text,
  height,
  charPerLine = 80,
  lineHeigheight = 24,
  className,
}: VirtualTextProps) {
  // 分段文本
  const chunks = useMemo(() => {
    const chunks: string[] = []
    const chars = text.length
    const chunkSize = charPerLine * 20 // 每段20行

    for (let i = 0; i < chars; i += chunkSize) {
      chunks.push(text.slice(i, i + chunkSize))
    }

    return chunks
  }, [text, charPerLine])

  const chunkHeight = 20 * lineHeigheight // 每段高度

  return (
    <VirtualScroll
      items={chunks}
      itemHeight={chunkHeight}
      height={height}
      renderItem={(chunk, index) => (
        <div
          key={index}
          className="p-4 whitespace-pre-wrap break-words"
          style={{ lineHeight: `${lineHeigheight}px` }}
        >
          {chunk}
        </div>
      )}
      className={className}
    />
  )
}

export default VirtualScroll
