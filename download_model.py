#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动下载 sentence-transformers 模型
解决网络连接问题
"""

import os
import requests
from pathlib import Path
import json

def download_file(url, local_path, chunk_size=8192):
    """下载文件"""
    print(f"📥 下载: {url}")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
        
        print(f"✅ 下载完成: {local_path}")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def download_minilm_model():
    """下载 all-MiniLM-L6-v2 模型"""
    
    # 镜像源 URLs
    base_urls = [
        "https://hf-mirror.com/sentence-transformers/all-MiniLM-L6-v2/resolve/main",
        "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main"
    ]
    
    # 需要下载的文件
    files_to_download = [
        "config.json",
        "pytorch_model.bin", 
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.txt",
        "special_tokens_map.json",
        "1_Pooling/config.json"
    ]
    
    # 本地存储路径
    model_dir = Path("./models/all-MiniLM-L6-v2")
    
    print("🚀 开始下载 all-MiniLM-L6-v2 模型...")
    print(f"📁 保存到: {model_dir.absolute()}")
    
    success_count = 0
    
    for base_url in base_urls:
        print(f"\n🌐 尝试镜像源: {base_url}")
        
        for file_name in files_to_download:
            if file_name == "1_Pooling/config.json":
                url = f"{base_url}/1_Pooling/config.json"
                local_path = model_dir / "1_Pooling" / "config.json"
            else:
                url = f"{base_url}/{file_name}"
                local_path = model_dir / file_name
            
            # 如果文件已存在，跳过
            if local_path.exists():
                print(f"⏭️  跳过已存在文件: {local_path}")
                success_count += 1
                continue
            
            if download_file(url, local_path):
                success_count += 1
            else:
                print(f"❌ 文件下载失败: {file_name}")
        
        # 如果所有文件都下载成功，跳出循环
        if success_count == len(files_to_download):
            break
    
    print(f"\n📊 下载统计: {success_count}/{len(files_to_download)} 文件成功")
    
    if success_count == len(files_to_download):
        print("✅ 模型下载完成！")
        print(f"📁 模型路径: {model_dir.absolute()}")
        print("\n🔧 使用方法:")
        print("编辑 generate_embeddings_offline.py，修改:")
        print(f"model_strategy = 'local'")
        print(f"MODELS['local']['name'] = '{model_dir.absolute()}'")
        return True
    else:
        print("❌ 模型下载不完整")
        return False

def main():
    print("🌊 SwarmChemistry 模型下载工具")
    print("=" * 50)
    
    # 检查网络连接
    print("🔍 检查网络连接...")
    test_urls = [
        "https://hf-mirror.com",
        "https://huggingface.co"
    ]
    
    available_mirrors = []
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                available_mirrors.append(url)
                print(f"✅ {url} 可访问")
        except:
            print(f"❌ {url} 无法访问")
    
    if not available_mirrors:
        print("❌ 无法访问任何镜像源，请检查网络连接")
        return False
    
    # 下载模型
    return download_minilm_model()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 准备就绪！可以运行 generate_embeddings_offline.py")
    else:
        print("\n⚠️  建议使用简化模式: model_strategy = 'simple'") 