#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding JSON 格式化工具
提供多种可读性选项
"""

import json
import os

def format_embeddings_compact(data):
    """紧凑格式：embedding在一行内"""
    result = []
    for item in data:
        formatted_item = {
            "prompt": item["prompt"],
            "embedding": item["embedding"],  # 保持为数组，但会在一行内
            "params": item["params"]
        }
        result.append(formatted_item)
    return result

def format_embeddings_truncated(data, show_dims=10):
    """截断格式：只显示前几维和后几维"""
    result = []
    for item in data:
        embedding = item["embedding"]
        if len(embedding) > show_dims * 2:
            # 显示前几维 + "..." + 后几维
            truncated = (embedding[:show_dims] + 
                        [f"... {len(embedding) - show_dims*2} more ..."] + 
                        embedding[-show_dims:])
            formatted_item = {
                "prompt": item["prompt"],
                "embedding_preview": truncated,
                "embedding_full": f"[{len(embedding)} dimensions - use programmatically]",
                "embedding": item["embedding"],  # 完整数据保留
                "params": item["params"]
            }
        else:
            formatted_item = item.copy()
        result.append(formatted_item)
    return result

def format_embeddings_summary(data):
    """摘要格式：用统计信息替代完整数组"""
    result = []
    for item in data:
        embedding = item["embedding"]
        
        # 计算统计信息
        stats = {
            "dimensions": len(embedding),
            "mean": round(sum(embedding) / len(embedding), 6),
            "min": round(min(embedding), 6),
            "max": round(max(embedding), 6),
            "first_5": [round(x, 6) for x in embedding[:5]],
            "last_5": [round(x, 6) for x in embedding[-5:]]
        }
        
        formatted_item = {
            "prompt": item["prompt"],
            "embedding_stats": stats,
            "embedding": item["embedding"],  # 完整数据保留
            "params": item["params"]
        }
        result.append(formatted_item)
    return result

def save_formatted_json(data, output_file, format_type="compact"):
    """保存格式化的JSON"""
    
    if format_type == "compact":
        formatted_data = format_embeddings_compact(data)
        # 自定义JSON编码器，让embedding数组紧凑显示
        json_str = json.dumps(formatted_data, ensure_ascii=False, indent=2)
        
    elif format_type == "truncated":
        formatted_data = format_embeddings_truncated(data, show_dims=5)
        json_str = json.dumps(formatted_data, ensure_ascii=False, indent=2)
        
    elif format_type == "summary":
        formatted_data = format_embeddings_summary(data)
        json_str = json.dumps(formatted_data, ensure_ascii=False, indent=2)
        
    else:  # default
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    return formatted_data

def main():
    """主函数"""
    INPUT_FILE = 'public/all_prompts_results_with_embeddings.json'
    
    # 检查输入文件
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到文件: {INPUT_FILE}")
        print("请先运行 generate_embeddings_offline.py")
        return
    
    # 读取数据
    print(f"📖 Reading data from: {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📝 Found {len(data)} prompts")
    
    # 生成不同格式的文件
    formats = {
        "compact": {
            "file": "public/embeddings_compact.json",
            "desc": "紧凑格式 - embedding在一行内"
        },
        "truncated": {
            "file": "public/embeddings_readable.json", 
            "desc": "可读格式 - 只显示部分embedding"
        },
        "summary": {
            "file": "public/embeddings_summary.json",
            "desc": "摘要格式 - 用统计信息代替"
        }
    }
    
    print("\n🎨 生成不同格式的文件...")
    
    for format_name, config in formats.items():
        print(f"🔄 生成 {config['desc']}...")
        
        try:
            formatted_data = save_formatted_json(data, config['file'], format_name)
            file_size = os.path.getsize(config['file']) / 1024
            
            print(f"✅ {config['file']} ({file_size:.1f} KB)")
            
            # 显示第一个示例
            if format_name == "summary":
                sample = formatted_data[0]
                print(f"   示例统计: {sample['embedding_stats']['dimensions']}维, "
                      f"均值={sample['embedding_stats']['mean']}")
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
    
    print(f"\n📋 原始文件大小: {os.path.getsize(INPUT_FILE) / 1024:.1f} KB")
    print("\n💡 使用建议:")
    print("- 开发调试时查看: embeddings_readable.json 或 embeddings_summary.json")
    print("- 前端集成使用: embeddings_compact.json (更小的文件大小)")
    print("- 完整数据备份: all_prompts_results_with_embeddings.json")

if __name__ == "__main__":
    main() 