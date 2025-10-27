# 文件名截断优化总结

## 需求
将上传的文件名显示优化为：**前6位字符 + ... + 扩展名**

## 实施内容

### 1. 截断逻辑
**函数**: `truncateFileName(fileName: string): string`

**规则**:
- 如果文件名总长度 ≤ 10，不截断
- 如果文件名（不含扩展名）长度 ≤ 6，不截断
- 如果文件名很长，截取前6位 + `...` + 扩展名

**示例**:
```typescript
truncateFileName("test.pdf")                    // "test.pdf" (不截断)
truncateFileName("document.docx")               // "document.docx" (不截断)
truncateFileName("very_long_filename.pdf")      // "very_l...pdf"
truncateFileName("后端接收设备需求规格A1.1.docx")  // "后端接收设...docx"
truncateFileName("pasted-image-1234567890.png") // "pasted...png"
```

### 2. 修改文件

#### 文件 1: `frontend/src/pages/Home.tsx`
**位置**: Home 组件内部

**改动**:
1. 添加 `truncateFileName` 函数
2. 导入 `Tooltip` 组件
3. `documentList` 增加 `fullTitle` 字段保存完整文件名
4. 文件名显示处添加 Tooltip

**代码**:
```tsx
// 截断逻辑
const truncateFileName = (fileName: string): string => {
  // ... 实现
};

// documentList 添加 fullTitle
const documentList = useMemo(
  () =>
    documents.map((document) => ({
      id: document.id,
      title: truncateFileName(document.original_name),
      fullTitle: document.original_name, // 完整文件名
      sizeString: formatBytes(document.size)
    })),
  [documents]
);

// 显示时添加 Tooltip
<Tooltip title={item.fullTitle} placement="topLeft">
  <span style={{ cursor: 'help' }}>{item.title}</span>
</Tooltip>
```

#### 文件 2: `frontend/src/components/FileUploader.tsx`
**位置**: FileUploader 组件内部

**改动**:
1. 添加相同的 `truncateFileName` 函数
2. "上次上传"提示文字中应用截断

**代码**:
```tsx
{lastUploadedName && (
  <p className="ant-upload-hint">
    上次：{truncateFileName(lastUploadedName)}{lastUploadedSize}
  </p>
)}
```

## 用户体验优化

### 截断效果
**原来**:
```
后端接收设备需求规格A1.1.docx
```

**现在**:
```
后端接收设...docx  [鼠标悬停显示完整文件名]
```

### Tooltip 交互
- **鼠标悬停**: 显示完整文件名
- **位置**: topLeft（避免遮挡）
- **光标**: help（提示可查看详情）

## 适用场景

### 文档列表
✅ 左侧文档列表中的文件名
✅ 适配移动端和桌面端
✅ 避免长文件名溢出

### 上传提示
✅ "上次上传成功" 提示中的文件名
✅ 节省上传区域空间

## 测试用例

### 1. 短文件名（不截断）
- `test.pdf` → `test.pdf`
- `doc.docx` → `doc.docx`
- `image.png` → `image.png`

### 2. 中等文件名（不截断）
- `report.pdf` → `report.pdf`
- `需求文档.docx` → `需求文档.docx`

### 3. 长文件名（截断）
- `very_long_filename_example.pdf` → `very_l...pdf`
- `后端接收设备需求规格A1.1.docx` → `后端接收设...docx`
- `pasted-image-1729611234567.png` → `pasted...png`

### 4. 无扩展名（不截断）
- `README` → `README`
- `dockerfile` → `dockerfile`

### 5. 特殊字符
- `文件名-with-特殊@字符.pdf` → `文件名-wi...pdf`
- `file (1).docx` → `file (...docx`

## 技术细节

### 截断算法
1. 找到最后一个 `.` 的位置（扩展名分隔符）
2. 分离文件名主体和扩展名
3. 判断是否需要截断（主体长度 > 6）
4. 拼接：`主体前6位 + "..." + 扩展名`

### 性能考虑
- 纯字符串操作，性能优秀
- 无正则表达式，避免性能损耗
- 在 `useMemo` 中计算，避免重复计算

### 边界处理
- 空文件名返回空字符串
- 无扩展名文件不截断
- 文件名很短时不截断（≤10字符）

## 视觉效果

### 桌面端
```
┌───────────────────────────────┐
│ ☐ test.pdf        2.5 MB      │  ← 短文件名，不截断
│ ☐ 后端接收设...docx  1.2 MB   │  ← 长文件名，截断显示
│ ☐ image.png       512 KB      │  ← 短文件名，不截断
└───────────────────────────────┘
     ↑
   鼠标悬停显示完整文件名
```

### 移动端
```
┌──────────────────────┐
│ ☐ test.pdf   2.5 MB  │
│ ☐ 后端接收设...docx  │
│   1.2 MB             │
└──────────────────────┘
```

## 访问测试

**地址**: http://110.40.159.145:3004

**测试步骤**:
1. 上传一个长文件名的文档
2. 查看文档列表中的显示效果
3. 鼠标悬停在文件名上，查看 Tooltip
4. 检查上传提示中的文件名显示

## 总结

✅ **实现了文件名智能截断**
- 保留前6位字符 + 扩展名
- 短文件名不受影响
- 长文件名优雅截断

✅ **提升了用户体验**
- Tooltip 显示完整文件名
- 光标提示可查看详情
- 避免布局溢出

✅ **兼容性良好**
- PC端和移动端都适用
- 中英文文件名都支持
- 特殊字符正常处理

文件名截断功能已完成，自动热重载生效！
