import os
import sys
import asyncio
import logging

# 将 LightRAG 源码目录添加到路径中，以便可以导入
sys.path.append(r"e:\代码发布区\LightRAG")

try:
    from lightrag.llm.openai import openai_complete
    from lightrag.utils import logger
except ImportError as e:
    print(f"❌ 导入 LightRAG 失败: {e}")
    print("请确认 LightRAG 目录路径是否正确。")
    sys.exit(1)

# 设置日志级别以便观察输出
logger.setLevel(logging.INFO)

# 模拟 LightRAG 的配置对象
class MockConfig:
    def __init__(self):
        self.global_config = {"llm_model_name": "gpt-3.5-turbo"}

async def main():
    print("=" * 50)
    print("Langfuse 集成验证脚本")
    print("=" * 50)

    # 1. 检查环境变量
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    print(f"检查环境变量配置:")
    print(f"- LANGFUSE_PUBLIC_KEY: {'✅ 已设置' if pk else '❌ 未设置'}")
    print(f"- LANGFUSE_SECRET_KEY: {'✅ 已设置' if sk else '❌ 未设置'}")
    print(f"- LANGFUSE_HOST:       {host}")
    
    if not pk or not sk:
        print("\n⚠️  错误: 请先设置环境变量 LANGFUSE_PUBLIC_KEY 和 LANGFUSE_SECRET_KEY")
        return

    # 2. 检查 OpenAI Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️  错误: 未找到 OPENAI_API_KEY，无法发起 LLM 请求")
        return

    print("\n正在发起测试请求...")
    try:
        # 3. 调用 LightRAG 的 LLM 接口
        # 注意：这里我们模拟了一个 LightRAG 内部调用，直接触发 openai_complete
        response = await openai_complete(
            prompt="Hello! Please reply with 'Langfuse check passed' if you can confirm.",
            hashing_kv=MockConfig()
        )
        
        print(f"\n✅ LLM 响应成功:\n{response}")
        print("\n🎉 验证完成！")
        print(f"请登录 Langfuse 仪表盘 ({host}) 查看名为 'gpt-3.5-turbo' 的 Trace。")
        
    except ImportError:
        print("\n❌ 错误: 似乎没有安装 langfuse 库。请运行 `pip install langfuse`。")
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
