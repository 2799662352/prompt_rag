#!/usr/bin/env python3

import os
import re
import argparse

class TxtToMarkdown:
    def __init__(self, input_dir, output_dir="artifacts/markdown_converted", list_type="unordered"):
        """初始化转换器，设置输入和输出目录."""
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.list_type = list_type  # "ordered" 或 "unordered"
        
    def convert_txt_to_markdown(self, content, filename):
        """将文本内容转换为Markdown格式."""
        # 移除文件名中的扩展名作为标题
        title = os.path.splitext(filename)[0]
        
        # 创建Markdown内容
        markdown_content = f"# {title}\n\n"
        
        # 分割逗号分隔的标签
        tags = [tag.strip() for tag in content.split(',')]
        
        # 创建标签列表
        for i, tag in enumerate(tags, 1):
            # 去除标签中的转义字符
            clean_tag = re.sub(r'\\', '', tag)
            
            # 根据列表类型添加列表项
            if self.list_type == "ordered":
                markdown_content += f"{i}. {clean_tag}\n"
            else:
                markdown_content += f"- {clean_tag}\n"
                
        return markdown_content
    
    def process_file(self, filepath):
        """处理单个txt文件."""
        try:
            # 读取文件
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 获取文件名
            filename = os.path.basename(filepath)
            
            # 转换为Markdown
            markdown_content = self.convert_txt_to_markdown(content, filename)
            
            # 确定输出路径
            rel_path = os.path.relpath(filepath, self.input_dir)
            output_path = os.path.join(self.output_dir, rel_path)
            
            # 更改文件扩展名为.md
            output_path = os.path.splitext(output_path)[0] + '.md'
            
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 写入Markdown内容
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"已处理: {filepath} -> {output_path}")
            return True
        except Exception as e:
            print(f"处理 {filepath} 出错: {e}")
            return False

    def process_directory(self):
        """处理输入目录中的所有txt文件."""
        # 创建输出目录（如果不存在）
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 统计
        processed_files = 0
        failed_files = 0
        
        # 遍历输入目录
        for root, dirs, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith('.txt'):
                    filepath = os.path.join(root, file)
                    success = self.process_file(filepath)
                    if success:
                        processed_files += 1
                    else:
                        failed_files += 1
        
        print(f"\n转换完成。处理了 {processed_files} 个文件。失败: {failed_files} 个。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将txt文件转换为Markdown格式.")
    parser.add_argument("--input", "-i", required=True, 
                        help="包含txt文件的输入目录")
    parser.add_argument("--output", "-o", default="artifacts/markdown_converted",
                        help="输出Markdown文件的目录 (默认: artifacts/markdown_converted)")
    parser.add_argument("--list-type", "-l", choices=["ordered", "unordered"], default="unordered",
                        help="列表类型：ordered (有序) 或 unordered (无序, 默认)")
   
    args = parser.parse_args()
    
    converter = TxtToMarkdown(
        input_dir=args.input,
        output_dir=args.output,
        list_type=args.list_type
    )
    converter.process_directory()