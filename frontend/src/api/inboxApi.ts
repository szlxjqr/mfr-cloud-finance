import http from '@/utils/request'
import type { InvoiceInbox } from '@/types/invoice'

// 发票箱 API：上传（浏览器已解析，随文件带 extracted_json）/列表/详情/校正/挂接/查验/删除。
export const inboxApi = {
  list: (params?: { status?: string; keyword?: string }) =>
    http.get<InvoiceInbox[]>('/invoice-inbox', { params }),

  get: (id: number) => http.get<InvoiceInbox>(`/invoice-inbox/${id}`),

  // 上传原文件 + 浏览器端已解析的 extracted_json（JSON 字符串）
  upload: (file: File, extractedJson: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('extracted_json', extractedJson)
    return http.post<InvoiceInbox>('/invoice-inbox/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // 人工校正：提交完整 extracted_json
  update: (id: number, extractedJson: string) =>
    http.put<InvoiceInbox>(`/invoice-inbox/${id}`, { extracted_json: extractedJson }),

  // 挂接到业务单：reimburse(报销单) / purchase(采购申请)
  link: (id: number, docType: string, docId: number) =>
    http.post<InvoiceInbox>(`/invoice-inbox/${id}/link`, {
      doc_type: docType,
      doc_id: docId,
    }),

  // P1 查验结果登记
  verify: (id: number, result: string, note?: string) =>
    http.post<InvoiceInbox>(`/invoice-inbox/${id}/verify`, { result, note }),

  remove: (id: number) => http.delete(`/invoice-inbox/${id}`),
}
