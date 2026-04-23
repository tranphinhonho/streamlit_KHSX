import { useState, useEffect } from 'react';
import { Card, Upload, Button, Select, Typography, message, Table, Space, Tag, Alert, Descriptions } from 'antd';
import { UploadOutlined, CloudUploadOutlined, FileExcelOutlined } from '@ant-design/icons';
import { importApi, productApi } from '../../api/apiClient';
import * as XLSX from 'xlsx';

const { Title, Text } = Typography;

const IMPORT_TYPES = [
  { value: 'order', label: '🛒 Đặt hàng', color: '#A3BE8C' },
  { value: 'plan', label: '📋 Kế hoạch sản xuất', color: '#5E81AC' },
  { value: 'pellet', label: '⚙️ Pellet', color: '#EBCB8B' },
  { value: 'stock', label: '📊 Stock', color: '#B48EAD' },
  { value: 'product', label: '📦 Sản phẩm', color: '#BF616A' },
];

// ========== Types ==========

interface OrderPreviewRow {
  _key: number;
  codeCam: string;
  ngayLay: string;
  soLuong: number;
  idSanPham: number | null;
  tenCam: string;
  matched: boolean;
}

interface ExcelMeta {
  daiLy: string;
  mskh: string;
  diaChi: string;
  tuan: string;
}

interface ProductItem {
  id: number;
  codeCam: string;
  tenCam?: string;
}

// ========== Excel Parser for Weekly Order Plan ==========

