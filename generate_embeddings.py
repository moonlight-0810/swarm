#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwarmChemistry Prompt Embedding Generator
为SwarmChemistry项目的prompt生成语义embedding向量

依赖安装：
pip install sentence-transformers numpy scikit-learn
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
import os
import time

class PromptEmbeddingGenerator:
    def __init__(self, model_name='all-MiniLM-L6-v2', reduce_dim=None):
        """
        初始化embedding生成器
        
        Args:
            model_name (str): sentence-transformers模型名称
            reduce_dim (int, optional): 如果指定，使用PCA降维到指定维度
        """
        print(f"🚀 Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.reduce_dim = reduce_dim
        self.pca = None
        
        print(f"✅ Model loaded successfully")
        print(f"📊 Original embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        
    def generate_embeddings(self, prompts):
        """
        为prompt列表生成embedding向量
        
        Args:
            prompts (list): prompt字符串列表
            
        Returns:
            numpy.ndarray: embedding矩阵
        """
        print(f"🔄 Generating embeddings for {len(prompts)} prompts...")
        
        # 生成原始embeddings
        embeddings = self.model.encode(prompts, show_progress_bar=True)
        
        # 可选：降维处理
        if self.reduce_dim and self.reduce_dim < embeddings.shape[1]:
            print(f"🔧 Reducing dimensions from {embeddings.shape[1]} to {self.reduce_dim}")
            self.pca = PCA(n_components=self.reduce_dim)
            embeddings = self.pca.fit_transform(embeddings)
            print(f"✅ Dimension reduction completed")
            
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
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Processing completed successfully!")
        print(f"📊 Statistics:")
        print(f"  - Total prompts: {len(prompts)}")
        print(f"  - Embedding dimension: {len(data[0]['embedding'])}")
        print(f"  - Output file size: {os.path.getsize(output_path) / 1024:.1f} KB")
        
        return data
    
    def save_pca_model(self, filepath):
        """保存PCA模型用于前端一致性"""
        if self.pca is not None:
            import pickle
            with open(filepath, 'wb') as f:
                pickle.dump(self.pca, f)
            print(f"📦 PCA model saved to: {filepath}")

def main():
    """主函数"""
    # 配置参数
    INPUT_FILE = 'public/all_prompts_results.json'  # 输入文件路径
    OUTPUT_FILE = 'public/all_prompts_results_with_embeddings.json'  # 输出文件路径
    MODEL_NAME = 'all-MiniLM-L6-v2'  # 推荐模型
    REDUCE_DIM = None  # 设置为整数启用降维，如：50, 100, 或 None 禁用
    
    try:
        print("🌊 SwarmChemistry Prompt Embedding Generator")
        print("=" * 50)
        
        # 创建生成器
        generator = PromptEmbeddingGenerator(
            model_name=MODEL_NAME,
            reduce_dim=REDUCE_DIM
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 