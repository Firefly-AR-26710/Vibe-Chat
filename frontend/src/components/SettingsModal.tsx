import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Radio, Button, Space, App } from 'antd';

interface SettingsModalProps {
  open: boolean;
  onCancel: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ open, onCancel }) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const provider = Form.useWatch('provider', form);

  useEffect(() => {
    if (open) {
      fetchSettings();
    }
  }, [open]);

  const fetchSettings = async () => {
    setFetching(true);
    try {
      const host = window.location.hostname;
      const res = await fetch(`http://${host}:8000/api/settings/llm`);
      if (res.ok) {
        const data = await res.json();
        form.setFieldsValue(data);
      } else {
        message.error("无法加载设置");
      }
    } catch (error) {
      message.error("连接设置服务器失败");
    } finally {
      setFetching(false);
    }
  };

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      const host = window.location.hostname;
      const res = await fetch(`http://${host}:8000/api/settings/llm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });

      if (res.ok) {
        message.success("设置保存成功");
        onCancel();
      } else {
        message.error("保存失败");
      }
    } catch (error) {
      message.error("保存失败，请检查网络");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="API 接口自定义设置"
      open={open}
      onCancel={onCancel}
      footer={null}
      destroyOnHidden
    >
      <Spin spinning={fetching}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{ provider: "openai" }}
          className="mt-4"
        >
          <Form.Item name="provider" label="大模型提供商">
            <Radio.Group>
              <Radio value="openai">OpenAI 兼容接口</Radio>
              <Radio value="anthropic">Anthropic 兼容接口</Radio>
            </Radio.Group>
          </Form.Item>

          {provider === 'openai' && (
            <>
              <Form.Item name="openai_api_key" label="API Key">
                <Input.Password placeholder="sk-..." />
              </Form.Item>
              <Form.Item name="openai_base_url" label="Base URL (可选)">
                <Input placeholder="https://api.openai.com/v1" />
              </Form.Item>
              <Form.Item name="openai_model" label="模型名称">
                <Input placeholder="gpt-4o-mini" />
              </Form.Item>
            </>
          )}

          {provider === 'anthropic' && (
            <>
              <Form.Item name="anthropic_api_key" label="API Key">
                <Input.Password placeholder="sk-ant-..." />
              </Form.Item>
              <Form.Item name="anthropic_base_url" label="Base URL (可选)">
                <Input placeholder="https://api.anthropic.com" />
              </Form.Item>
              <Form.Item name="anthropic_model" label="模型名称">
                <Input placeholder="claude-3-5-sonnet-20241022" />
              </Form.Item>
            </>
          )}

          <div className="flex justify-end gap-2 mt-6">
            <Button onClick={onCancel}>取消</Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存
            </Button>
          </div>
        </Form>
      </Spin>
    </Modal>
  );
};

// Also import Spin locally inside the component to avoid any missing imports
import { Spin } from 'antd';