function parseWeeklyOrderExcel(ws: XLSX.WorkSheet): { rows: OrderPreviewRow[]; meta: ExcelMeta; format: 'bao' | 'silo'; products: Map<string, any> } | null {
  // Read as raw 2D array to handle merged cells & complex layout
  const raw: any[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
  if (!raw || raw.length < 5) return null;

  // DEBUG: Log raw data to help diagnose parsing issues
  console.log('=== RAW EXCEL DATA ===');
  raw.forEach((row, i) => {
    const cells = row.map((c: any, j: number) => `[${j}]=${JSON.stringify(c)}`).join(' | ');
    console.log(`Row ${i}: ${cells}`);
  });
  console.log('=== END RAW DATA ===');

  // Extract meta info from first rows
  const meta: ExcelMeta = { daiLy: '', mskh: '', diaChi: '', tuan: '' };

  for (let i = 0; i < Math.min(raw.length, 10); i++) {
    const cellA = String(raw[i]?.[0] || '').trim();
    const upper = cellA.toUpperCase();
    if (upper.includes('ĐẠI LÝ') || upper.includes('DAI LY') || upper.includes('CHI NHÁNH')) meta.daiLy = cellA;
    else if (upper.includes('MSKH')) meta.mskh = cellA;
    else if (upper.includes('ĐC') || upper.includes('ĐỊA CHỈ')) meta.diaChi = cellA;
    else if (upper.includes('TUẦN') || upper.includes('TUAN') || upper.includes('KẾ HOẠCH')) meta.tuan = cellA;
    else if (upper.includes('TỪ NGÀY') || upper.includes('TU NGAY')) { if (!meta.tuan) meta.tuan = cellA; }
  }

  // STRATEGY: Find the header row and date columns
  // Format 1 (BAO): "CÁM BAO | THỨ 2 | THỨ 3..." + next row "Ngày | 23/3 | 24/3..."
  // Format 2 (SILO): "NGÀY | PELLET SIZE | 23/3/2026 | 24/3/2026..." (dates in same row)

  let headerIdx = -1;
  let dateIdx = -1;
  let dataColStart = 1; // column index where date columns start (skip col A = product name)

  for (let i = 0; i < Math.min(raw.length, 20); i++) {
    const row = raw[i];
    if (!row) continue;

    // Count "THỨ" keywords in columns B+ (BAO format)
    let thuCount = 0;
    for (let c = 1; c < Math.min(row.length, 12); c++) {
      const cell = String(row[c] || '').trim().toUpperCase();
      if (cell.includes('THỨ') || cell.includes('THU')) thuCount++;
    }
    if (thuCount >= 3) {
      headerIdx = i;
      console.log(`Found BAO header row at index ${i}`);
      break;
    }

    // Count date-like values in columns (SILO format: dates directly in header)
    let dateCount = 0;
    let firstDateCol = -1;
    for (let c = 1; c < Math.min(row.length, 12); c++) {
      if (looksLikeDate(row[c])) {
        dateCount++;
        if (firstDateCol < 0) firstDateCol = c;
      }
    }
    // If this row has 3+ dates, it's a SILO-style header with dates inline
    if (dateCount >= 3) {
      // Also check column A for "NGÀY", "CÁM", or similar header text
      const cellA = String(row[0] || '').trim().toUpperCase();
      if (cellA.includes('NGÀY') || cellA.includes('NGAY') || cellA.includes('CÁM')
          || cellA.includes('CAM') || cellA.includes('STT') || cellA.includes('TÊN')) {
        headerIdx = i;
        dateIdx = i; // dates are in the same row!
        dataColStart = firstDateCol;
        console.log(`Found SILO header+date row at index ${i}, dates start at col ${firstDateCol}`);
        break;
      }
    }

    // Check column A for "CÁM" with "THỨ" in other columns
    const cellA = String(row[0] || '').trim().toUpperCase();
    if (cellA.includes('CÁM') || cellA.includes('CAM')) {
      let hasThu = false;
      for (let c = 1; c < Math.min(row.length, 12); c++) {
        if (String(row[c] || '').trim().toUpperCase().includes('THỨ')) { hasThu = true; break; }
      }
      if (hasThu) {
        headerIdx = i;
        console.log(`Found BAO header row (via CÁM) at index ${i}`);
        break;
      }
    }
  }

  if (headerIdx < 0) {
    console.log('Could not find header row');
    return null;
  }

  // If dateIdx not yet found (BAO format), search for date row after header
  if (dateIdx < 0) {
    for (let i = headerIdx + 1; i <= Math.min(headerIdx + 3, raw.length - 1); i++) {
      const row = raw[i];
      if (!row) continue;
      let dateCount = 0;
      for (let c = 1; c < Math.min(row.length, 12); c++) {
        if (looksLikeDate(row[c])) dateCount++;
      }
      if (dateCount >= 3) {
        dateIdx = i;
        console.log(`Found separate date row at index ${i}`);
        break;
      }
    }
  }

  if (dateIdx < 0) {
    console.log('Could not find date row');
    return null;
  }

  // Extract dates from the date row
  const dateRow = raw[dateIdx];

  // Map column index → date string
  const colDates: Map<number, string> = new Map();
  for (let c = dataColStart; c < dateRow.length; c++) {
    // Stop at TOTAL/summary columns
    const cellVal = String(dateRow[c] || '').trim().toUpperCase();
    if (cellVal.includes('TOTAL') || cellVal === 'BAG' || cellVal === 'TON' || cellVal.includes('TỔNG')) break;
    // Also check the header row for TOTAL keywords if header != date row
    if (headerIdx !== dateIdx) {
      const headerCell = String(raw[headerIdx][c] || '').trim().toUpperCase();
      if (headerCell.includes('TOTAL') || headerCell === 'BAG' || headerCell === 'TON') break;
    }

    const dateVal = dateRow[c];
    if (looksLikeDate(dateVal)) {
      const dateStr = formatExcelDate(dateVal);
      if (dateStr) {
        colDates.set(c, dateStr);
        console.log(`Column ${c}: date = ${dateStr}`);
      }
    }
  }

  console.log(`Found ${colDates.size} date columns`);
  if (colDates.size === 0) return null;

  // Extract data rows (after dateIdx, skip TOTAL/empty)
  const dataStartIdx = dateIdx + 1;
  const rows: OrderPreviewRow[] = [];
  let keyCounter = 0;

  for (let r = dataStartIdx; r < raw.length; r++) {
    const row = raw[r];
    if (!row || row.length === 0) continue;

    const codeCam = String(row[0] || '').trim();
    if (!codeCam) continue;

    // Skip TOTAL & summary rows (not product data)
    const upper = codeCam.toUpperCase();
    if (upper === 'TOTAL' || upper.includes('TỔNG') || upper.includes('SỐ LƯỢNG')
        || upper.includes('TONG') || upper.includes('SO LUONG')) continue;

    // For each date column, if quantity > 0, create a preview row
    for (const [colIdx, dateStr] of colDates) {
      const cellVal = row[colIdx];
      const qty = parseNumber(cellVal);
      if (qty > 0) {
        rows.push({
          _key: keyCounter++,
          codeCam,
          ngayLay: dateStr,
          soLuong: qty,
          idSanPham: null, // will be matched later
          tenCam: '',
          matched: false,
        });
      }
    }
  }

  // Determine format: if dateIdx === headerIdx, it's SILO (dates inline)
  const format = (dateIdx === headerIdx) ? 'silo' as const : 'bao' as const;
  console.log(`Detected format: ${format}`);

  return { rows, meta, format, products: new Map() };
}

/** Parse a cell value as a number */
function parseNumber(val: any): number {
  if (val === null || val === undefined || val === '' || val === '-') return 0;
  if (typeof val === 'number') return val;
  const cleaned = String(val).replace(/,/g, '').trim();
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
}

/** Check if a value looks like a date (string "23/3/2026" or Excel serial number) */
function looksLikeDate(val: any): boolean {
  if (!val && val !== 0) return false;
  // String date pattern: dd/mm/yyyy or d/m/yyyy
  if (typeof val === 'string' && /\d{1,2}\/\d{1,2}\/\d{4}/.test(val.trim())) return true;
  // Excel serial date number (typically 40000-60000 range for years 2009-2063)
  if (typeof val === 'number' && val > 40000 && val < 70000) return true;
  return false;
}

/** Format Excel date: could be serial number, Date object, or string like "23/3/2026" */
function formatExcelDate(val: any): string {
  if (!val && val !== 0) return '';
  // Already a formatted string
  if (typeof val === 'string') {
    const trimmed = val.trim();
    if (/\d{1,2}\/\d{1,2}\/\d{4}/.test(trimmed)) {
      // Convert dd/mm/yyyy → yyyy-mm-dd for backend
      const parts = trimmed.split('/');
      if (parts.length === 3) {
        return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
      }
    }
    return trimmed;
  }
  // Excel serial date number
  if (typeof val === 'number' && val > 1000) {
    try {
      const date = XLSX.SSF.parse_date_code(val);
      if (date) {
        return `${date.y}-${String(date.m).padStart(2, '0')}-${String(date.d).padStart(2, '0')}`;
      }
    } catch { /* ignore */ }
  }
  return String(val);
}

/** Format yyyy-mm-dd back to dd/mm/yyyy for display */
function displayDate(dateStr: string): string {
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    const [y, m, d] = dateStr.split('-');
    return `${d}/${m}/${y}`;
  }
  return dateStr;
}

