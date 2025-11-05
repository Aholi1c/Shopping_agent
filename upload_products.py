#!/usr/bin/env python3
"""
商品数据上传脚本
用于将JSON文件中的商品数据上传到数据库
"""

import requests
import json
import sys
import os

API_BASE_URL = "http://localhost:8000"

def upload_products_from_json(file_path):
    """从JSON文件上传商品数据"""
    try:
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 验证数据格式
        if not isinstance(data, dict) or 'products' not in data:
            print("❌ 错误：JSON格式不正确，需要包含'products'字段")
            return False
        
        products = data['products']
        if not isinstance(products, list):
            print("❌ 错误：'products'必须是数组格式")
            return False
        
        print(f"📦 准备上传 {len(products)} 个商品...")
        
        # 调用API上传
        url = f"{API_BASE_URL}/api/product-management/products/upload"
        
        # 增加超时时间到60秒
        response = requests.post(url, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 上传成功！")
            print(f"   成功: {result.get('success_count', 0)} 个")
            print(f"   失败: {result.get('error_count', 0)} 个")
            
            if result.get('errors'):
                print("\n⚠️  错误详情：")
                for error in result['errors'][:5]:  # 只显示前5个错误
                    print(f"   - {error}")
            
            return True
        else:
            print(f"❌ 上传失败：{response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误信息：{error_data.get('detail', '未知错误')}")
            except:
                print(f"   错误信息：{response.text}")
            return False
            
    except FileNotFoundError:
        print(f"❌ 错误：文件不存在 - {file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ 错误：JSON格式错误 - {e}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 错误：无法连接到服务器 {API_BASE_URL}")
        print("   请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # 默认使用当前目录下的 products_data.json
        file_path = os.path.join(os.path.dirname(__file__), 'products_data.json')
    
    if not os.path.exists(file_path):
        print(f"❌ 错误：文件不存在 - {file_path}")
        print("\n使用方法：")
        print(f"  python3 upload_products.py [json文件路径]")
        print(f"\n示例：")
        print(f"  python3 upload_products.py products_data.json")
        sys.exit(1)
    
    print(f"📄 正在读取文件: {file_path}")
    success = upload_products_from_json(file_path)
    
    if success:
        print("\n✨ 上传完成！您现在可以使用比价和分析功能了。")
        print("\n💡 提示：")
        print("   - 查询商品列表: GET /api/product-management/products")
        print("   - 查看统计信息: GET /api/product-management/products/stats")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

