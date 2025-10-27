import { InboxOutlined } from '@ant-design/icons';
import type { UploadRequestOption } from 'rc-upload/lib/interface';
import { Button, message, Upload } from 'antd';
import type { UploadProps } from 'antd/es/upload';
import React, { useEffect, useState } from 'react';

import { uploadDocument } from '../services/api';
import { useAppStore, DOCUMENT_HISTORY_STORAGE_KEY } from '../stores/chatStore';
import type { Document } from '../types';
import { useMediaQuery } from '../hooks/useMediaQuery';

const { Dragger } = Upload;

const LAST_UPLOADED_KEY = 'last_uploaded_document';
const UPLOADED_LIST_KEY = 'uploaded_documents';
const MAX_FILE_SIZE_BYTES = 6 * 1024 * 1024;
const MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024;
const SIZE_LIMIT_ERROR = 'SIZE_LIMIT_EXCEEDED';

const FileUploader: React.FC = () => {
  const addDocument = useAppStore((state) => state.addDocument);
  const clearDocuments = useAppStore((state) => state.clearDocuments);
  const [lastUploadedName, setLastUploadedName] = useState<string | null>(null);
  const [lastUploadedSize, setLastUploadedSize] = useState<string | null>(null);
  const isMobile = useMediaQuery('(max-width: 767px)');

  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const value = bytes / Math.pow(1024, i);
    const fixed = value >= 100 ? value.toFixed(0) : value >= 10 ? value.toFixed(1) : value.toFixed(2);
    return `${fixed} ${units[i]}`;
  };

  // 截断文件名：保留前6位字符 + 扩展名
  const truncateFileName = (fileName: string): string => {
    if (!fileName) return '';

    // 找到最后一个点的位置（扩展名）
    const lastDotIndex = fileName.lastIndexOf('.');

    // 如果没有扩展名或文件名很短，直接返回
    if (lastDotIndex === -1 || fileName.length <= 10) {
      return fileName;
    }

    // 分离文件名和扩展名
    const nameWithoutExt = fileName.substring(0, lastDotIndex);
    const extension = fileName.substring(lastDotIndex); // 包含 .

    // 如果文件名（不含扩展名）长度 <= 6，直接返回完整文件名
    if (nameWithoutExt.length <= 6) {
      return fileName;
    }

    // 截取前6位 + ... + 扩展名
    return `${nameWithoutExt.substring(0, 6)}...${extension}`;
  };

  // Load last successful upload from localStorage on mount
  useEffect(() => {
    try {
      const listRaw = localStorage.getItem(UPLOADED_LIST_KEY);
      if (listRaw) {
        const docs: Document[] = JSON.parse(listRaw) ?? [];
        docs.forEach((d) => {
          if (d && d.id) addDocument(d);
        });
        if (docs.length > 0) {
          const last = docs[docs.length - 1];
          setLastUploadedName(last?.original_name ?? null);
          setLastUploadedSize(typeof last?.size === 'number' ? formatBytes(last.size) : null);
        }
      } else {
        // fallback to last single record for backward compatibility
        const raw = localStorage.getItem(LAST_UPLOADED_KEY);
        if (raw) {
          const doc = JSON.parse(raw);
          if (doc && doc.id) {
            addDocument(doc);
            setLastUploadedName(doc.original_name ?? null);
            setLastUploadedSize(typeof doc.size === 'number' ? formatBytes(doc.size) : null);
          }
        }
      }
    } catch {
      // ignore parse/localStorage errors
    }
  }, [addDocument]);

  const getSizeLimitError = (file: File): string | null => {
    const isImage = (file.type || '').startsWith('image/');
    if (isImage && file.size > MAX_IMAGE_SIZE_BYTES) {
      return '图片大小不能超过2MB';
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return '文件大小不能超过6MB';
    }
    return null;
  };

  // 上传文件的通用函数
  const uploadFile = async (
    file: File,
    options?: {
      onSizeError?: (message: string) => void;
      suppressSuccessToast?: boolean;
    }
  ) => {
    const notifySizeError = options?.onSizeError ?? ((msg: string) => message.error(msg));
    const sizeError = getSizeLimitError(file);
    if (sizeError) {
      notifySizeError(sizeError);
      throw new Error(SIZE_LIMIT_ERROR);
    }

    try {
      const response = await uploadDocument(file);
      addDocument(response.document);
      // Broadcast uploaded document id so pages can react (e.g., select it)
      try {
        const evt = new CustomEvent('document_uploaded', {
          detail: { id: response.document.id }
        });
        window.dispatchEvent(evt);
      } catch {}
      // persist last successful upload & update history list
      try {
        const doc = response.document as Document;
        localStorage.setItem(LAST_UPLOADED_KEY, JSON.stringify(doc));
        const listRaw = localStorage.getItem(UPLOADED_LIST_KEY);
        const list: Document[] = listRaw ? JSON.parse(listRaw) : [];
        const next = [...list.filter((d) => d.id !== doc.id), doc];
        localStorage.setItem(UPLOADED_LIST_KEY, JSON.stringify(next));
        setLastUploadedName(doc.original_name ?? null);
        setLastUploadedSize(typeof doc.size === 'number' ? formatBytes(doc.size) : null);
      } catch {
        // ignore localStorage errors
      }
      const sizeText = formatBytes(response.document.size);
      if (!options?.suppressSuccessToast) {
        if (response.is_duplicate) {
          message.info(`已存在相同文件，复用历史记录: ${response.document.original_name} (${sizeText})`);
        } else {
          message.success(`上传成功: ${response.document.original_name} (${sizeText})`);
        }
      }
    } catch (error) {
      throw error;
    }
  };

  // 监听粘贴事件
  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        // 检查是否为图片
        if (item.type.indexOf('image') !== -1) {
          e.preventDefault();
          const file = item.getAsFile();
          if (file) {
            // 生成文件名
            const timestamp = new Date().getTime();
            const ext = file.type.split('/')[1] || 'png';
            const fileName = `pasted-image-${timestamp}.${ext}`;
            // 创建新的File对象，设置文件名
            const newFile = new File([file], fileName, { type: file.type });

            message.loading({ content: '正在上传粘贴的图片...', key: 'paste-upload' });
            try {
              await uploadFile(newFile, {
                onSizeError: (msg) => message.error({ content: msg, key: 'paste-upload' }),
                suppressSuccessToast: true
              });
              message.success({ content: '图片上传成功', key: 'paste-upload' });
            } catch (error) {
              if (error instanceof Error && error.message === SIZE_LIMIT_ERROR) {
                return;
              }
              message.error({ content: '图片上传失败', key: 'paste-upload' });
            }
          }
          break;
        }
      }
    };

    document.addEventListener('paste', handlePaste);
    return () => {
      document.removeEventListener('paste', handlePaste);
    };
  }, [addDocument]);

  const props: UploadProps = {
    name: 'file',
    multiple: false,
    showUploadList: false,
    beforeUpload: (file) => {
      const errorMessage = getSizeLimitError(file as File);
      if (errorMessage) {
        message.error(errorMessage);
        return Upload.LIST_IGNORE;
      }
      return true;
    },
    customRequest: async ({ file, onSuccess, onError }: UploadRequestOption) => {
      try {
        await uploadFile(file as File);
        onSuccess?.('ok', file);
      } catch (error) {
        if (!(error instanceof Error && error.message === SIZE_LIMIT_ERROR)) {
          message.error('上传失败，请重试');
        }
        onError?.(error as Error);
      }
    }
  };

  const handleClearHistory = () => {
    try {
      localStorage.removeItem(LAST_UPLOADED_KEY);
      localStorage.removeItem(UPLOADED_LIST_KEY);
      localStorage.removeItem(DOCUMENT_HISTORY_STORAGE_KEY);
    } catch {}
    clearDocuments();
    setLastUploadedName(null);
    setLastUploadedSize(null);
    message.success('已清除本地上传记录');
  };

  return (
    <Dragger {...props} style={{ padding: isMobile ? '4px 8px' : '12px 16px' }}>
      <p className="ant-upload-drag-icon" style={{ marginBottom: isMobile ? 2 : 8 }}>
        <InboxOutlined style={{ fontSize: isMobile ? 24 : 32 }} />
      </p>
      <p className="ant-upload-text" style={{ fontSize: isMobile ? 13 : 14, marginBottom: isMobile ? 2 : 4 }}>
        {isMobile ? '点击上传' : '点击或拖拽文件到此处上传'}
      </p>
      <p className="ant-upload-hint" style={{ fontSize: isMobile ? 11 : 12, marginBottom: lastUploadedName ? (isMobile ? 2 : 4) : 0 }}>
        {isMobile ? '支持 PDF / DOCX / 图片' : '支持 PDF / DOCX / 图片 等格式，也可以直接粘贴图片（Ctrl+V）'}
      </p>
      {lastUploadedName && (
        <p className="ant-upload-hint" style={{ fontSize: isMobile ? 11 : 12, marginBottom: 0 }}>
          上次：{truncateFileName(lastUploadedName)}{lastUploadedSize ? ` (${lastUploadedSize})` : ''}
        </p>
      )}
      <div style={{ marginTop: isMobile ? 2 : 8 }}>
        <Button type="link" size="small" onClick={handleClearHistory}>
          {isMobile ? '清除记录' : '清除本地上传记录'}
        </Button>
      </div>
    </Dragger>
  );
};

export default FileUploader;
