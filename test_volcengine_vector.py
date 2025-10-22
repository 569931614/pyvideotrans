"""
火山引擎向量化服务测试脚本

测试向量化存储和检索功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from videotrans.hearsight.volcengine_vector import VolcengineVectorClient


def test_basic_connection():
    """测试基本连接"""
    print("=" * 60)
    print("测试1: 基本连接测试")
    print("=" * 60)

    # 使用提供的API密钥
    api_key = "2cad3d85-a6a5-433e-9ac5-41598e1aae83"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    embedding_model = "ep-20241217191853-w54rf"  # 示例endpoint ID，请替换为实际的

    client = VolcengineVectorClient(
        api_key=api_key,
        base_url=base_url,
        embedding_model=embedding_model
    )

    # 测试连接
    success = client.test_connection()

    if success:
        print("✅ 连接测试成功！")
        return client
    else:
        print("❌ 连接测试失败！")
        return None


def test_embedding():
    """测试文本向量化"""
    print("\n" + "=" * 60)
    print("测试2: 文本向量化")
    print("=" * 60)

    api_key = "2cad3d85-a6a5-433e-9ac5-41598e1aae83"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    embedding_model = "ep-20241217191853-w54rf"

    client = VolcengineVectorClient(
        api_key=api_key,
        base_url=base_url,
        embedding_model=embedding_model
    )

    # 测试单个文本
    test_text = "这是一个测试文本，用于测试火山引擎的向量化服务。"
    print(f"测试文本: {test_text}")

    embedding = client._get_embedding(test_text)

    if embedding:
        print(f"✅ 向量化成功!")
        print(f"   - 向量维度: {len(embedding)}")
        print(f"   - 前10个值: {embedding[:10]}")
        return True
    else:
        print("❌ 向量化失败!")
        return False


def test_batch_embedding():
    """测试批量文本向量化"""
    print("\n" + "=" * 60)
    print("测试3: 批量文本向量化")
    print("=" * 60)

    api_key = "2cad3d85-a6a5-433e-9ac5-41598e1aae83"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    embedding_model = "ep-20241217191853-w54rf"

    client = VolcengineVectorClient(
        api_key=api_key,
        base_url=base_url,
        embedding_model=embedding_model
    )

    # 测试多个文本
    test_texts = [
        "今天天气很好",
        "我喜欢看电影",
        "机器学习是一门重要的技术"
    ]

    print(f"测试文本数量: {len(test_texts)}")

    embeddings = client._batch_get_embeddings(test_texts)

    if embeddings and len(embeddings) == len(test_texts):
        print(f"✅ 批量向量化成功!")
        print(f"   - 返回向量数: {len(embeddings)}")
        for i, emb in enumerate(embeddings):
            if emb:
                print(f"   - 文本{i+1}维度: {len(emb)}")
        return True
    else:
        print("❌ 批量向量化失败!")
        return False


def test_store_and_search():
    """测试存储和检索"""
    print("\n" + "=" * 60)
    print("测试4: 存储和检索")
    print("=" * 60)

    api_key = "2cad3d85-a6a5-433e-9ac5-41598e1aae83"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    embedding_model = "ep-20241217191853-w54rf"

    client = VolcengineVectorClient(
        api_key=api_key,
        base_url=base_url,
        embedding_model=embedding_model
    )

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
        print("❌ 存储失败!")
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

    print("\n✅ 存储和检索测试完成!")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("火山引擎向量化服务测试")
    print("=" * 60 + "\n")

    print("⚠️  注意: 请确保已配置正确的API密钥和Embedding模型endpoint ID")
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
            print(f"\n❌ 测试 '{name}' 发生异常: {e}")
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
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    print(f"\n总计: {success_count}/{total_count} 个测试通过")

    if success_count == total_count:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个测试失败")


if __name__ == "__main__":
    main()
