"""
火山引擎向量化服务测试脚本

测试向量化存储和检索功能
"""

import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from videotrans.hearsight.volcengine_vector import VolcengineVectorClient


def load_config():
    """从配置文件加载火山引擎配置"""
    config_path = os.path.join(os.path.dirname(__file__), "hearsight_config.json")
    if not os.path.exists(config_path):
        print(f"[警告] 配置文件不存在: {config_path}")
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    vector_config = config.get('vector', {})
    volc_config = vector_config.get('volcengine', {})

    return volc_config


def get_client_from_config():
    """从配置文件创建客户端"""
    volc_config = load_config()

    if not volc_config:
        # 使用默认配置
        print("[警告] 未找到配置文件，使用默认配置")
        api_key = "2cad3d85-a6a5-433e-9ac5-41598e1aae83"
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
        embedding_model = "ep-20241217191853-w54rf"
    else:
        api_key = volc_config.get('api_key', '')
        base_url = volc_config.get('base_url', 'https://ark.cn-beijing.volces.com/api/v3')
        embedding_model = volc_config.get('embedding_model', '')

    # 验证配置
    print("\n" + "=" * 60)
    print("当前配置:")
    print("=" * 60)
    print(f"API Key: {'[已设置]' if api_key else '[未设置]'}")
    print(f"Base URL: {base_url}")
    print(f"Embedding Model: {embedding_model if embedding_model else '[未设置]'}")

    if not api_key:
        print("\n[错误] API Key 未配置！")
        print("请在 hearsight_config.json 中配置 vector.volcengine.api_key")
        return None

    if not embedding_model:
        print("\n[错误] Embedding Model 未配置！")
        print("请在 hearsight_config.json 中配置 vector.volcengine.embedding_model")
        print("\n获取Embedding Model的步骤:")
        print("1. 访问: https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint")
        print("2. 创建或查找您的 Embedding 模型端点")
        print("3. 复制 Endpoint ID (格式如: ep-20241217191853-xxxxx)")
        return None

    return VolcengineVectorClient(
        api_key=api_key,
        base_url=base_url,
        embedding_model=embedding_model
    )


def test_basic_connection():
    """测试基本连接"""
    print("\n" + "=" * 60)
    print("测试1: 基本连接测试")
    print("=" * 60)

    client = get_client_from_config()
    if not client:
        return None

    # 测试连接
    success = client.test_connection()

    if success:
        print("[OK] 连接测试成功！")
        return client
    else:
        print("[Failed] 连接测试失败！")
        return None


def test_embedding():
    """测试文本向量化"""
    print("\n" + "=" * 60)
    print("测试2: 文本向量化")
    print("=" * 60)

    client = get_client_from_config()
    if not client:
        return False

    # 测试单个文本
    test_text = "这是一个测试文本，用于测试火山引擎的向量化服务。"
    print(f"测试文本: {test_text}")

    embedding = client._get_embedding(test_text)

    if embedding:
        print(f"[OK] 向量化成功!")
        print(f"   - 向量维度: {len(embedding)}")
        print(f"   - 前10个值: {embedding[:10]}")
        return True
    else:
        print("[Failed] 向量化失败!")
        return False


def test_batch_embedding():
    """测试批量文本向量化"""
    print("\n" + "=" * 60)
    print("测试3: 批量文本向量化")
    print("=" * 60)

    client = get_client_from_config()
    if not client:
        return False

    # 测试多个文本
    test_texts = [
        "今天天气很好",
        "我喜欢看电影",
        "机器学习是一门重要的技术"
    ]

    print(f"测试文本数量: {len(test_texts)}")

    embeddings = client._batch_get_embeddings(test_texts)

    if embeddings and len(embeddings) == len(test_texts):
        print(f"[OK] 批量向量化成功!")
        print(f"   - 返回向量数: {len(embeddings)}")
        for i, emb in enumerate(embeddings):
            if emb:
                print(f"   - 文本{i+1}维度: {len(emb)}")
        return True
    else:
        print("[Failed] 批量向量化失败!")
        return False


def test_store_and_search():
    """测试存储和检索"""
    print("\n" + "=" * 60)
    print("测试4: 存储和检索")
    print("=" * 60)

    client = get_client_from_config()
    if not client:
        return False

    # 模拟视频摘要数据
    video_path = "test_video.mp4"
    summary = {
        "topic": "Python编程教程",
        "summary": "本视频介绍了Python编程的基础知识，包括变量、函数和类的使用。",
        "total_duration": 300.0
    }

    paragraphs = [
        {
            "text": "大家好，欢迎来到Python编程教程。今天我们将学习Python的基础知识。",
            "summary": "课程介绍",
            "start_time": 0.0,
            "end_time": 10.0
        },
        {
            "text": "首先，让我们了解什么是变量。变量是用来存储数据的容器。",
            "summary": "变量的概念",
            "start_time": 10.0,
            "end_time": 30.0
        },
        {
            "text": "接下来，我们学习函数。函数是可重用的代码块，可以执行特定的任务。",
            "summary": "函数的使用",
            "start_time": 30.0,
            "end_time": 60.0
        }
    ]

    # 存储
    print("正在存储视频摘要...")
    success = client.store_summary(
        video_path=video_path,
        summary=summary,
        paragraphs=paragraphs
    )

    if not success:
        print("[Failed] 存储失败!")
        return False

    # 检索
    print("\n正在检索...")
    queries = [
        "什么是变量？",
        "如何使用函数？",
        "Python编程"
    ]

    for query in queries:
        print(f"\n查询: {query}")
        results = client.search(query, n_results=2)

        if results:
            print(f"找到 {len(results)} 个相关结果:")
            for i, result in enumerate(results, 1):
                print(f"\n  结果 {i}:")
                print(f"    相似度: {result['similarity']:.4f}")
                print(f"    类型: {result['metadata']['type']}")
                print(f"    内容: {result['document'][:80]}...")
        else:
            print("  未找到结果")

    print("\n[OK] 存储和检索测试完成!")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("火山引擎向量化服务测试")
    print("=" * 60 + "\n")

    print("[提示] 请确保已配置正确的API密钥和Embedding模型endpoint ID")
    print()

    # 运行测试
    tests = [
        ("基本连接", test_basic_connection),
        ("文本向量化", test_embedding),
        ("批量向量化", test_batch_embedding),
        ("存储和检索", test_store_and_search)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[错误] 测试 '{name}' 发生异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    success_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for name, result in results:
        status = "[通过]" if result else "[失败]"
        print(f"{name}: {status}")

    print(f"\n总计: {success_count}/{total_count} 个测试通过")

    if success_count == total_count:
        print("\n[成功] 所有测试通过!")
    else:
        print(f"\n[警告] 有 {total_count - success_count} 个测试失败")


if __name__ == "__main__":
    main()
