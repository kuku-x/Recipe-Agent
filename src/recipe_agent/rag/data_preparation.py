"""
图数据库数据准备模块
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from neo4j import GraphDatabase
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

@dataclass
class GraphNode:
    """图节点数据结构"""
    node_id: str
    labels: List[str]
    name: str
    properties: Dict[str, Any]

@dataclass
class GraphRelation:
    """图关系数据结构"""
    start_node_id: str
    end_node_id: str
    relation_type: str
    properties: Dict[str, Any]

# ============== GraphIndexingModule (merged from graph_indexing.py) ==============

@dataclass
class EntityKeyValue:
    """实体键值对"""
    entity_name: str
    index_keys: List[str]  # 索引键列表
    value_content: str     # 详细描述内容
    entity_type: str       # 实体类型 (Recipe, Ingredient, CookingStep)
    metadata: Dict[str, Any]

@dataclass
class RelationKeyValue:
    """关系键值对"""
    relation_id: str
    index_keys: List[str]  # 多个索引键（可包含全局主题）
    value_content: str     # 关系描述内容
    relation_type: str     # 关系类型
    source_entity: str     # 源实体
    target_entity: str     # 目标实体
    metadata: Dict[str, Any]

class GraphIndexingModule:
    """
    图索引模块
    核心功能：
    1. 为实体创建键值对（名称作为唯一索引键）
    2. 为关系创建键值对（多个索引键，包含全局主题）
    3. 去重和优化图操作
    4. 支持增量更新
    """

    def __init__(self, config, llm_client):
        self.config = config
        self.llm_client = llm_client

        # 键值对存储
        self.entity_kv_store: Dict[str, EntityKeyValue] = {}
        self.relation_kv_store: Dict[str, RelationKeyValue] = {}

        # 索引映射：key -> entity/relation IDs
        self.key_to_entities: Dict[str, List[str]] = defaultdict(list)
        self.key_to_relations: Dict[str, List[str]] = defaultdict(list)

    def create_entity_key_values(self, recipes: List[Any], ingredients: List[Any],
                                cooking_steps: List[Any]) -> Dict[str, EntityKeyValue]:
        """
        为实体创建键值对结构
        每个实体使用其名称作为唯一索引键
        """
        logger.info("开始创建实体键值对...")

        # 处理菜谱实体
        for recipe in recipes:
            entity_id = recipe.node_id
            entity_name = recipe.name or f"菜谱_{entity_id}"

            # 构建详细内容
            content_parts = [f"菜品名称: {entity_name}"]

            if hasattr(recipe, 'properties'):
                props = recipe.properties
                if props.get('description'):
                    content_parts.append(f"描述: {props['description']}")
                if props.get('category'):
                    content_parts.append(f"分类: {props['category']}")
                if props.get('cuisineType'):
                    content_parts.append(f"菜系: {props['cuisineType']}")
                if props.get('difficulty'):
                    content_parts.append(f"难度: {props['difficulty']}")
                if props.get('cookingTime'):
                    content_parts.append(f"制作时间: {props['cookingTime']}")

            # 创建键值对
            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],  # 使用名称作为唯一索引键
                value_content='\n'.join(content_parts),
                entity_type="Recipe",
                metadata={
                    "node_id": entity_id,
                    "properties": getattr(recipe, 'properties', {})
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理食材实体
        for ingredient in ingredients:
            entity_id = ingredient.node_id
            entity_name = ingredient.name or f"食材_{entity_id}"

            content_parts = [f"食材名称: {entity_name}"]

            if hasattr(ingredient, 'properties'):
                props = ingredient.properties
                if props.get('category'):
                    content_parts.append(f"类别: {props['category']}")
                if props.get('nutrition'):
                    content_parts.append(f"营养信息: {props['nutrition']}")
                if props.get('storage'):
                    content_parts.append(f"储存方式: {props['storage']}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="Ingredient",
                metadata={
                    "node_id": entity_id,
                    "properties": getattr(ingredient, 'properties', {})
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        # 处理烹饪步骤实体
        for step in cooking_steps:
            entity_id = step.node_id
            entity_name = f"步骤_{entity_id}"

            content_parts = [f"烹饪步骤: {entity_name}"]

            if hasattr(step, 'properties'):
                props = step.properties
                if props.get('description'):
                    content_parts.append(f"步骤描述: {props['description']}")
                if props.get('order'):
                    content_parts.append(f"步骤顺序: {props['order']}")
                if props.get('technique'):
                    content_parts.append(f"技巧: {props['technique']}")
                if props.get('time'):
                    content_parts.append(f"时间: {props['time']}")

            entity_kv = EntityKeyValue(
                entity_name=entity_name,
                index_keys=[entity_name],
                value_content='\n'.join(content_parts),
                entity_type="CookingStep",
                metadata={
                    "node_id": entity_id,
                    "properties": getattr(step, 'properties', {})
                }
            )

            self.entity_kv_store[entity_id] = entity_kv
            self.key_to_entities[entity_name].append(entity_id)

        logger.info(f"实体键值对创建完成，共 {len(self.entity_kv_store)} 个实体")
        return self.entity_kv_store

    def create_relation_key_values(self, relationships: List[Tuple[str, str, str]]) -> Dict[str, RelationKeyValue]:
        """
        为关系创建键值对结构
        关系可能有多个索引键，包含从LLM增强的全局主题
        """
        logger.info("开始创建关系键值对...")

        for i, (source_id, relation_type, target_id) in enumerate(relationships):
            relation_id = f"rel_{i}_{source_id}_{target_id}"

            # 获取源实体和目标实体信息
            source_entity = self.entity_kv_store.get(source_id)
            target_entity = self.entity_kv_store.get(target_id)

            if not source_entity or not target_entity:
                continue

            # 构建关系描述
            content_parts = [
                f"关系类型: {relation_type}",
                f"源实体: {source_entity.entity_name} ({source_entity.entity_type})",
                f"目标实体: {target_entity.entity_name} ({target_entity.entity_type})"
            ]

            # 生成多个索引键（包含全局主题）
            index_keys = self._generate_relation_index_keys(
                source_entity, target_entity, relation_type
            )

            # 创建关系键值对
            relation_kv = RelationKeyValue(
                relation_id=relation_id,
                index_keys=index_keys,
                value_content='\n'.join(content_parts),
                relation_type=relation_type,
                source_entity=source_id,
                target_entity=target_id,
                metadata={
                    "source_name": source_entity.entity_name,
                    "target_name": target_entity.entity_name,
                    "created_from_graph": True
                }
            )

            self.relation_kv_store[relation_id] = relation_kv

            # 为每个索引键建立映射
            for key in index_keys:
                self.key_to_relations[key].append(relation_id)

        logger.info(f"关系键值对创建完成，共 {len(self.relation_kv_store)} 个关系")
        return self.relation_kv_store

    def _generate_relation_index_keys(self, source_entity: EntityKeyValue,
                                    target_entity: EntityKeyValue,
                                    relation_type: str) -> List[str]:
        """
        为关系生成多个索引键，包含全局主题
        """
        keys = [relation_type]  # 基础关系类型键

        # 根据关系类型和实体类型生成主题键
        if relation_type == "REQUIRES":
            # 菜谱-食材关系的主题键
            keys.extend([
                "食材搭配",
                "烹饪原料",
                f"{source_entity.entity_name}_食材",
                target_entity.entity_name
            ])
        elif relation_type == "HAS_STEP":
            # 菜谱-步骤关系的主题键
            keys.extend([
                "制作步骤",
                "烹饪过程",
                f"{source_entity.entity_name}_步骤",
                "制作方法"
            ])
        elif relation_type == "BELONGS_TO_CATEGORY":
            # 分类关系的主题键
            keys.extend([
                "菜品分类",
                "美食类别",
                target_entity.entity_name
            ])

        # 使用LLM增强关系索引键（可选）
        if getattr(self.config, 'enable_llm_relation_keys', False):
            enhanced_keys = self._llm_enhance_relation_keys(source_entity, target_entity, relation_type)
            keys.extend(enhanced_keys)

        # 去重并返回
        return list(set(keys))

    def _llm_enhance_relation_keys(self, source_entity: EntityKeyValue,
                                 target_entity: EntityKeyValue,
                                 relation_type: str) -> List[str]:
        """
        使用LLM增强关系索引键，生成全局主题
        """
        prompt = f"""
        分析以下实体关系，生成相关的主题关键词：

        源实体: {source_entity.entity_name} ({source_entity.entity_type})
        目标实体: {target_entity.entity_name} ({target_entity.entity_type})
        关系类型: {relation_type}

        请生成3-5个相关的主题关键词，用于索引和检索。
        返回JSON格式：{{"keywords": ["关键词1", "关键词2", "关键词3"]}}
        """

        try:
            response = self.llm_client.chat.completions.create(
                model=self.config.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )

            result = json.loads(response.choices[0].message.content.strip())
            return result.get("keywords", [])

        except Exception as e:
            logger.error(f"LLM增强关系索引键失败: {e}")
            return []

    def deduplicate_entities_and_relations(self):
        """
        去重相同的实体和关系，优化图操作
        """
        logger.info("开始去重实体和关系...")

        # 实体去重：基于名称
        name_to_entities = defaultdict(list)
        for entity_id, entity_kv in self.entity_kv_store.items():
            name_to_entities[entity_kv.entity_name].append(entity_id)

        # 合并重复实体
        entities_to_remove = []
        for name, entity_ids in name_to_entities.items():
            if len(entity_ids) > 1:
                # 保留第一个，合并其他的内容
                primary_id = entity_ids[0]
                primary_entity = self.entity_kv_store[primary_id]

                for entity_id in entity_ids[1:]:
                    duplicate_entity = self.entity_kv_store[entity_id]
                    # 合并内容
                    primary_entity.value_content += f"\n\n补充信息: {duplicate_entity.value_content}"
                    # 标记删除
                    entities_to_remove.append(entity_id)

        # 删除重复实体
        for entity_id in entities_to_remove:
            del self.entity_kv_store[entity_id]

        # 关系去重：基于源-目标-类型
        relation_signature_to_ids = defaultdict(list)
        for relation_id, relation_kv in self.relation_kv_store.items():
            signature = f"{relation_kv.source_entity}_{relation_kv.target_entity}_{relation_kv.relation_type}"
            relation_signature_to_ids[signature].append(relation_id)

        # 合并重复关系
        relations_to_remove = []
        for signature, relation_ids in relation_signature_to_ids.items():
            if len(relation_ids) > 1:
                # 保留第一个，删除其他
                for relation_id in relation_ids[1:]:
                    relations_to_remove.append(relation_id)

        # 删除重复关系
        for relation_id in relations_to_remove:
            del self.relation_kv_store[relation_id]

        # 重建索引映射
        self._rebuild_key_mappings()

        logger.info(f"去重完成 - 删除了 {len(entities_to_remove)} 个重复实体，{len(relations_to_remove)} 个重复关系")

    def _rebuild_key_mappings(self):
        """重建键到实体/关系的映射"""
        self.key_to_entities.clear()
        self.key_to_relations.clear()

        # 重建实体映射
        for entity_id, entity_kv in self.entity_kv_store.items():
            for key in entity_kv.index_keys:
                self.key_to_entities[key].append(entity_id)

        # 重建关系映射
        for relation_id, relation_kv in self.relation_kv_store.items():
            for key in relation_kv.index_keys:
                self.key_to_relations[key].append(relation_id)

    def get_entities_by_key(self, key: str) -> List[EntityKeyValue]:
        """根据索引键获取实体"""
        entity_ids = self.key_to_entities.get(key, [])
        return [self.entity_kv_store[eid] for eid in entity_ids if eid in self.entity_kv_store]

    def get_relations_by_key(self, key: str) -> List[RelationKeyValue]:
        """根据索引键获取关系"""
        relation_ids = self.key_to_relations.get(key, [])
        return [self.relation_kv_store[rid] for rid in relation_ids if rid in self.relation_kv_store]

    def get_statistics(self) -> Dict[str, Any]:
        """获取键值对存储统计信息"""
        return {
            "total_entities": len(self.entity_kv_store),
            "total_relations": len(self.relation_kv_store),
            "total_entity_keys": sum(len(kv.index_keys) for kv in self.entity_kv_store.values()),
            "total_relation_keys": sum(len(kv.index_keys) for kv in self.relation_kv_store.values()),
            "entity_types": {
                "Recipe": len([kv for kv in self.entity_kv_store.values() if kv.entity_type == "Recipe"]),
                "Ingredient": len([kv for kv in self.entity_kv_store.values() if kv.entity_type == "Ingredient"]),
                "CookingStep": len([kv for kv in self.entity_kv_store.values() if kv.entity_type == "CookingStep"])
            }
        }


# ============== GraphDataPreparationModule ==============

class GraphDataPreparationModule:
    """图数据库数据准备模块 - 从Neo4j读取数据并转换为文档"""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        初始化图数据库连接

        Args:
            uri: Neo4j连接URI
            user: 用户名
            password: 密码
            database: 数据库名称
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        self.documents: List[Document] = []
        self.chunks: List[Document] = []
        self.recipes: List[GraphNode] = []
        self.ingredients: List[GraphNode] = []
        self.cooking_steps: List[GraphNode] = []

        self._connect()

    def _connect(self):
        """建立Neo4j连接"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                database=self.database
            )
            logger.info(f"已连接到Neo4j数据库: {self.uri}")

            # 测试连接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_result = result.single()
                if test_result:
                    logger.info("Neo4j连接测试成功")

        except Exception as e:
            logger.error(f"连接Neo4j失败: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()
            logger.info("Neo4j连接已关闭")

    def load_graph_data(self) -> Dict[str, Any]:
        """
        从Neo4j加载图数据

        Returns:
            包含节点和关系的数据字典
        """
        logger.info("正在从Neo4j加载图数据...")

        with self.driver.session() as session:
            # 加载所有菜谱节点，从Category关系中读取分类信息
            recipes_query = """
            MATCH (r:Recipe)
            WHERE r.nodeId >= '200000000'
            OPTIONAL MATCH (r)-[:BELONGS_TO_CATEGORY]->(c:Category)
            WITH r, collect(c.name) as categories
            RETURN r.nodeId as nodeId, labels(r) as labels, r.name as name,
                   properties(r) as originalProperties,
                   CASE WHEN size(categories) > 0
                        THEN categories[0]
                        ELSE COALESCE(r.category, '未知') END as mainCategory,
                   CASE WHEN size(categories) > 0
                        THEN categories
                        ELSE [COALESCE(r.category, '未知')] END as allCategories
            ORDER BY r.nodeId
            """

            result = session.run(recipes_query)
            self.recipes = []
            for record in result:
                # 合并原始属性和新的分类信息
                properties = dict(record["originalProperties"])
                properties["category"] = record["mainCategory"]
                properties["all_categories"] = record["allCategories"]

                node = GraphNode(
                    node_id=record["nodeId"],
                    labels=record["labels"],
                    name=record["name"],
                    properties=properties
                )
                self.recipes.append(node)

            logger.info(f"加载了 {len(self.recipes)} 个菜谱节点")

            # 加载所有食材节点
            ingredients_query = """
            MATCH (i:Ingredient)
            WHERE i.nodeId >= '200000000'
            RETURN i.nodeId as nodeId, labels(i) as labels, i.name as name,
                   properties(i) as properties
            ORDER BY i.nodeId
            """

            result = session.run(ingredients_query)
            self.ingredients = []
            for record in result:
                node = GraphNode(
                    node_id=record["nodeId"],
                    labels=record["labels"],
                    name=record["name"],
                    properties=record["properties"]
                )
                self.ingredients.append(node)

            logger.info(f"加载了 {len(self.ingredients)} 个食材节点")

            # 加载所有烹饪步骤节点
            steps_query = """
            MATCH (s:CookingStep)
            WHERE s.nodeId >= '200000000'
            RETURN s.nodeId as nodeId, labels(s) as labels, s.name as name,
                   properties(s) as properties
            ORDER BY s.nodeId
            """

            result = session.run(steps_query)
            self.cooking_steps = []
            for record in result:
                node = GraphNode(
                    node_id=record["nodeId"],
                    labels=record["labels"],
                    name=record["name"],
                    properties=record["properties"]
                )
                self.cooking_steps.append(node)

            logger.info(f"加载了 {len(self.cooking_steps)} 个烹饪步骤节点")

        return {
            'recipes': len(self.recipes),
            'ingredients': len(self.ingredients),
            'cooking_steps': len(self.cooking_steps)
        }

    def build_recipe_documents(self) -> List[Document]:
        """
        构建菜谱文档，集成相关的食材和步骤信息

        Returns:
            结构化的菜谱文档列表
        """
        logger.info("正在构建菜谱文档...")

        documents = []

        with self.driver.session() as session:
            for recipe in self.recipes:
                try:
                    recipe_id = recipe.node_id
                    recipe_name = recipe.name

                    # 获取菜谱的相关食材
                    ingredients_query = """
                    MATCH (r:Recipe {nodeId: $recipe_id})-[req:REQUIRES]->(i:Ingredient)
                    RETURN i.name as name, i.category as category,
                           req.amount as amount, req.unit as unit,
                           i.description as description
                    ORDER BY i.name
                    """

                    ingredients_result = session.run(ingredients_query, {"recipe_id": recipe_id})
                    ingredients_info = []
                    for ing_record in ingredients_result:
                        amount = ing_record.get("amount", "")
                        unit = ing_record.get("unit", "")
                        ingredient_text = f"{ing_record['name']}"
                        if amount and unit:
                            ingredient_text += f"({amount}{unit})"
                        if ing_record.get("description"):
                            ingredient_text += f" - {ing_record['description']}"
                        ingredients_info.append(ingredient_text)

                    # 获取菜谱的烹饪步骤
                    steps_query = """
                    MATCH (r:Recipe {nodeId: $recipe_id})-[c:CONTAINS_STEP]->(s:CookingStep)
                    RETURN s.name as name, s.description as description,
                           s.stepNumber as stepNumber, s.methods as methods,
                           s.tools as tools, s.timeEstimate as timeEstimate,
                           c.stepOrder as stepOrder
                    ORDER BY COALESCE(c.stepOrder, s.stepNumber, 999)
                    """

                    steps_result = session.run(steps_query, {"recipe_id": recipe_id})
                    steps_info = []
                    for step_record in steps_result:
                        step_text = f"步骤: {step_record['name']}"
                        if step_record.get("description"):
                            step_text += f"\n描述: {step_record['description']}"
                        if step_record.get("methods"):
                            step_text += f"\n方法: {step_record['methods']}"
                        if step_record.get("tools"):
                            step_text += f"\n工具: {step_record['tools']}"
                        if step_record.get("timeEstimate"):
                            step_text += f"\n时间: {step_record['timeEstimate']}"
                        steps_info.append(step_text)

                    # 构建完整的菜谱文档内容
                    content_parts = [f"# {recipe_name}"]

                    # 添加菜谱基本信息
                    if recipe.properties.get("description"):
                        content_parts.append(f"\n## 菜品描述\n{recipe.properties['description']}")

                    if recipe.properties.get("cuisineType"):
                        content_parts.append(f"\n菜系: {recipe.properties['cuisineType']}")

                    if recipe.properties.get("difficulty"):
                        content_parts.append(f"难度: {recipe.properties['difficulty']}星")

                    if recipe.properties.get("prepTime") or recipe.properties.get("cookTime"):
                        time_info = []
                        if recipe.properties.get("prepTime"):
                            time_info.append(f"准备时间: {recipe.properties['prepTime']}")
                        if recipe.properties.get("cookTime"):
                            time_info.append(f"烹饪时间: {recipe.properties['cookTime']}")
                        content_parts.append(f"\n时间信息: {', '.join(time_info)}")

                    if recipe.properties.get("servings"):
                        content_parts.append(f"份量: {recipe.properties['servings']}")

                    # 添加食材信息
                    if ingredients_info:
                        content_parts.append("\n## 所需食材")
                        for i, ingredient in enumerate(ingredients_info, 1):
                            content_parts.append(f"{i}. {ingredient}")

                    # 添加步骤信息
                    if steps_info:
                        content_parts.append("\n## 制作步骤")
                        for i, step in enumerate(steps_info, 1):
                            content_parts.append(f"\n### 第{i}步\n{step}")

                    # 添加标签信息
                    if recipe.properties.get("tags"):
                        content_parts.append(f"\n## 标签\n{recipe.properties['tags']}")

                    # 组合成最终内容
                    full_content = "\n".join(content_parts)

                    # 创建文档对象
                    doc = Document(
                        page_content=full_content,
                        metadata={
                            "node_id": recipe_id,
                            "recipe_name": recipe_name,
                            "node_type": "Recipe",
                            "category": recipe.properties.get("category", "未知"),
                            "cuisine_type": recipe.properties.get("cuisineType", "未知"),
                            "difficulty": recipe.properties.get("difficulty", 0),
                            "prep_time": recipe.properties.get("prepTime", ""),
                            "cook_time": recipe.properties.get("cookTime", ""),
                            "servings": recipe.properties.get("servings", ""),
                            "ingredients_count": len(ingredients_info),
                            "steps_count": len(steps_info),
                            "doc_type": "recipe",
                            "content_length": len(full_content)
                        }
                    )

                    documents.append(doc)

                except Exception as e:
                    logger.warning(f"构建菜谱文档失败 {recipe_name} (ID: {recipe_id}): {e}")
                    continue

        self.documents = documents
        logger.info(f"成功构建 {len(documents)} 个菜谱文档")
        return documents

    def chunk_documents(self, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Document]:
        """
        对文档进行分块处理

        Args:
            chunk_size: 分块大小
            chunk_overlap: 重叠大小

        Returns:
            分块后的文档列表
        """
        logger.info(f"正在进行文档分块，块大小: {chunk_size}, 重叠: {chunk_overlap}")

        if not self.documents:
            raise ValueError("请先构建文档")

        chunks = []
        chunk_id = 0

        for doc in self.documents:
            content = doc.page_content

            # 简单的按长度分块
            if len(content) <= chunk_size:
                # 内容较短，不需要分块
                chunk = Document(
                    page_content=content,
                    metadata={
                        **doc.metadata,
                        "chunk_id": f"{doc.metadata['node_id']}_chunk_{chunk_id}",
                        "parent_id": doc.metadata["node_id"],
                        "chunk_index": 0,
                        "total_chunks": 1,
                        "chunk_size": len(content),
                        "doc_type": "chunk"
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
            else:
                # 按章节分块（基于标题）
                sections = content.split('\n## ')
                if len(sections) <= 1:
                    # 没有二级标题，按长度强制分块
                    total_chunks = (len(content) - 1) // (chunk_size - chunk_overlap) + 1

                    for i in range(total_chunks):
                        start = i * (chunk_size - chunk_overlap)
                        end = min(start + chunk_size, len(content))

                        chunk_content = content[start:end]

                        chunk = Document(
                            page_content=chunk_content,
                            metadata={
                                **doc.metadata,
                                "chunk_id": f"{doc.metadata['node_id']}_chunk_{chunk_id}",
                                "parent_id": doc.metadata["node_id"],
                                "chunk_index": i,
                                "total_chunks": total_chunks,
                                "chunk_size": len(chunk_content),
                                "doc_type": "chunk"
                            }
                        )
                        chunks.append(chunk)
                        chunk_id += 1
                else:
                    # 按章节分块
                    total_chunks = len(sections)
                    for i, section in enumerate(sections):
                        if i == 0:
                            # 第一个部分包含标题
                            chunk_content = section
                        else:
                            # 其他部分添加章节标题
                            chunk_content = f"## {section}"

                        chunk = Document(
                            page_content=chunk_content,
                            metadata={
                                **doc.metadata,
                                "chunk_id": f"{doc.metadata['node_id']}_chunk_{chunk_id}",
                                "parent_id": doc.metadata["node_id"],
                                "chunk_index": i,
                                "total_chunks": total_chunks,
                                "chunk_size": len(chunk_content),
                                "doc_type": "chunk",
                                "section_title": section.split('\n')[0] if i > 0 else "主标题"
                            }
                        )
                        chunks.append(chunk)
                        chunk_id += 1

        self.chunks = chunks
        logger.info(f"文档分块完成，共生成 {len(chunks)} 个块")
        return chunks



    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息

        Returns:
            统计信息字典
        """
        stats = {
            'total_recipes': len(self.recipes),
            'total_ingredients': len(self.ingredients),
            'total_cooking_steps': len(self.cooking_steps),
            'total_documents': len(self.documents),
            'total_chunks': len(self.chunks)
        }

        if self.documents:
            # 分类统计
            categories = {}
            cuisines = {}
            difficulties = {}

            for doc in self.documents:
                category = doc.metadata.get('category', '未知')
                categories[category] = categories.get(category, 0) + 1

                cuisine = doc.metadata.get('cuisine_type', '未知')
                cuisines[cuisine] = cuisines.get(cuisine, 0) + 1

                difficulty = doc.metadata.get('difficulty', 0)
                difficulties[str(difficulty)] = difficulties.get(str(difficulty), 0) + 1

            stats.update({
                'categories': categories,
                'cuisines': cuisines,
                'difficulties': difficulties,
                'avg_content_length': sum(doc.metadata.get('content_length', 0) for doc in self.documents) / len(self.documents),
                'avg_chunk_size': sum(chunk.metadata.get('chunk_size', 0) for chunk in self.chunks) / len(self.chunks) if self.chunks else 0
            })

        return stats



    def __del__(self):
        """析构函数，确保关闭连接"""
        self.close()