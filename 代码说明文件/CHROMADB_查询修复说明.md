# ChromaDB 查询修复说明

## 问题描述

用户报告了两个错误：

### 错误1: CSS警告
```
Unknown property box-shadow
```

### 错误2: ChromaDB查询错误
```
❌ 获取摘要失败: Expected where to have exactly one operator, 
got {'video_id': '91f34c2566525aa7de9dbff096d81c9d', 'type': 'paragraph'} in get.
```

## 问题分析

### 问题1: box-shadow CSS属性

**原因**: Qt的QSS（Qt Style Sheets）不支持CSS3的`box-shadow`属性。

**影响**: 
- 不影响功能，只是产生警告信息
- 按钮样式仍然正常显示，只是没有阴影效果

**位置**: `videotrans/mainwin/_main_win.py` 中的按钮样式定义

### 问题2: ChromaDB多条件查询

**原因**: ChromaDB的`where`查询语法要求多个条件必须使用操作符（如`$and`、`$or`）组合。

**错误的写法**:
```python
where = {
    "video_id": video_id,
    "type": "paragraph"
}
```

**正确的写法**:
```python
where = {
    "$and": [
        {"video_id": video_id},
        {"type": "paragraph"}
    ]
}
```

**影响**: 
- 无法获取视频的段落摘要
- 多条件搜索失败
- 摘要管理器无法正常显示视频详情

## 修复方案

### 修复1: 移除不支持的CSS属性

**文件**: `videotrans/mainwin/_main_win.py`

**修改位置**: 
- 第834行: `hearsight_btn` 的hover样式
- 第860行: `hearsight_config_btn` 的hover样式
- 第886行: `summary_manager_btn` 的hover样式

**修改内容**: 移除所有`box-shadow`属性

**修改前**:
```python
QPushButton:hover {
    background: qlineargradient(...);
    box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);  # 移除这行
}
```

**修改后**:
```python
QPushButton:hover {
    background: qlineargradient(...);
}
```

### 修复2: 修复ChromaDB查询语法

**文件**: `videotrans/hearsight/vector_store.py`

#### 修复2.1: get_video_summary方法

**位置**: 第293-301行

**修改前**:
```python
paragraphs = self.collection.get(
    where={
        "video_id": video_id,
        "type": "paragraph"
    }
)
```

**修改后**:
```python
paragraphs = self.collection.get(
    where={
        "$and": [
            {"video_id": video_id},
            {"type": "paragraph"}
        ]
    }
)
```

#### 修复2.2: search方法

**位置**: 第201-221行

**修改前**:
```python
where = {}
if video_id:
    where["video_id"] = video_id
if filter_type:
    where["type"] = filter_type

results = self.collection.query(
    query_texts=[query],
    n_results=n_results,
    where=where if where else None
)
```

**修改后**:
```python
where = None
conditions = []
if video_id:
    conditions.append({"video_id": video_id})
if filter_type:
    conditions.append({"type": filter_type})

# 如果有多个条件，使用$and操作符
if len(conditions) > 1:
    where = {"$and": conditions}
elif len(conditions) == 1:
    where = conditions[0]

results = self.collection.query(
    query_texts=[query],
    n_results=n_results,
    where=where
)
```

**改进点**:
- 正确处理单条件查询（不需要操作符）
- 正确处理多条件查询（使用`$and`操作符）
- 正确处理无条件查询（`where=None`）

## 测试验证

### 测试工具

创建了两个测试脚本：

1. **`create_test_summary.py`** - 创建测试数据
   ```bash
   python create_test_summary.py
   ```

2. **`test_chromadb_fix.py`** - 验证修复
   ```bash
   python test_chromadb_fix.py
   ```

### 测试结果

```
测试1: 列出所有视频
✅ 找到 2 个视频

测试2: 获取视频摘要（测试多条件where查询）
✅ 成功获取视频摘要
   整体摘要: 雌激素及其与肝脏的关系
   段落数量: 4
   第一个段落: 0.00s - 18.33s

测试3: 搜索功能
   3.1 无过滤条件的搜索 ✅
   3.2 单条件搜索（video_id） ✅
   3.3 单条件搜索（type） ✅
   3.4 多条件搜索（video_id + type） ✅

🎉 所有测试通过！
```

## 影响范围

### 修改的文件
1. `videotrans/mainwin/_main_win.py` - 移除box-shadow CSS属性
2. `videotrans/hearsight/vector_store.py` - 修复ChromaDB查询语法

### 影响的功能
1. **摘要管理器** - 现在可以正确显示视频的段落摘要
2. **语义搜索** - 多条件搜索现在可以正常工作
3. **按钮样式** - 移除了不支持的阴影效果（视觉上的微小变化）

### 不影响的功能
- 摘要生成功能
- 摘要存储功能
- 其他UI组件
- 视频处理流程

## ChromaDB查询语法参考

### 单条件查询
```python
where = {"field": "value"}
```

### 多条件AND查询
```python
where = {
    "$and": [
        {"field1": "value1"},
        {"field2": "value2"}
    ]
}
```

### 多条件OR查询
```python
where = {
    "$or": [
        {"field1": "value1"},
        {"field2": "value2"}
    ]
}
```

### 复杂查询
```python
where = {
    "$and": [
        {"field1": "value1"},
        {
            "$or": [
                {"field2": "value2"},
                {"field3": "value3"}
            ]
        }
    ]
}
```

## 后续建议

1. **代码审查**: 检查其他地方是否有类似的多条件查询问题
2. **单元测试**: 为vector_store模块添加完整的单元测试
3. **文档更新**: 更新开发文档，说明ChromaDB查询的正确用法
4. **错误处理**: 增强错误处理，提供更友好的错误信息

## 总结

**问题**: ChromaDB多条件查询语法错误 + CSS不支持的属性

**解决**: 
1. 使用`$and`操作符组合多个查询条件
2. 移除QSS不支持的`box-shadow`属性

**验证**: 通过测试脚本验证所有查询场景

**影响**: 最小化，只修复了查询逻辑和样式定义

现在摘要管理器可以正常工作了！