// ========== Generic Parser (for other import types) ==========

/** Auto-format a cell value: detect Excel serial dates and format as dd/mm/yyyy hh:mm:ss */
function autoFormatCell(val: any): any {
  if (val === null || val === undefined || val === '') return val;
  // Detect Excel serial date number (range ~40000-70000 covers years 2009-2091)
  if (typeof val === 'number' && val > 40000 && val < 70000) {
    try {
      const date = XLSX.SSF.parse_date_code(val);
      if (date) {
        const dd = String(date.d).padStart(2, '0');
        const mm = String(date.m).padStart(2, '0');
        const yyyy = date.y;
        const hh = String(date.H).padStart(2, '0');
        const min = String(date.M).padStart(2, '0');
        const ss = String(date.S).padStart(2, '0');
        // If time is 00:00:00, just show date
        if (date.H === 0 && date.M === 0 && date.S === 0) {
          return `${dd}/${mm}/${yyyy}`;
        }
        return `${dd}/${mm}/${yyyy} ${hh}:${min}:${ss}`;
      }
    } catch { /* not a date, return as-is */ }
  }
  return val;
}

function parseGenericExcel(ws: XLSX.WorkSheet) {
  const data = XLSX.utils.sheet_to_json(ws);
  if (data.length === 0) return { data: [], columns: [] };

  const columns = Object.keys(data[0] as object).map((key) => ({
    title: key,
    dataIndex: key,
    key,
    ellipsis: true,
  }));

  // Auto-format all cell values (detect serial dates)
  const formattedData = data.map((row: any, i: number) => {
    const newRow: any = { _key: i };
    for (const key of Object.keys(row)) {
      newRow[key] = autoFormatCell(row[key]);
    }
    return newRow;
  });

  return {
    data: formattedData,
    columns,
  };
}

