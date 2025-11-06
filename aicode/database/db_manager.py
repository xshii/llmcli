"""
SQLite数据库管理器
"""
import sqlite3
import os
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from aicode.models.schema import (
    ModelSchema,
    CREATE_MODELS_TABLE,
    row_to_model
)
from aicode.utils.validators import validate_model_data
from aicode.llm.exceptions import (
    DatabaseError,
    ModelNotFoundError,
    ModelAlreadyExistsError
)
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """SQLite数据库管理器"""

    def __init__(self, db_path: str):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = os.path.expanduser(db_path)
        self._ensure_db_directory()
        self._init_database()
        logger.info(f"Database initialized at {self.db_path}")

    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.debug(f"Created database directory: {db_dir}")

    def _init_database(self):
        """初始化数据库表"""
        try:
            with self.get_connection() as conn:
                conn.execute(CREATE_MODELS_TABLE)
                conn.commit()
                logger.debug("Database tables initialized")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接（上下文管理器）

        Yields:
            sqlite3.Connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Database connection error: {e}")
        finally:
            if conn:
                conn.close()

    def insert_model(self, model: ModelSchema) -> None:
        """
        插入模型

        Args:
            model: ModelSchema实例

        Raises:
            ModelAlreadyExistsError: 模型已存在
            DatabaseError: 数据库错误
        """
        # 检查是否已存在
        if self.model_exists(model.name):
            raise ModelAlreadyExistsError(f"Model '{model.name}' already exists")

        try:
            data = model.to_dict()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            sql = f"INSERT INTO models ({columns}) VALUES ({placeholders})"

            with self.get_connection() as conn:
                conn.execute(sql, list(data.values()))
                conn.commit()
                logger.info(f"Inserted model: {model.name}")
        except sqlite3.Error as e:
            logger.error(f"Failed to insert model {model.name}: {e}")
            raise DatabaseError(f"Failed to insert model: {e}")

    def update_model(self, model_name: str, updates: Dict[str, Any]) -> None:
        """
        更新模型

        Args:
            model_name: 模型名称
            updates: 要更新的字段字典

        Raises:
            ModelNotFoundError: 模型不存在
            DatabaseError: 数据库错误
        """
        if not self.model_exists(model_name):
            raise ModelNotFoundError(f"Model '{model_name}' not found")

        if not updates:
            return

        try:
            # 验证更新数据（部分验证）
            # 获取现有模型数据并合并
            existing = self.get_model(model_name)
            merged_data = existing.to_dict()
            merged_data.update(updates)
            validate_model_data(merged_data)

            set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
            sql = f"UPDATE models SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE name = ?"

            with self.get_connection() as conn:
                conn.execute(sql, list(updates.values()) + [model_name])
                conn.commit()
                logger.info(f"Updated model: {model_name}")
        except sqlite3.Error as e:
            logger.error(f"Failed to update model {model_name}: {e}")
            raise DatabaseError(f"Failed to update model: {e}")

    def get_model(self, model_name: str) -> ModelSchema:
        """
        获取模型

        Args:
            model_name: 模型名称

        Returns:
            ModelSchema实例

        Raises:
            ModelNotFoundError: 模型不存在
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM models WHERE name = ?",
                    (model_name,)
                )
                row = cursor.fetchone()

                if row is None:
                    raise ModelNotFoundError(f"Model '{model_name}' not found")

                return row_to_model(row)
        except ModelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get model {model_name}: {e}")
            raise DatabaseError(f"Failed to get model: {e}")

    def delete_model(self, model_name: str) -> None:
        """
        删除模型

        Args:
            model_name: 模型名称

        Raises:
            ModelNotFoundError: 模型不存在
        """
        if not self.model_exists(model_name):
            raise ModelNotFoundError(f"Model '{model_name}' not found")

        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM models WHERE name = ?", (model_name,))
                conn.commit()
                logger.info(f"Deleted model: {model_name}")
        except sqlite3.Error as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            raise DatabaseError(f"Failed to delete model: {e}")

    def model_exists(self, model_name: str) -> bool:
        """
        检查模型是否存在

        Args:
            model_name: 模型名称

        Returns:
            bool: 存在返回True
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM models WHERE name = ?",
                    (model_name,)
                )
                count = cursor.fetchone()[0]
                return count > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to check model existence: {e}")
            raise DatabaseError(f"Failed to check model existence: {e}")

    def list_models(self) -> List[ModelSchema]:
        """
        列出所有模型

        Returns:
            List[ModelSchema]: 模型列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM models ORDER BY name")
                rows = cursor.fetchall()
                return [row_to_model(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise DatabaseError(f"Failed to list models: {e}")

    def query_models(self, filters: Optional[Dict[str, Any]] = None) -> List[ModelSchema]:
        """
        查询模型（支持筛选）

        Args:
            filters: 筛选条件字典
                - provider: 提供商
                - min_code_score: 最小代码评分
                - specialty: 专长（包含检查）

        Returns:
            List[ModelSchema]: 符合条件的模型列表
        """
        try:
            conditions = []
            params = []

            if filters:
                if 'provider' in filters:
                    conditions.append("provider = ?")
                    params.append(filters['provider'])

                if 'min_code_score' in filters:
                    conditions.append("code_score >= ?")
                    params.append(filters['min_code_score'])

                if 'specialty' in filters:
                    # SQLite的LIKE查询
                    conditions.append(
                        "(specialties LIKE ? OR specialties LIKE ? OR specialties LIKE ?)"
                    )
                    specialty = filters['specialty']
                    params.extend([
                        f"{specialty},%",  # 开头
                        f"%,{specialty},%",  # 中间
                        f"%,{specialty}"  # 结尾
                    ])

            sql = "SELECT * FROM models"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY name"

            with self.get_connection() as conn:
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                return [row_to_model(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to query models: {e}")
            raise DatabaseError(f"Failed to query models: {e}")

    def import_batch(self, models: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量导入模型

        Args:
            models: 模型数据字典列表

        Returns:
            Dict[str, int]: 统计信息 {'imported': N, 'skipped': M, 'errors': K}
        """
        stats = {'imported': 0, 'skipped': 0, 'errors': 0}

        for model_data in models:
            try:
                # 验证数据
                validated = validate_model_data(model_data)
                model = ModelSchema.from_dict(validated)

                # 检查是否已存在
                if self.model_exists(model.name):
                    logger.debug(f"Model {model.name} already exists, skipping")
                    stats['skipped'] += 1
                    continue

                # 插入
                self.insert_model(model)
                stats['imported'] += 1

            except Exception as e:
                logger.error(f"Failed to import model: {e}")
                stats['errors'] += 1

        logger.info(
            f"Batch import completed: {stats['imported']} imported, "
            f"{stats['skipped']} skipped, {stats['errors']} errors"
        )
        return stats

    def export_all(self) -> List[Dict[str, Any]]:
        """
        导出所有模型为字典列表

        Returns:
            List[Dict[str, Any]]: 模型数据列表
        """
        models = self.list_models()
        return [model.to_dict() for model in models]

    def count_models(self) -> int:
        """
        统计模型数量

        Returns:
            int: 模型总数
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM models")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Failed to count models: {e}")
            raise DatabaseError(f"Failed to count models: {e}")
