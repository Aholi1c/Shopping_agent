#!/usr/bin/env python3
"""
网购助手初始化脚本
用于创建数据库表和初始化示例数据
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.models import (
    Base, User, Product, ProductSpec, PriceHistory,
    Coupon, ProductImage, UserPreference
)
from backend.app.models.schemas import PlatformType, DiscountType

def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")

    # 创建数据库引擎
    engine = create_engine(settings.database_url)

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    print("数据库表创建完成！")
    return engine

def create_sample_user(engine):
    """创建示例用户"""
    print("正在创建示例用户...")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 检查是否已存在用户
        existing_user = db.query(User).filter(User.username == "demo_user").first()
        if existing_user:
            print("示例用户已存在")
            return existing_user

        # 创建新用户
        user = User(
            username="demo_user",
            email="demo@example.com",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"示例用户创建成功，用户ID: {user.id}")
        return user

    except Exception as e:
        print(f"创建用户失败: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def create_sample_products(engine, user_id):
    """创建示例商品"""
    print("正在创建示例商品...")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        sample_products = [
            {
                "platform": PlatformType.JD,
                "product_id": "jd_001",
                "title": "iPhone 15 Pro Max 256GB 钛金属",
                "description": "Apple iPhone 15 Pro Max，搭载A17 Pro芯片，钛金属设计，支持Action按钮",
                "category": "手机",
                "brand": "Apple",
                "price": 9999.0,
                "original_price": 11999.0,
                "discount_rate": 0.17,
                "image_url": "https://example.com/iphone15.jpg",
                "product_url": "https://item.jd.com/123456.html",
                "rating": 4.8,
                "review_count": 2500,
                "sales_count": 10000,
                "stock_status": "in_stock"
            },
            {
                "platform": PlatformType.TAOBAO,
                "product_id": "tb_001",
                "title": "华为Mate 60 Pro 12GB+512GB 雅川青",
                "description": "华为Mate 60 Pro，麒麟9000S芯片，卫星通话，超光变影像",
                "category": "手机",
                "brand": "华为",
                "price": 6999.0,
                "original_price": 7999.0,
                "discount_rate": 0.13,
                "image_url": "https://example.com/mate60.jpg",
                "product_url": "https://item.taobao.com/item.htm?id=654321",
                "rating": 4.6,
                "review_count": 1800,
                "sales_count": 8000,
                "stock_status": "in_stock"
            },
            {
                "platform": PlatformType.PDD,
                "product_id": "pdd_001",
                "title": "小米14 16GB+1TB 白色",
                "description": "小米14，骁龙8 Gen 3处理器，徕卡光学镜头，澎湃OS",
                "category": "手机",
                "brand": "小米",
                "price": 4999.0,
                "original_price": 5999.0,
                "discount_rate": 0.17,
                "image_url": "https://example.com/mi14.jpg",
                "product_url": "https://mobile.yangkeduo.com/goods2.html?goods_id=789012",
                "rating": 4.5,
                "review_count": 1500,
                "sales_count": 6000,
                "stock_status": "in_stock"
            }
        ]

        created_products = []
        for product_data in sample_products:
            # 检查是否已存在
            existing = db.query(Product).filter(
                Product.platform == product_data["platform"],
                Product.product_id == product_data["product_id"]
            ).first()

            if not existing:
                product = Product(**product_data)
                db.add(product)
                db.commit()
                db.refresh(product)
                created_products.append(product)
                print(f"商品创建成功: {product.title}")
            else:
                created_products.append(existing)
                print(f"商品已存在: {existing.title}")

        return created_products

    except Exception as e:
        print(f"创建商品失败: {e}")
        db.rollback()
        return []
    finally:
        db.close()

def create_sample_specs(engine, products):
    """创建示例商品规格"""
    print("正在创建商品规格...")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        specs_data = [
            # iPhone 15 Pro 规格参数
            (products[0].id, "屏幕尺寸", "6.7英寸"),
            (products[0].id, "处理器", "A17 Pro"),
            (products[0].id, "内存", "256GB"),
            (products[0].id, "摄像头", "4800万主摄"),
            (products[0].id, "电池", "4422mAh"),

            # 华为Mate 60 Pro 规格参数
            (products[1].id, "屏幕尺寸", "6.82英寸"),
            (products[1].id, "处理器", "麒麟9000S"),
            (products[1].id, "内存", "512GB"),
            (products[1].id, "摄像头", "5000万主摄"),
            (products[1].id, "电池", "5000mAh"),

            # 小米14 规格参数
            (products[2].id, "屏幕尺寸", "6.36英寸"),
            (products[2].id, "处理器", "骁龙8 Gen 3"),
            (products[2].id, "内存", "1TB"),
            (products[2].id, "摄像头", "徕卡光学镜头"),
            (products[2].id, "电池", "4610mAh"),
        ]

        for product_id, spec_name, spec_value in specs_data:
            # 检查是否已存在
            existing = db.query(ProductSpec).filter(
                ProductSpec.product_id == product_id,
                ProductSpec.spec_name == spec_name
            ).first()

            if not existing:
                spec = ProductSpec(
                    product_id=product_id,
                    spec_name=spec_name,
                    spec_value=spec_value
                )
                db.add(spec)

        db.commit()
        print("商品规格创建完成！")

    except Exception as e:
        print(f"创建商品规格失败: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_coupons(engine):
    """创建示例优惠券"""
    print("正在创建示例优惠券...")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        coupons_data = [
            {
                "platform": PlatformType.JD,
                "coupon_id": "jd_coupon_001",
                "title": "京东满减券",
                "description": "全场商品满5000减300",
                "discount_type": DiscountType.FIXED,
                "discount_value": 300.0,
                "min_purchase_amount": 5000.0,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30),
                "usage_limit": 1000,
                "terms": "仅限京东平台使用"
            },
            {
                "platform": PlatformType.TAOBAO,
                "coupon_id": "tb_coupon_001",
                "title": "淘宝折扣券",
                "description": "数码品类8.8折优惠",
                "discount_type": DiscountType.PERCENTAGE,
                "discount_value": 12.0,
                "min_purchase_amount": 1000.0,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=15),
                "usage_limit": 500,
                "terms": "仅限数码品类使用"
            },
            {
                "platform": PlatformType.PDD,
                "coupon_id": "pdd_coupon_001",
                "title": "拼多多新人券",
                "description": "新用户立减50元",
                "discount_type": DiscountType.FIXED,
                "discount_value": 50.0,
                "min_purchase_amount": 200.0,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=7),
                "usage_limit": 100,
                "terms": "仅限新用户首次购买使用"
            }
        ]

        for coupon_data in coupons_data:
            # 检查是否已存在
            existing = db.query(Coupon).filter(
                Coupon.platform == coupon_data["platform"],
                Coupon.coupon_id == coupon_data["coupon_id"]
            ).first()

            if not existing:
                coupon = Coupon(**coupon_data)
                db.add(coupon)
                print(f"优惠券创建成功: {coupon.title}")
            else:
                print(f"优惠券已存在: {existing.title}")

        db.commit()
        print("优惠券创建完成！")

    except Exception as e:
        print(f"创建优惠券失败: {e}")
        db.rollback()
    finally:
        db.close()

def create_user_preferences(engine, user_id):
    """创建用户偏好"""
    print("正在创建用户偏好...")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        preferences = [
            {
                "user_id": user_id,
                "preference_type": "category",
                "preference_key": "手机",
                "preference_value": "手机",
                "weight": 0.8
            },
            {
                "user_id": user_id,
                "preference_type": "brand",
                "preference_key": "Apple",
                "preference_value": "Apple",
                "weight": 0.9
            },
            {
                "user_id": user_id,
                "preference_type": "price_range",
                "preference_key": "5000-10000",
                "preference_value": "5000-10000",
                "weight": 0.7
            }
        ]

        for pref_data in preferences:
            # 检查是否已存在
            existing = db.query(UserPreference).filter(
                UserPreference.user_id == user_id,
                UserPreference.preference_type == pref_data["preference_type"],
                UserPreference.preference_key == pref_data["preference_key"]
            ).first()

            if not existing:
                preference = UserPreference(**pref_data)
                db.add(preference)
                print(f"用户偏好创建成功: {pref_data['preference_type']} - {pref_data['preference_key']}")

        db.commit()
        print("用户偏好创建完成！")

    except Exception as e:
        print(f"创建用户偏好失败: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """主函数"""
    print("=" * 50)
    print("网购助手数据库初始化")
    print("=" * 50)

    try:
        # 初始化数据库
        engine = init_database()

        # 创建示例用户
        user = create_sample_user(engine)
        if not user:
            print("创建用户失败，退出")
            return

        # 创建示例商品
        products = create_sample_products(engine, user.id)

        # 创建商品规格
        if products:
            create_sample_specs(engine, products)

        # 创建优惠券
        create_sample_coupons(engine)

        # 创建用户偏好
        create_user_preferences(engine, user.id)

        print("\n" + "=" * 50)
        print("网购助手初始化完成！")
        print("=" * 50)
        print(f"示例用户: {user.username} (ID: {user.id})")
        print(f"示例商品数量: {len(products)}")
        print("现在可以启动应用了！")

    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()