import { Modal, Input, message } from 'antd';
import React, { useState, useEffect } from 'react';

const { TextArea } = Input;

interface Props {
  visible: boolean;
  title: string;
  data: Record<string, unknown>;
  onSave: (data: Record<string, unknown>) => void;
  onCancel: () => void;
}

const EditResultModal: React.FC<Props> = ({ visible, title, data, onSave, onCancel }) => {
  const [jsonText, setJsonText] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (visible && data) {
      setJsonText(JSON.stringify(data, null, 2));
      setError(null);
    }
  }, [visible, data]);

  const handleSave = () => {
    try {
      const parsed = JSON.parse(jsonText);
      setError(null);
      onSave(parsed);
      message.success('数据已保存');
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : '无效的JSON格式';
      setError(errorMsg);
      message.error('JSON格式错误: ' + errorMsg);
    }
  };

  return (
    <Modal
      title={`编辑 - ${title}`}
      open={visible}
      onOk={handleSave}
      onCancel={onCancel}
      width={800}
      okText="保存并继续"
      cancelText="取消"
    >
      <div style={{ marginBottom: 8 }}>
        <span style={{ color: '#666' }}>请编辑JSON数据:</span>
      </div>
      <TextArea
        value={jsonText}
        onChange={(e) => setJsonText(e.target.value)}
        rows={20}
        style={{
          fontFamily: 'monospace',
          fontSize: 13,
          borderColor: error ? '#ff4d4f' : undefined
        }}
      />
      {error && (
        <div style={{ marginTop: 8, color: '#ff4d4f', fontSize: 12 }}>
          错误: {error}
        </div>
      )}
      <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
        提示: 修改完成后点击"保存并继续"将继续执行后续智能体
      </div>
    </Modal>
  );
};

export default EditResultModal;
