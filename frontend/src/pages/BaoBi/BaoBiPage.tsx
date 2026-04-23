import { useEffect, useState } from 'react';
import { Table, Card, Button, Space, Typography, Modal, Form, InputNumber,
  Input, DatePicker, Select, message, Popconfirm, Tag } from 'antd';
import { PlusOutlined, DeleteOutlined, ReloadOutlined, WarningOutlined } from '@ant-design/icons';
import { baobiApi } from '../../api/apiClient';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';

const { Title } = Typography;

const ALERT_COLORS: Record<string, string> = {
  'Bình thường': 'green', 'Cần theo dõi': 'orange', 'Cảnh báo': 'red', 'Thiếu': 'volcano',
};

export default function BaoBiPage() {
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => { loadData(); }, [page]);

  const loadData = async () => {
    setLoading(true);
    try { const res = await baobiApi.getAll({ page, pageSize: 50 }); setRecords(res.data.items); setTotal(res.data.totalCount); }
    catch { /* */ } finally { setLoading(false); }
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await baobiApi.create({ ...values, ngayKiemTra: values.ngayKiemTra?.toISOString() ?? new Date().toISOString() });
      message.success('Đã thêm!'); setShowModal(false); form.resetFields(); loadData();
    } catch { message.error('Lỗi'); }
  };

  const columns: ColumnsType<any> = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: 'Loại bao', dataIndex: 'loaiBao', width: 150 },
    { title: 'Kích cỡ (kg)', dataIndex: 'kichCoKg', width: 100, align: 'right' },
    { title: 'Tồn kho hiện tại', dataIndex: 'tonKhoHienTai', width: 130, align: 'right',
      render: (v: number) => <strong>{v?.toLocaleString()}</strong> },
    { title: 'Nhu cầu dự kiến', dataIndex: 'nhuCauDuKien', width: 130, align: 'right',
      render: (v: number) => v ? v.toLocaleString() : '-' },
    { title: 'Mức cảnh báo', dataIndex: 'mucCanhBao', width: 120,
      render: (v: string) => v ? <Tag icon={v === 'Thiếu' ? <WarningOutlined /> : undefined}
        color={ALERT_COLORS[v] || 'default'}>{v}</Tag> : '-' },
    { title: 'SL thiếu', dataIndex: 'soLuongThieu', width: 80, align: 'right',
      render: (v: number) => v ? <span style={{ color: '#BF616A', fontWeight: 600 }}>{v.toLocaleString()}</span> : '-' },
    { title: 'Ngày kiểm tra', dataIndex: 'ngayKiemTra', width: 120,
      render: (v: string) => v ? dayjs(v).format('DD/MM/YYYY') : '-' },
    { title: 'Ghi chú', dataIndex: 'ghiChu', ellipsis: true },
    { title: '', key: 'action', width: 50,
      render: (_, r: any) => (
        <Popconfirm title="Xóa?" onConfirm={async () => { await baobiApi.delete(r.id); loadData(); }}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3}>🎒 Bao bì - Tồn kho</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadData}>Tải lại</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowModal(true)}>Thêm</Button>
        </Space>
      </div>
      <Card style={{ borderRadius: 12 }}>
        <Table dataSource={records} columns={columns} rowKey="id" loading={loading} size="middle" scroll={{ x: 900 }}
          pagination={{ current: page, total, pageSize: 50, onChange: setPage, showTotal: (t) => `Tổng ${t}` }} />
      </Card>
      <Modal title="Thêm bao bì" open={showModal} onOk={handleCreate}
        onCancel={() => setShowModal(false)} okText="Tạo" cancelText="Hủy">
        <Form form={form} layout="vertical" initialValues={{ kichCoKg: 25, ngayKiemTra: dayjs() }}>
          <Form.Item name="ngayKiemTra" label="Ngày kiểm tra"><DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" /></Form.Item>
          <Form.Item name="loaiBao" label="Loại bao" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="kichCoKg" label="Kích cỡ (kg)">
            <Select options={[25, 40, 50].map(v => ({ value: v, label: `${v} kg` }))} />
          </Form.Item>
          <Form.Item name="tonKhoHienTai" label="Tồn kho hiện tại" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
          <Form.Item name="nhuCauDuKien" label="Nhu cầu dự kiến"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
          <Form.Item name="mucCanhBao" label="Mức cảnh báo">
            <Select options={Object.keys(ALERT_COLORS).map(k => ({ value: k, label: k }))} />
          </Form.Item>
          <Form.Item name="soLuongThieu" label="Số lượng thiếu"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
          <Form.Item name="ghiChu" label="Ghi chú"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
