"""
HearSight功能测试脚本

用于独立测试HearSight模块的功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_segment_merger():
    """测试段落合并功能"""
    print("=" * 60)
    print("测试1: 段落合并功能")
    print("=" * 60)

    from videotrans.hearsight.segment_merger import merge_srt_to_paragraphs

    # 需要提供一个SRT文件路径
    srt_path = input("请输入SRT文件路径: ").strip()

    if not os.path.exists(srt_path):
        print(f"❌ 文件不存在: {srt_path}")
        return False

    try:
        paragraphs = merge_srt_to_paragraphs(
            srt_path=srt_path,
            max_gap=2.0,
            max_duration=30.0,
            max_chars=200
        )

        print(f"\n✅ 段落合并成功！")
        print(f"原始字幕数: (需要解析SRT文件)")
        print(f"合并后段落数: {len(paragraphs)}")
        print(f"\n前3个段落预览：")

        for i, para in enumerate(paragraphs[:3], 1):
            start = para['start_time']
            end = para['end_time']
            text = para['text']
            print(f"\n段落 {i}:")
            print(f"  时间: {start:.2f}s - {end:.2f}s")
            print(f"  内容: {text[:100]}...")

        return True

    except Exception as e:
        print(f"❌ 段落合并失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_summarizer():
    """测试摘要生成功能"""
    print("\n" + "=" * 60)
    print("测试2: 摘要生成功能")
    print("=" * 60)

    from videotrans.hearsight.summarizer import generate_summary

    # 配置LLM
    print("\n请输入LLM API配置:")
    api_key = input("API Key: ").strip()
    base_url = input("Base URL (回车使用默认): ").strip() or "https://api.openai.com/v1"
    model = input("Model (回车使用默认): ").strip() or "gpt-3.5-turbo"

    if not api_key:
        print("❌ API Key不能为空")
        return False

    # 获取段落
    srt_path = input("\n请输入SRT文件路径: ").strip()

    if not os.path.exists(srt_path):
        print(f"❌ 文件不存在: {srt_path}")
        return False

    try:
        # 先合并段落
        from videotrans.hearsight.segment_merger import merge_srt_to_paragraphs

        print("\n⏳ 正在合并段落...")
        paragraphs = merge_srt_to_paragraphs(srt_path)
        print(f"✅ 合并完成，共 {len(paragraphs)} 个段落")

        # 生成摘要
        print("\n⏳ 正在生成摘要（可能需要1-2分钟）...")
        summary = generate_summary(
            paragraphs=paragraphs,
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        print(f"\n✅ 摘要生成成功！")
        print(f"\n主题: {summary['topic']}")
        print(f"\n总结:\n{summary['summary']}")
        print(f"\n统计:")
        print(f"  段落数: {summary['paragraph_count']}")
        print(f"  总时长: {summary['total_duration']:.1f}秒")

        return True

    except Exception as e:
        print(f"❌ 摘要生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui():
    """测试UI界面"""
    print("\n" + "=" * 60)
    print("测试3: UI界面")
    print("=" * 60)

    try:
        from PySide6.QtWidgets import QApplication
        from videotrans.ui.hearsight_config import HearSightConfigDialog
        from videotrans.ui.hearsight_viewer import SummaryViewerDialog

        app = QApplication(sys.argv)

        # 测试配置对话框
        print("\n测试配置对话框...")
        config_dialog = HearSightConfigDialog()
        config_dialog.show()

        print("✅ 配置对话框创建成功")
        print("请在对话框中进行配置，完成后关闭对话框...")

        result = config_dialog.exec()

        if result:
            print("✅ 配置已保存")
            cfg = config_dialog.get_config()
            print(f"LLM Model: {cfg['llm']['model']}")
        else:
            print("⚠️  配置未保存")

        # 测试查看器对话框
        print("\n测试查看器对话框...")

        # 创建示例数据
        summary = {
            "topic": "测试视频摘要",
            "summary": "这是一个测试摘要，用于演示HearSight功能。",
            "paragraph_count": 2,
            "total_duration": 60.0
        }

        paragraphs = [
            {
                "index": 1,
                "start_time": 0.0,
                "end_time": 30.0,
                "text": "这是第一段测试内容。"
            },
            {
                "index": 2,
                "start_time": 30.0,
                "end_time": 60.0,
                "text": "这是第二段测试内容。"
            }
        ]

        viewer = SummaryViewerDialog()
        viewer.set_data(summary, paragraphs)
        viewer.show()

        print("✅ 查看器对话框创建成功")
        print("请在对话框中查看结果，完成后关闭对话框...")

        viewer.exec()

        app.quit()

        return True

    except Exception as e:
        print(f"❌ UI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow():
    """测试完整流程"""
    print("\n" + "=" * 60)
    print("测试4: 完整工作流程")
    print("=" * 60)

    print("\n这个测试将执行完整的HearSight流程:")
    print("1. 读取SRT文件")
    print("2. 合并段落")
    print("3. 生成摘要")
    print("4. 显示结果")
    print("5. 导出Markdown")

    proceed = input("\n是否继续? (y/n): ").strip().lower()
    if proceed != 'y':
        print("已取消")
        return False

    try:
        from PySide6.QtWidgets import QApplication
        from videotrans.hearsight.processor import HearSightProcessor
        from videotrans.ui.hearsight_viewer import SummaryViewerDialog

        # 获取配置
        srt_path = input("\nSRT文件路径: ").strip()
        api_key = input("API Key: ").strip()
        base_url = input("Base URL (回车使用默认): ").strip() or "https://api.openai.com/v1"
        model = input("Model (回车使用默认): ").strip() or "gpt-3.5-turbo"

        if not os.path.exists(srt_path):
            print(f"❌ 文件不存在: {srt_path}")
            return False

        if not api_key:
            print("❌ API Key不能为空")
            return False

        # 创建Qt应用
        app = QApplication(sys.argv)

        # 配置
        llm_config = {
            'api_key': api_key,
            'base_url': base_url,
            'model': model,
            'temperature': 0.3,
            'timeout': 120
        }

        merge_config = {
            'max_gap': 2.0,
            'max_duration': 30.0,
            'max_chars': 200
        }

        # 创建处理器
        processor = HearSightProcessor(
            srt_path=srt_path,
            llm_config=llm_config,
            merge_config=merge_config
        )

        # 存储结果
        result_data = {}

        def on_progress(text, percent):
            print(f"[{percent}%] {text}")

        def on_finished(summary, paragraphs):
            result_data['summary'] = summary
            result_data['paragraphs'] = paragraphs
            print("\n✅ 处理完成！")

        def on_error(error):
            print(f"\n❌ 处理失败: {error}")
            result_data['error'] = error

        # 连接信号
        processor.progress_updated.connect(on_progress)
        processor.finished.connect(on_finished)
        processor.error_occurred.connect(on_error)

        # 开始处理
        print("\n⏳ 开始处理...")
        processor.start()

        # 等待完成
        processor.wait()

        # 检查结果
        if 'error' in result_data:
            return False

        if 'summary' not in result_data:
            print("❌ 未获取到结果")
            return False

        # 显示结果
        summary = result_data['summary']
        paragraphs = result_data['paragraphs']

        print(f"\n主题: {summary['topic']}")
        print(f"段落数: {len(paragraphs)}")

        # 显示UI
        viewer = SummaryViewerDialog()
        viewer.set_data(summary, paragraphs)
        viewer.exec()

        # 导出Markdown
        export = input("\n是否导出为Markdown? (y/n): ").strip().lower()
        if export == 'y':
            output_path = input("输出文件路径 (.md): ").strip()
            if output_path:
                from videotrans.hearsight.summarizer import export_summary_to_markdown
                export_summary_to_markdown(summary, paragraphs, output_path)
                print(f"✅ 已导出到: {output_path}")

        app.quit()

        return True

    except Exception as e:
        print(f"❌ 完整流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("HearSight 功能测试脚本")
    print("=" * 60)

    print("\n请选择测试项目:")
    print("1. 测试段落合并")
    print("2. 测试摘要生成")
    print("3. 测试UI界面")
    print("4. 测试完整流程")
    print("0. 退出")

    choice = input("\n请输入选项 (0-4): ").strip()

    if choice == '1':
        test_segment_merger()
    elif choice == '2':
        test_summarizer()
    elif choice == '3':
        test_ui()
    elif choice == '4':
        test_full_workflow()
    elif choice == '0':
        print("再见！")
        return
    else:
        print("❌ 无效选项")
        return

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
