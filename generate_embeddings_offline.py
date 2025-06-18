#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwarmChemistry Prompt Embedding Generator (支持离线/镜像源)
为SwarmChemistry项目的prompt生成语义embedding向量

依赖安装：
pip install sentence-transformers numpy scikit-learn
"""

import json
import numpy as np
import os
import time
from pathlib import Path

# 设置环境变量使用国内镜像源
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.decomposition import PCA
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("⚠️ sentence-transformers not installed. Installing...")

class PromptEmbeddingGenerator:
    def __init__(self, model_name='all-MiniLM-L6-v2', reduce_dim=None, use_mirror=True):
        """
        初始化embedding生成器
        
        Args:
            model_name (str): sentence-transformers模型名称
            reduce_dim (int, optional): 如果指定，使用PCA降维到指定维度
            use_mirror (bool): 是否使用国内镜像源
        """
        if use_mirror:
            # 设置镜像源
            os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
            print(f"🌐 使用国内镜像源: {os.environ.get('HF_ENDPOINT')}")
        
        print(f"🚀 Loading model: {model_name}")
        
        try:
            # 尝试加载模型
            self.model = SentenceTransformer(model_name)
            self.reduce_dim = reduce_dim
            self.pca = None
            
            print(f"✅ Model loaded successfully")
            print(f"📊 Original embedding dimension: {self.model.get_sentence_embedding_dimension()}")
            
        except Exception as e:
            print(f"❌ 模型加载失败: {str(e)}")
            print("🔄 尝试使用本地替代方案...")
            self._fallback_to_simple_embedding()
    
    def _fallback_to_simple_embedding(self):
        """如果无法加载transformers模型，使用简单的文本特征作为替代"""
        print("⚠️  使用简化的文本特征替代方案")
        print("   这不是完整的语义embedding，但可以用于测试")
        self.model = None
        self.reduce_dim = None
        self.pca = None
    
    def _simple_text_features(self, text):
        """简单的文本特征提取（用于测试）"""
        features = []
        
        # 基本文本统计特征
        features.append(len(text))  # 文本长度
        features.append(len(text.split()))  # 单词数
        features.append(text.count(' '))  # 空格数
        
        # 字符频率特征（取前10个最常见字符）
        char_freq = {}
        for char in text.lower():
            if char.isalpha():
                char_freq[char] = char_freq.get(char, 0) + 1
        
        # 选择固定的特征维度
        common_chars = 'abcdefghijklmnopqrstuvwxyz'
        for char in common_chars:
            features.append(char_freq.get(char, 0))
        
        # 一些简单的语义特征
        emotional_words = ['joy', 'happy', 'sad', 'angry', 'fear', 'love', 'hate']
        for word in emotional_words:
            features.append(1 if word in text.lower() else 0)
        
        nature_words = ['flower', 'tree', 'water', 'fire', 'earth', 'sky', 'ocean']
        for word in nature_words:
            features.append(1 if word in text.lower() else 0)
        
        # 填充到固定维度（50维）
        while len(features) < 50:
            features.append(0.0)
        
        return np.array(features[:50], dtype=np.float32)
    
    def generate_embeddings(self, prompts):
        """
        为prompt列表生成embedding向量
        
        Args:
            prompts (list): prompt字符串列表
            
        Returns:
            numpy.ndarray: embedding矩阵
        """
        print(f"🔄 Generating embeddings for {len(prompts)} prompts...")
        
        if self.model is not None:
            # 使用真实的transformers模型
            embeddings = self.model.encode(prompts, show_progress_bar=True)
            
            # 可选：降维处理
            if self.reduce_dim and self.reduce_dim < embeddings.shape[1]:
                print(f"🔧 Reducing dimensions from {embeddings.shape[1]} to {self.reduce_dim}")
                self.pca = PCA(n_components=self.reduce_dim)
                embeddings = self.pca.fit_transform(embeddings)
                print(f"✅ Dimension reduction completed")
        else:
            # 使用简单的文本特征
            print("⚠️  使用简化特征生成embedding...")
            embeddings = np.array([self._simple_text_features(prompt) for prompt in prompts])
            
        return embeddings
    
    def process_json_file(self, input_file, output_file=None):
        """
        处理JSON文件，添加embedding字段
        
        Args:
            input_file (str): 输入JSON文件路径
            output_file (str, optional): 输出文件路径（默认覆盖原文件）
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
            
        # 读取原始数据
        print(f"📖 Reading data from: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            raise ValueError("JSON文件应该包含一个数组")
            
        # 提取所有prompt
        prompts = []
        for item in data:
            if 'prompt' not in item:
                raise ValueError(f"数据项缺少'prompt'字段: {item}")
            prompts.append(item['prompt'])
            
        print(f"📝 Found {len(prompts)} prompts:")
        for i, prompt in enumerate(prompts, 1):
            print(f"  {i}. \"{prompt}\"")
            
        # 生成embeddings
        embeddings = self.generate_embeddings(prompts)
        
        # 更新数据结构
        print("🔄 Updating data structure...")
        for i, item in enumerate(data):
            # 将numpy数组转换为Python列表，保留合理的精度
            embedding_list = embeddings[i].astype(np.float32).tolist()
            # 四舍五入到6位小数以减少文件大小
            embedding_list = [round(x, 6) for x in embedding_list]
            item['embedding'] = embedding_list
            
        # 保存结果
        output_path = output_file or input_file
        print(f"💾 Saving updated data to: {output_path}")
        
        # 使用紧凑格式保存，embedding数组在一行内
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
            
        print(f"✅ Processing completed successfully!")
        print(f"📊 Statistics:")
        print(f"  - Total prompts: {len(prompts)}")
        print(f"  - Embedding dimension: {len(data[0]['embedding'])}")
        print(f"  - Output file size: {os.path.getsize(output_path) / 1024:.1f} KB")
        
        if self.model is None:
            print("⚠️  注意：使用了简化的特征提取方案")
            print("   建议解决网络问题后使用完整的语义embedding")
        
        return data
    
    def save_pca_model(self, filepath):
        """保存PCA模型用于前端一致性"""
        if self.pca is not None:
            import pickle
            with open(filepath, 'wb') as f:
                pickle.dump(self.pca, f)
            print(f"📦 PCA model saved to: {filepath}")

def download_model_manually():
    """手动下载模型的说明"""
    print("🔧 手动下载模型方案：")
    print("1. 访问: https://hf-mirror.com/sentence-transformers/all-MiniLM-L6-v2")
    print("2. 下载所有文件到本地文件夹")
    print("3. 修改 MODEL_NAME 为本地路径")
    print()

def main():
    """主函数"""
    # 配置参数
    INPUT_FILE = 'public/all_prompts_results.json'  # 输入文件路径
    OUTPUT_FILE = 'public/all_prompts_results_with_embeddings.json'  # 输出文件路径
    
    # 模型配置选项
    MODELS = {
        'mirror': {
            'name': 'all-MiniLM-L6-v2',
            'use_mirror': True,
            'description': '使用国内镜像源'
        },
        'local': {
            'name': './models/all-MiniLM-L6-v2',  # 本地模型路径
            'use_mirror': False,
            'description': '使用本地模型'
        },
        'simple': {
            'name': None,
            'use_mirror': False,
            'description': '使用简化特征（不需要网络）'
        }
    }
    
    # 选择模型策略
    model_strategy = 'mirror'  # 可选: 'mirror', 'local', 'simple'
    
    REDUCE_DIM = None  # 设置为整数启用降维，如：50, 100, 或 None 禁用
    
    try:
        print("🌊 SwarmChemistry Prompt Embedding Generator")
        print("=" * 50)
        
        selected_model = MODELS[model_strategy]
        print(f"📋 使用策略: {selected_model['description']}")
        
        # 创建生成器
        if selected_model['name'] is None:
            # 简化模式
            generator = PromptEmbeddingGenerator(
                model_name='dummy',
                reduce_dim=REDUCE_DIM,
                use_mirror=False
            )
            generator.model = None  # 强制使用简化模式
        else:
            generator = PromptEmbeddingGenerator(
                model_name=selected_model['name'],
                reduce_dim=REDUCE_DIM,
                use_mirror=selected_model['use_mirror']
            )
        
        # 处理文件
        start_time = time.time()
        result_data = generator.process_json_file(INPUT_FILE, OUTPUT_FILE)
        end_time = time.time()
        
        # 可选：保存PCA模型
        if generator.pca is not None:
            generator.save_pca_model('pca_model.pkl')
        
        print("=" * 50)
        print(f"🎉 All done! Processing time: {end_time - start_time:.2f} seconds")
        print(f"🔗 Updated file ready for web integration: {OUTPUT_FILE}")
        
        # 显示第一个示例
        if result_data:
            sample = result_data[0]
            print(f"\n📋 Sample result:")
            print(f"  Prompt: \"{sample['prompt']}\"")
            print(f"  Embedding shape: {len(sample['embedding'])} dimensions")
            print(f"  Parameters: {len(sample['params'])} groups")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n🔧 可能的解决方案：")
        print("1. 检查网络连接")
        print("2. 使用科学上网工具")
        print("3. 手动下载模型文件")
        print("4. 使用简化模式（修改 model_strategy = 'simple'）")
        
        download_model_manually()
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 