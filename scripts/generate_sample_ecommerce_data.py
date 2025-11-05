#!/usr/bin/env python3
"""
电商平台数据生成器
生成示例数据用于RAG知识库构建
"""

import pandas as pd
import random
import json
from datetime import datetime, timedelta
import os

class EcommerceDataGenerator:
    def __init__(self):
        self.brands = {
            'Apple': ['iPhone 15 Pro', 'iPhone 15', 'MacBook Air', 'iPad Air', 'Apple Watch'],
            'Xiaomi': ['小米14', '小米14 Pro', 'Redmi K70', '小米平板6', '小米手环8'],
            'Huawei': ['Mate 60 Pro', 'P60 Pro', 'MatePad Pro', 'Watch GT 4', 'FreeBuds Pro 3'],
            'Samsung': ['Galaxy S24', 'Galaxy S24 Ultra', 'Tab S9', 'Galaxy Watch 6', 'Buds2 Pro'],
            'OPPO': ['Find X7', 'Reno11', 'OnePlus 12', 'Pad 2', 'Enco Air 3']
        }

        self.categories = {
            '智能手机': ['旗舰机', '中端机', '入门机', '游戏手机', '拍照手机'],
            '笔记本电脑': ['轻薄本', '游戏本', '商务本', '二合一', '创作本'],
            '平板电脑': ['娱乐平板', '办公平板', '绘画平板', '学习平板'],
            '智能手表': ['运动手表', '商务手表', '时尚手表', '健康手表'],
            '无线耳机': ['降噪耳机', '运动耳机', '商务耳机', '音乐耳机']
        }

        self.platforms = ['jd', 'taobao', 'pdd', 'suning', 'gome']

        self.specs_templates = {
            '智能手机': {
                'screen_size': ['6.1英寸', '6.36英寸', '6.7英寸', '6.8英寸'],
                'processor': ['A17 Pro芯片', '骁龙8 Gen 3', '天玑9300', '麒麟9000S'],
                'ram': ['8GB', '12GB', '16GB'],
                'storage': ['128GB', '256GB', '512GB', '1TB'],
                'battery': ['4000mAh', '4500mAh', '5000mAh', '5500mAh'],
                'camera': ['4800万像素', '5000万像素', '6400万像素', '1亿像素'],
                'os': ['iOS 17', 'Android 14', 'HarmonyOS 4.0', 'MIUI 14'],
                'weight': ['180g', '190g', '200g', '220g'],
                'material': ['玻璃', '金属', '陶瓷', '素皮']
            },
            '笔记本电脑': {
                'screen_size': ['13.3英寸', '14英寸', '15.6英寸', '16英寸'],
                'processor': ['M2芯片', 'i5-1340P', 'i7-13700H', 'R7 7840HS'],
                'ram': ['8GB', '16GB', '32GB'],
                'storage': ['256GB SSD', '512GB SSD', '1TB SSD', '2TB SSD'],
                'battery': ['50Wh', '60Wh', '70Wh', '80Wh'],
                'graphics': ['集成显卡', 'RTX 4050', 'RTX 4060', 'M2 GPU'],
                'os': ['macOS', 'Windows 11', 'Ubuntu'],
                'weight': ['1.2kg', '1.5kg', '1.8kg', '2.2kg'],
                'material': ['铝合金', '镁合金', '碳纤维']
            }
        }

        self.review_templates = {
            'positive': [
                '产品质量非常好，值得推荐',
                '物流很快，包装完好',
                '性能强劲，使用体验佳',
                '外观设计精美，做工精良',
                '性价比很高，推荐购买'
            ],
            'negative': [
                '价格有点贵，希望能再便宜一些',
                '电池续航一般，需要经常充电',
                '系统偶尔会卡顿，有待优化',
                '配件较少，需要额外购买',
                '发热比较明显，玩游戏时更明显'
            ],
            'neutral': [
                '整体还不错，符合预期',
                '功能齐全，日常使用足够',
                '品牌信誉好，质量有保障',
                '客服响应及时，服务态度好'
            ]
        }

    def generate_products_data(self, num_products=200):
        """生成商品基本信息数据"""
        products = []

        for i in range(num_products):
            brand = random.choice(list(self.brands.keys()))
            product_name_base = random.choice(self.brands[brand])
            category = random.choice(list(self.categories.keys()))
            subcategory = random.choice(self.categories[category])
            platform = random.choice(self.platforms)

            # 生成规格变体
            storage_variants = ['128GB', '256GB', '512GB'] if '手机' in category else ['256GB', '512GB', '1TB']
            color_variants = ['黑色', '白色', '蓝色', '红色', '金色']

            for storage in storage_variants[:2]:  # 每个产品生成2个存储版本
                for color in color_variants[:2]:  # 每个存储版本生成2个颜色
                    product_id = f"{brand.lower()}_{product_name_base.lower().replace(' ', '_')}_{storage}_{color}_{i}"

                    base_price = random.randint(1000, 15000)
                    discount_rate = random.uniform(0, 0.3)
                    current_price = int(base_price * (1 - discount_rate))

                    product = {
                        'product_id': product_id,
                        'product_name': f"{brand} {product_name_base} {storage} {color}",
                        'brand': brand,
                        'category': category,
                        'subcategory': subcategory,
                        'current_price': current_price,
                        'original_price': base_price,
                        'discount_rate': round(discount_rate * 100, 1),
                        'platform': platform,
                        'product_url': f"https://www.{platform}.com/product/{product_id}",
                        'image_url': f"https://img.{platform}.com/{product_id}.jpg",
                        'stock_status': random.choice(['有货', '预售', '缺货']),
                        'shipping_info': random.choice(['免运费', '满99包邮', '运费10元']),
                        'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
                        'updated_at': datetime.now().strftime('%Y-%m-%d')
                    }
                    products.append(product)

        return pd.DataFrame(products)

    def generate_specifications_data(self, products_df):
        """生成商品规格参数数据"""
        specifications = []

        for _, product in products_df.iterrows():
            category = product['category']
            specs_template = self.specs_templates.get(category, self.specs_templates['智能手机'])

            spec_data = {
                'product_id': product['product_id'],
                'screen_size': random.choice(specs_template['screen_size']),
                'processor': random.choice(specs_template['processor']),
                'ram': random.choice(specs_template['ram']),
                'storage': product['product_name'].split()[-1],  # 从产品名提取存储容量
                'battery': random.choice(specs_template['battery']),
                'camera': random.choice(specs_template['camera']) if '手机' in category else 'N/A',
                'os': random.choice(specs_template['os']),
                'weight': random.choice(specs_template['weight']),
                'material': random.choice(specs_template['material']),
                'colors': product['product_name'].split()[-1],  # 从产品名提取颜色
                'network': '5G',
                'features': self._generate_features(category)
            }
            specifications.append(spec_data)

        return pd.DataFrame(specifications)

    def generate_price_history_data(self, products_df, days_history=180):
        """生成价格历史数据"""
        price_history = []

        for _, product in products_df.iterrows():
            base_price = product['original_price']
            current_price = product['current_price']

            # 生成历史价格点
            for days_ago in range(days_history, 0, -7):  # 每7天一个价格点
                date = datetime.now() - timedelta(days=days_ago)

                # 模拟价格波动
                price_variation = random.uniform(0.8, 1.2)
                historical_price = int(base_price * price_variation)

                # 特殊促销日期
                if date.month == 6 and date.day >= 1 and date.day <= 18:  # 618
                    historical_price = int(base_price * 0.8)
                elif date.month == 11 and date.day >= 1 and date.day <= 11:  # 双11
                    historical_price = int(base_price * 0.7)

                price_entry = {
                    'product_id': product['product_id'],
                    'price': historical_price,
                    'platform': product['platform'],
                    'discount_type': self._get_discount_type(date, historical_price, base_price),
                    'promotion_info': self._get_promotion_info(date),
                    'date': date.strftime('%Y-%m-%d'),
                    'is_stock_available': random.choice([True, False]),
                    'seller_info': f"{product['brand']}官方旗舰店",
                    'monthly_sales': random.randint(100, 50000)
                }
                price_history.append(price_entry)

        return pd.DataFrame(price_history)

    def generate_reviews_data(self, products_df, reviews_per_product=50):
        """生成用户评价数据"""
        reviews = []

        for _, product in products_df.iterrows():
            for i in range(reviews_per_product):
                rating = random.choice([5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0])

                # 根据评分选择评论模板
                if rating >= 4.0:
                    template = random.choice(self.review_templates['positive'])
                elif rating >= 3.0:
                    template = random.choice(self.review_templates['neutral'])
                else:
                    template = random.choice(self.review_templates['negative'])

                # 生成个性化的评论内容
                review_content = self._generate_review_content(template, product, rating)

                review = {
                    'product_id': product['product_id'],
                    'username': f"用户{random.randint(10000, 99999)}",
                    'rating': rating,
                    'content': review_content['content'],
                    'pros': review_content['pros'],
                    'cons': review_content['cons'],
                    'purchase_date': (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
                    'helpful_count': random.randint(0, 100),
                    'verified_purchase': random.choice([True, False]),
                    'user_level': random.choice(['VIP会员', '普通会员', '新会员']),
                    'tags': self._generate_review_tags(product['category'])
                }
                reviews.append(review)

        return pd.DataFrame(reviews)

    def _generate_features(self, category):
        """生成产品特性列表"""
        feature_pools = {
            '智能手机': ['5G网络', 'NFC', '快速充电', '无线充电', '指纹识别', '面部识别', '防水防尘'],
            '笔记本电脑': ['背光键盘', '指纹识别', '快速充电', 'WiFi 6', '蓝牙5.0', '高清摄像头'],
            '平板电脑': ['手写笔支持', '4K显示屏', '指纹识别', '快速充电', '立体声扬声器'],
            '智能手表': ['心率监测', '血氧监测', 'GPS定位', '防水50米', '睡眠监测'],
            '无线耳机': ['主动降噪', '通透模式', '快速充电', '无线充电', '防水防汗']
        }

        features = random.sample(feature_pools.get(category, feature_pools['智能手机']), 3)
        return '/'.join(features)

    def _get_discount_type(self, date, price, base_price):
        """获取折扣类型"""
        discount_ratio = price / base_price

        if discount_ratio < 0.8:
            return '大促优惠'
        elif discount_ratio < 0.9:
            return '满减优惠'
        elif discount_ratio < 0.95:
            return '店铺优惠券'
        else:
            return '无优惠'

    def _get_promotion_info(self, date):
        """获取促销信息"""
        if date.month == 6 and 1 <= date.day <= 18:
            return '618年中大促'
        elif date.month == 11 and 1 <= date.day <= 11:
            return '双11全球狂欢节'
        elif date.month == 12 and 12 <= date.day <= 25:
            return '双12年终大促'
        else:
            return '日常优惠'

    def _generate_review_content(self, template, product, rating):
        """生成个性化评论内容"""
        brand = product['brand']
        category = product['category']

        # 根据产品特性定制评论
        category_features = {
            '智能手机': ['拍照', '续航', '性能', '系统', '屏幕'],
            '笔记本电脑': ['性能', '续航', '散热', '屏幕', '便携性'],
            '平板电脑': ['屏幕', '续航', '性能', '便携性', '笔支持'],
            '智能手表': ['续航', '健康监测', '运动功能', '外观', '准确性'],
            '无线耳机': ['音质', '降噪', '续航', '舒适度', '连接稳定性']
        }

        features = random.sample(category_features.get(category, ['质量', '服务']), 2)

        content = template
        if rating >= 4.0:
            pros = f"{features[0]}很好/{features[1]}不错/品牌值得信赖"
            cons = "无明显缺点"
        elif rating >= 3.0:
            pros = f"{features[0]}还可以"
            cons = f"{features[1]}有待改进"
        else:
            pros = "包装完好"
            cons = f"{features[0]}/{features[1]}不理想"

        return {
            'content': content,
            'pros': pros,
            'cons': cons
        }

    def _generate_review_tags(self, category):
        """生成评价标签"""
        tag_pools = {
            '智能手机': ['拍照', '性能', '外观', '续航', '性价比'],
            '笔记本电脑': ['办公', '学习', '游戏', '便携', '性能'],
            '平板电脑': ['娱乐', '学习', '办公', '绘画', '阅读'],
            '智能手表': ['运动', '健康', '时尚', '实用', '续航'],
            '无线耳机': ['音质', '降噪', '便携', '舒适', '续航']
        }

        tags = random.sample(tag_pools.get(category, tag_pools['智能手机']), 3)
        return '/'.join(tags)

    def generate_all_data(self, num_products=200):
        """生成所有数据并保存为CSV文件"""
        print("开始生成电商数据...")

        # 创建数据目录
        data_dir = "data/ecommerce"
        os.makedirs(data_dir, exist_ok=True)

        # 生成各类数据
        print("生成商品基本信息...")
        products_df = self.generate_products_data(num_products)
        products_df.to_csv(f"{data_dir}/products.csv", index=False, encoding='utf-8-sig')

        print("生成商品规格参数...")
        specs_df = self.generate_specifications_data(products_df)
        specs_df.to_csv(f"{data_dir}/specifications.csv", index=False, encoding='utf-8-sig')

        print("生成价格历史...")
        price_df = self.generate_price_history_data(products_df)
        price_df.to_csv(f"{data_dir}/price_history.csv", index=False, encoding='utf-8-sig')

        print("生成用户评价...")
        reviews_df = self.generate_reviews_data(products_df.head(50))  # 只为前50个商品生成评价
        reviews_df.to_csv(f"{data_dir}/reviews.csv", index=False, encoding='utf-8-sig')

        # 生成数据说明文件
        self._generate_data_documentation(data_dir)

        print(f"数据生成完成！文件保存在 {data_dir}/ 目录下")
        print(f"- 商品数据: {len(products_df)} 条记录")
        print(f"- 规格参数: {len(specs_df)} 条记录")
        print(f"- 价格历史: {len(price_df)} 条记录")
        print(f"- 用户评价: {len(reviews_df)} 条记录")

    def _generate_data_documentation(self, data_dir):
        """生成数据说明文档"""
        doc_content = """# 电商平台数据集说明

## 数据集概述
本数据集包含了多个电商平台的商品信息、价格历史、规格参数和用户评价数据，用于训练和测试RAG商品知识库系统。

## 数据文件说明

### 1. products.csv - 商品基本信息
- product_id: 商品唯一标识
- product_name: 商品名称
- brand: 品牌
- category: 商品类别
- subcategory: 商品子类别
- current_price: 当前价格
- original_price: 原价
- discount_rate: 折扣率
- platform: 平台
- product_url: 商品链接
- image_url: 商品图片链接
- stock_status: 库存状态
- shipping_info: 配送信息
- created_at: 创建时间
- updated_at: 更新时间

### 2. specifications.csv - 商品规格参数
- product_id: 商品ID
- screen_size: 屏幕尺寸
- processor: 处理器
- ram: 内存
- storage: 存储容量
- battery: 电池容量
- camera: 摄像头
- os: 操作系统
- weight: 重量
- material: 材质
- colors: 颜色
- network: 网络类型
- features: 产品特性

### 3. price_history.csv - 价格历史
- product_id: 商品ID
- price: 价格
- platform: 平台
- discount_type: 折扣类型
- promotion_info: 促销信息
- date: 日期
- is_stock_available: 是否有货
- seller_info: 卖家信息
- monthly_sales: 月销量

### 4. reviews.csv - 用户评价
- product_id: 商品ID
- username: 用户名
- rating: 评分
- content: 评价内容
- pros: 优点
- cons: 缺点
- purchase_date: 购买日期
- helpful_count: 有用投票数
- verified_purchase: 是否验证购买
- user_level: 用户等级
- tags: 评价标签

## 数据格式说明
- 所有文本字段使用UTF-8编码
- 价格单位为人民币元
- 日期格式为YYYY-MM-DD
- 评分范围为1.0-5.0

## 使用建议
1. 数据可用于RAG知识库构建
2. 支持商品推荐和价格分析
3. 可用于训练商品分类和情感分析模型
4. 支持市场趋势分析和竞品对比

## 注意事项
- 数据为模拟生成，仅供测试使用
- 使用时请替换为真实数据
- 确保数据隐私和合规性要求
"""

        with open(f"{data_dir}/README.md", "w", encoding="utf-8") as f:
            f.write(doc_content)

if __name__ == "__main__":
    # 创建数据生成器实例
    generator = EcommerceDataGenerator()

    # 生成示例数据（50个商品，约200条商品记录）
    generator.generate_all_data(num_products=50)

    print("\n数据生成完成！请查看 data/ecommerce/ 目录下的文件。")