// ========== Component ==========

export default function ImportPage() {
  const [importType, setImportType] = useState('order');
  const [fileName, setFileName] = useState('');
  const [importing, setImporting] = useState(false);

  // For order import (weekly plan)
  const [orderRows, setOrderRows] = useState<OrderPreviewRow[]>([]);
  const [excelMeta, setExcelMeta] = useState<ExcelMeta | null>(null);
  const [excelFormat, setExcelFormat] = useState<'bao' | 'silo'>('bao');
  const [productList, setProductList] = useState<ProductItem[]>([]);

  // For generic import
  const [genericData, setGenericData] = useState<any[]>([]);
  const [genericColumns, setGenericColumns] = useState<any[]>([]);

  // Load product list on mount
  useEffect(() => {
    productApi.getList().then((res) => {
      setProductList(res.data || []);
    }).catch(() => { /* ignore */ });
  }, []);

  // Match code cám to products (by TenCam first, then CodeCam)
  // Excel has product names like "552", "551X" which are TenCam in the system
  // The actual CodeCam would be something like "321001"
  const matchProducts = (rows: OrderPreviewRow[], products: ProductItem[]): OrderPreviewRow[] => {
    const byTenCam = new Map<string, ProductItem>();
    const byCodeCam = new Map<string, ProductItem>();
    products.forEach(p => {
      if (p.tenCam) byTenCam.set(p.tenCam.toUpperCase().trim(), p);
      if (p.codeCam) byCodeCam.set(p.codeCam.toUpperCase().trim(), p);
    });

    return rows.map(row => {
      const key = row.codeCam.toUpperCase().trim();
      // Try matching by TenCam first (most common for Excel imports)
      const product = byTenCam.get(key) || byCodeCam.get(key);
      return {
        ...row,
        idSanPham: product?.id ?? null,
        tenCam: product?.tenCam || '',
        matched: !!product,
      };
    });
  };

  const handleFileUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const wb = XLSX.read(e.target?.result, { type: 'binary' });
        // Use LAST sheet (latest data) instead of first sheet
        const lastSheetName = wb.SheetNames[wb.SheetNames.length - 1];
        const ws = wb.Sheets[lastSheetName];
        console.log(`Using sheet: "${lastSheetName}" (${wb.SheetNames.length} sheets total)`);

        if (importType === 'order') {
          // Smart parse for weekly order plan
          const result = parseWeeklyOrderExcel(ws);
          if (!result || result.rows.length === 0) {
            message.warning('Không tìm thấy dữ liệu đặt hàng trong file. Hãy kiểm tra format file.');
            return;
          }

          const matched = matchProducts(result.rows, productList);
          const matchedCount = matched.filter(r => r.matched).length;
          const unmatchedCount = matched.filter(r => !r.matched).length;

          setOrderRows(matched);
          setExcelMeta(result.meta);
          setExcelFormat(result.format);
          setGenericData([]); setGenericColumns([]);
          setFileName(file.name);

          if (unmatchedCount > 0) {
            message.warning(`Đã đọc ${matched.length} dòng. ${unmatchedCount} code cám chưa có trong hệ thống!`);
          } else {
            message.success(`Đã đọc ${matched.length} dòng đặt hàng từ ${file.name}`);
          }
        } else {
          // Generic parse for other types
          const { data, columns } = parseGenericExcel(ws);
          if (data.length === 0) {
            message.warning('File không có dữ liệu');
            return;
          }
          setGenericData(data);
          setGenericColumns(columns);
          setOrderRows([]); setExcelMeta(null);
          setFileName(file.name);
          message.success(`Đã đọc ${data.length} dòng từ ${file.name}`);
        }
      } catch {
        message.error('Lỗi đọc file Excel');
      }
    };
    reader.readAsBinaryString(file);
    return false;
  };

  const handleImportOrder = async () => {
    const validRows = orderRows.filter(r => r.matched && r.soLuong > 0);
    if (validRows.length === 0) {
      message.warning('Không có dòng hợp lệ để import (code cám phải tồn tại trong hệ thống)');
      return;
    }

    setImporting(true);
    try {
      const items = validRows.map(r => ({
        idSanPham: r.idSanPham!,
        soLuong: r.soLuong,
        ngayLay: r.ngayLay,
        loaiDatHang: 'Đại lý Bá Cang',
        khachVangLai: 0,
        ghiChu: `Import từ ${fileName}`,
      }));

      const result = await importApi.importOrder({
        loaiDatHang: 'Đại lý Bá Cang',
        maDatHang: `DH_IMPORT_${Date.now()}`,
        items: items.map(i => ({
          idSanPham: i.idSanPham,
          soLuong: i.soLuong,
          ngayLay: i.ngayLay,
          ghiChu: i.ghiChu,
        })),
      });
      message.success(result?.data?.message || `Import thành công ${validRows.length} đơn hàng!`);
      setOrderRows([]); setExcelMeta(null); setFileName('');
    } catch (e: any) {
      message.error(e.response?.data?.message || 'Lỗi khi import');
    } finally {
      setImporting(false);
    }
  };

  const handleImportGeneric = async () => {
    if (genericData.length === 0) {
      message.warning('Chưa có dữ liệu để import');
      return;
    }

    setImporting(true);
    try {
      let result;
      switch (importType) {
        case 'plan':
          result = await importApi.importPlan({
            ngayPlan: new Date().toISOString().split('T')[0],
            maPlan: `PL_IMPORT_${Date.now()}`,
            items: genericData.map(r => ({
              idSanPham: r.id_san_pham || r.IdSanPham || r.ID || 0,
              soLuong: r.so_luong || r.SoLuong || r['Số lượng'] || 0,
              ghiChu: r.ghi_chu || r.GhiChu || r['Ghi chú'] || '',
            })),
          });
          break;
        case 'product':
          console.log('Product import data sample:', genericData[0]);
          result = await importApi.importProduct(genericData.map(r => ({
            codeCam: String(r['Code cám'] ?? r.code_cam ?? r.CodeCam ?? r['Code cam'] ?? ''),
            tenCam: String(r['Tên cám'] ?? r.ten_cam ?? r.TenCam ?? r['Ten cam'] ?? ''),
            dangEpVien: String(r['Dạng ép viên'] ?? r.dang_ep_vien ?? r.DangEpVien ?? ''),
            kichCoEpVien: String(r['Kích cỡ ép viên'] ?? r.kich_co_ep_vien ?? r.KichCoEpVien ?? ''),
            batchSize: Number(r['Batch size'] ?? r.BatchSize ?? r.batch_size ?? 0) || null,
            vatNuoi: String(r['Vật nuôi'] ?? r.vat_nuoi ?? r.VatNuoi ?? r['Vat nuoi'] ?? ''),
          })));
          break;
        case 'stock':
          result = await importApi.importStock({
            ngayCapNhat: new Date().toISOString().split('T')[0],
            items: genericData.map(r => ({
              idSanPham: r.id_san_pham || r.IdSanPham || r.ID || 0,
              soLuong: r.so_luong || r.SoLuong || r['Số lượng'] || 0,
            })),
          });
          break;
        case 'pellet':
          result = await importApi.importPellet({
            ngaySanXuat: new Date().toISOString(),
            items: genericData.map(r => ({
              idSanPham: r.id_san_pham || r.IdSanPham || r.ID || 0,
              soLuong: r.so_luong || r.SoLuong || r['Số lượng'] || 0,
              soMay: r.so_may || r.SoMay || 'M1',
            })),
          });
          break;
      }
      message.success(result?.data?.message || 'Import thành công!');
      setGenericData([]); setGenericColumns([]); setFileName('');
    } catch (e: any) {
      console.error('Import error:', e);
      console.error('Response data:', e.response?.data);
      const errMsg = e.response?.data?.message
        || e.response?.data?.title
        || (typeof e.response?.data === 'string' ? e.response.data : null)
        || e.message
        || 'Lỗi khi import';
      message.error(errMsg);
    } finally {
      setImporting(false);
    }
  };

  const totalRows = importType === 'order' ? orderRows.length : genericData.length;
  const matchedCount = orderRows.filter(r => r.matched).length;
  const unmatchedCodes = [...new Set(orderRows.filter(r => !r.matched).map(r => r.codeCam))];

  // Order preview columns — adapt based on format (BAO vs SILO)
  const isSilo = excelFormat === 'silo';
  const orderColumns = [
    {
      title: 'Code Cám',
      dataIndex: 'codeCam',
      key: 'codeCam',
      width: 120,
      render: (val: string, row: OrderPreviewRow) => (
        <Text strong style={{ color: row.matched ? undefined : '#BF616A' }}>{val}</Text>
      ),
    },
    {
      title: 'Ngày Lấy',
      dataIndex: 'ngayLay',
      key: 'ngayLay',
      width: 120,
      render: (val: string) => <Tag color="blue">{displayDate(val)}</Tag>,
    },
    {
      title: isSilo ? 'Số Lượng (Kg)' : 'Số Lượng (BAG)',
      dataIndex: 'soLuong',
      key: 'soLuong',
      width: 140,
      align: 'right' as const,
      render: (val: number) => (
        <Text strong style={{ color: '#A3BE8C', fontSize: 15 }}>
          {val.toLocaleString('vi-VN')}
        </Text>
      ),
    },
    // Only show Kg column for BAO format (BAG × 25)
    ...(!isSilo ? [{
      title: 'Số Lượng (Kg)',
      key: 'soLuongKg',
      width: 140,
      align: 'right' as const,
      render: (_: any, row: OrderPreviewRow) => (
        <Text strong style={{ color: '#5E81AC', fontSize: 15 }}>
          {(row.soLuong * 25).toLocaleString('vi-VN')}
        </Text>
      ),
    }] : []),
  ];

  return (
    <div>
      <Title level={3}>📥 Import dữ liệu từ Excel</Title>

      <Card style={{ borderRadius: 12, marginBottom: 16 }}>
        <Space size="large" wrap>
          <Select value={importType} onChange={(v) => {
            setImportType(v);
            // Clear preview on type change
            setOrderRows([]); setExcelMeta(null);
            setGenericData([]); setGenericColumns([]);
            setFileName('');
          }} style={{ width: 250 }} options={IMPORT_TYPES} />
          <Upload beforeUpload={handleFileUpload} accept=".xlsx,.xls,.csv" showUploadList={false}>
            <Button icon={<UploadOutlined />} size="large">Chọn file Excel</Button>
          </Upload>
          {fileName && <Tag icon={<FileExcelOutlined />} color="green">{fileName}</Tag>}
          {totalRows > 0 && (
            <Button type="primary" icon={<CloudUploadOutlined />}
              onClick={importType === 'order' ? handleImportOrder : handleImportGeneric}
              loading={importing} size="large">
              Import {importType === 'order' ? `${matchedCount} đơn hàng` : `${totalRows} dòng`}
            </Button>
          )}
        </Space>
      </Card>

      {/* Order Import Preview */}
      {importType === 'order' && orderRows.length > 0 && (
        <>
          {/* Meta info */}
          {excelMeta && (
            <Card style={{ borderRadius: 12, marginBottom: 16, background: '#f0f5ff' }} size="small">
              <Descriptions size="small" column={2} bordered>
                <Descriptions.Item label="Đại lý">{excelMeta.daiLy}</Descriptions.Item>
                <Descriptions.Item label="MSKH">{excelMeta.mskh}</Descriptions.Item>
                <Descriptions.Item label="Địa chỉ">{excelMeta.diaChi}</Descriptions.Item>
                <Descriptions.Item label="Tuần">{excelMeta.tuan}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}

          {/* Warnings */}
          {unmatchedCodes.length > 0 && (
            <Alert type="warning" showIcon style={{ marginBottom: 16, borderRadius: 8 }}
              message={`${unmatchedCodes.length} code cám chưa có trong hệ thống`}
              description={
                <div>
                  <Text>Các code cám sau sẽ <strong>không được import</strong>: </Text>
                  {unmatchedCodes.map(c => <Tag key={c} color="orange" style={{ margin: 2 }}>{c}</Tag>)}
                  <br/><Text type="secondary" style={{ fontSize: 12 }}>
                    Hãy thêm sản phẩm trước trong mục "Sản phẩm" rồi import lại.
                  </Text>
                </div>
              }
            />
          )}

          <Card
            title={
              <Space>
                <span>📋 Xem trước đơn hàng ({orderRows.length} dòng)</span>
                <Tag color="green">{matchedCount} hợp lệ</Tag>
                {unmatchedCodes.length > 0 && <Tag color="orange">{orderRows.length - matchedCount} thiếu sản phẩm</Tag>}
              </Space>
            }
            style={{ borderRadius: 12 }}
          >
            <Alert type="info" showIcon style={{ marginBottom: 16 }}
              message={isSilo
                ? "Mỗi dòng = 1 đơn hàng (code cám + ngày lấy + số lượng Kg). Chỉ dòng hợp lệ mới được import."
                : "Mỗi dòng = 1 đơn hàng (code cám + ngày lấy + số lượng BAG). Chỉ dòng hợp lệ mới được import."
              } />
            <Table dataSource={orderRows} columns={orderColumns} rowKey="_key"
              size="small" bordered pagination={{ pageSize: 30 }}
              rowClassName={(row) => row.matched ? '' : 'ant-table-row-warning'}
              summary={() => {
                const total = orderRows.reduce((sum, r) => sum + r.soLuong, 0);
                return (
                <Table.Summary.Row>
                  <Table.Summary.Cell index={0} colSpan={2}>
                    <Text strong>TỔNG</Text>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={2} align="right">
                    <Text strong style={{ color: '#A3BE8C', fontSize: 16 }}>
                      {total.toLocaleString('vi-VN')} {isSilo ? 'Kg' : 'BAG'}
                    </Text>
                  </Table.Summary.Cell>
                  {!isSilo && (
                    <Table.Summary.Cell index={3} align="right">
                      <Text strong style={{ color: '#5E81AC', fontSize: 16 }}>
                        {(total * 25).toLocaleString('vi-VN')} Kg
                      </Text>
                    </Table.Summary.Cell>
                  )}
                </Table.Summary.Row>);
              }}
            />
          </Card>
        </>
      )}

      {/* Generic Import Preview */}
      {importType !== 'order' && genericData.length > 0 && (
        <Card title={`📋 Xem trước dữ liệu (${genericData.length} dòng)`} style={{ borderRadius: 12 }}>
          <Alert type="info" showIcon style={{ marginBottom: 16 }}
            message="Kiểm tra dữ liệu trước khi import. Các cột sẽ được tự động map sang hệ thống." />
          <Table dataSource={genericData} columns={genericColumns} rowKey="_key"
            size="small" scroll={{ x: true }} pagination={{ pageSize: 20 }} bordered />
        </Card>
      )}

      {/* Empty state */}
      {totalRows === 0 && (
        <Card style={{ borderRadius: 12, textAlign: 'center', padding: 60 }}>
          <FileExcelOutlined style={{ fontSize: 64, color: '#ccc', marginBottom: 16 }} />
          <div><Text type="secondary" style={{ fontSize: 16 }}>
            {importType === 'order'
              ? 'Upload file "Kế hoạch cám tuần" (.xlsx) để import đặt hàng'
              : 'Chọn loại import và upload file Excel để bắt đầu'}
          </Text></div>
        </Card>
      )}
    </div>
  );
}
