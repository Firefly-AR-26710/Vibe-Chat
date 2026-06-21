import logging
from database import engine
import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("开始创建数据库表...")
    try:
        # 这一步会根据 models.py 中的定义，自动在 MySQL 中创建不存在的表
        models.Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功！")
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")

if __name__ == "__main__":
    init_db()
