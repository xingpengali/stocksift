# -*- coding: utf-8 -*-
"""
AKShare 适配器测试脚本
"""
import sys
sys.path.insert(0, '/Users/xingpeng/PyCharmMiscProject/stocksift/stocksift')
sys.path.insert(0, '/Users/xingpeng/PyCharmMiscProject/stocksift/stocksift/src')

from datasource.akshare_adapter import AkshareAdapter

def test_akshare_adapter():
    """测试 AKShare 适配器"""
    print("=" * 60)
    print("AKShare 适配器测试")
    print("=" * 60)
    
    # 创建适配器
    adapter = AkshareAdapter()
    
    # 测试连接
    print("\n1. 测试连接...")
    try:
        result = adapter.connect()
        print(f"   连接结果: {'成功' if result else '失败'}")
    except Exception as e:
        print(f"   连接失败: {e}")
        return
    
    # 测试获取股票列表
    print("\n2. 测试获取股票列表...")
    try:
        stocks = adapter.get_stock_list()
        print(f"   获取到 {len(stocks)} 只股票")
        if stocks:
            print(f"   示例: {stocks[0]}")
    except Exception as e:
        print(f"   获取失败: {e}")
    
    # 测试获取单只股票信息
    print("\n3. 测试获取单只股票信息...")
    try:
        stock = adapter.get_stock_basic('000001')
        print(f"   结果: {stock}")
    except Exception as e:
        print(f"   获取失败: {e}")
    
    # 测试获取实时行情
    print("\n4. 测试获取实时行情...")
    try:
        quotes = adapter.get_daily_quotes(['000001', '000002'])
        print(f"   获取到 {len(quotes)} 条行情")
        if quotes:
            print(f"   示例: {quotes[0]}")
    except Exception as e:
        print(f"   获取失败: {e}")
    
    # 测试获取指数列表
    print("\n5. 测试获取指数列表...")
    try:
        indices = adapter.get_index_list()
        print(f"   获取到 {len(indices)} 个指数")
        print(f"   示例: {indices[:3]}")
    except Exception as e:
        print(f"   获取失败: {e}")
    
    # 测试获取指数行情
    print("\n6. 测试获取指数行情...")
    try:
        index_quotes = adapter.get_index_quotes('000001')
        print(f"   获取到 {len(index_quotes)} 条指数行情")
        if index_quotes:
            print(f"   最新: {index_quotes[-1]}")
    except Exception as e:
        print(f"   获取失败: {e}")
    
    # 测试获取板块列表
    print("\n7. 测试获取行业板块列表...")
    try:
        industries = adapter.get_industry_list()
        print(f"   获取到 {len(industries)} 个行业")
        if industries:
            print(f"   示例: {industries[:3]}")
    except Exception as e:
        print(f"   获取失败: {e}")
    
    # 测试获取概念板块
    print("\n8. 测试获取概念板块列表...")
    try:
        concepts = adapter.get_concept_list()
        print(f"   获取到 {len(concepts)} 个概念")
        if concepts:
            print(f"   示例: {concepts[:3]}")
    except Exception as e:
        print(f"   获取失败: {e}")
    
    # 测试获取市场概览
    print("\n9. 测试获取市场概览...")
    try:
        overview = adapter.get_market_overview()
        print(f"   市场概览: {overview}")
    except Exception as e:
        print(f"   获取失败: {e}")
    
    # 断开连接
    adapter.disconnect()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_akshare_adapter()
