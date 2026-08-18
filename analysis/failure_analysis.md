# Failure Analysis — Lab 18: Production RAG

**Tác giả:** Hoàng Mạnh Dũng  
**Module phụ trách:** M1 (Chunking) · M2 (Search) · M3 (Reranking) · M4 (Evaluation) · M5 (Enrichment)

---

## RAGAS Scores

| Metric | Naive Baseline | Production Pipeline | Δ | Đánh giá |
|--------|:--------------:|:-------------------:|:---:|----------|
| **Faithfulness** | 0.8816 | 0.8270 | -0.0546 | ✅ Đạt chuẩn cao (>0.80) |
| **Answer Relevancy** | 0.9047 | 0.8993 | -0.0054 | ✅ Đạt chuẩn rất cao (~0.90) |
| **Context Precision** | 0.9234 | 0.8808 | -0.0426 | ✅ Đạt chuẩn cao (>0.85) |
| **Context Recall** | 0.9490 | 0.9102 | -0.0388 | ✅ Đạt chuẩn cao (>0.90) |

---

## Bottom-5 Failures Analysis

### #1. Thiết bị giá trị lớn (>50 triệu)
- **Question:** Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?
- **Expected (Ground Truth):** Trên 50 triệu thuộc thẩm quyền Tổng Giám đốc (CEO) phê duyệt và cần có ít nhất 3 báo giá cạnh tranh.
- **Got (Retrieved Top Context):** Đoạn trích từ `mua_sam.md` chứa bảng phân quyền hạn mức mua sắm.
- **Worst metric:** `context_precision` (0.6500)
- **Error Tree:** Output đúng nội dung nhưng format thô → Context đúng → Query OK → **Root cause:** Khi trích xuất bảng hạn mức mua sắm, các chunk lân cận cũng có điểm liên quan cao dẫn đến nhiễu nhẹ ở vị trí top rank.
- **Suggested fix:** Cải thiện Prompt System Instructions trong LLM generation để ép LLM trả lời trực diện vào câu hỏi với định dạng ngắn gọn 1-2 câu.

---

### #2. Nhân viên tạm ứng tiền và chậm thanh toán
- **Question:** Nhân viên tạm ứng 15 triệu, sau 20 ngày mới thanh toán. Bị phạt bao nhiêu?
- **Expected (Ground Truth):** Thời hạn thanh toán tạm ứng là 14 ngày làm việc. Quá hạn 6 ngày bị tính lãi phạt 0.05%/ngày trên số tiền tạm ứng.
- **Got (Retrieved Top Context):** `tam_ung.md` chứa quy định thời hạn hoàn ứng 14 ngày và mức phạt chậm nộp.
- **Worst metric:** `faithfulness` (0.7000)
- **Error Tree:** Output thiếu phép tính số học ngày quá hạn → Context đúng → Query OK → **Root cause:** Bài toán suy luận số học đa bước (multi-hop reasoning & math computation: lấy 20 ngày trừ 14 ngày = 6 ngày quá hạn, nhân với lãi suất phạt).
- **Suggested fix:** Áp dụng Chain-of-Thought (CoT) Prompting hoặc Tool-augmented RAG (Python REPL calculator) khi phát hiện câu hỏi chứa từ khóa tính toán số liệu tài chính.

---

### #3. Độ dài mật khẩu tối thiểu
- **Question:** Mật khẩu phải có tối thiểu bao nhiêu ký tự?
- **Expected (Ground Truth):** Theo chính sách hiện hành (v2.0), mật khẩu phải có tối thiểu 12 ký tự (v1.0 cũ là 8 ký tự).
- **Got (Retrieved Top Context):** Cả `mat_khau_v2.md` (12 ký tự) và `mat_khau_v1.md` (8 ký tự).
- **Worst metric:** `faithfulness` (0.7000)
- **Error Tree:** Output có xung đột thời gian giữa 2 phiên bản → Context chứa tài liệu cũ + mới → Query OK → **Root cause:** Lỗi Temporal Conflict (Xung đột phiên bản). Cả 2 tài liệu v1.0 và v2.0 đều có độ tương đồng embedding cao với câu hỏi.
- **Suggested fix:** Sử dụng Metadata Filtering dựa trên trường `metadata["status"] != "deprecated"` hoặc gán trọng số thời gian (`effective_date` / `version`) vào giai đoạn Reranking để ưu tiên phiên bản v2.0.

---

### #4. Lương thử việc cấp bậc Junior
- **Question:** Lương thử việc của nhân viên Junior mức cao nhất là bao nhiêu?
- **Expected (Ground Truth):** Lương Junior là 12-20 triệu VNĐ/tháng, lương thử việc 85% nên mức cao nhất là 17.000.000 VNĐ (85% của 20 triệu).
- **Got (Retrieved Top Context):** Đoạn trích bảng lương cấp bậc `bang_luong_2024.md` và điều khoản lương thử việc 85%.
- **Worst metric:** `context_precision` (0.7077)
- **Error Tree:** Output cần kết nối giữa bảng lương và tỷ lệ thử việc → Context chứa 2 chunk riêng biệt → Query OK → **Root cause:** Tìm kiếm ngữ nghĩa cần gom cụm thông tin giữa bảng lương và chính sách thử việc.
- **Suggested fix:** Nâng cấp chiến lược Chunking sang Hierarchical Chunking hoặc HyQA Enrichment để tạo cầu nối ngữ nghĩa (Semantic Bridge) giữa thực thể "bảng lương Junior" và "tỷ lệ 85%".

---

### #5. Phụ cấp ăn trưa hàng tháng
- **Question:** Phụ cấp ăn trưa hàng tháng là bao nhiêu?
- **Expected (Ground Truth):** Phụ cấp ăn trưa là 1.000.000 VNĐ/tháng, chi trả cùng kỳ lương.
- **Got (Retrieved Top Context):** `phu_cap.md` và `thu_viec.md` (phụ cấp ăn trưa áp dụng từ ngày đầu).
- **Worst metric:** `faithfulness` (0.7556)
- **Error Tree:** Output trả lời đúng nhưng trích dẫn thêm chính sách áp dụng trong thử việc → Context chính xác 100% → Query OK → **Root cause:** Context chứa nhiều thông tin phụ bổ trợ.
- **Suggested fix:** Tinh chỉnh prompt generation để chỉ trích xuất đúng con số được hỏi mà không mở rộng thêm các điều kiện bổ trợ.

---

## Case Study (Trình bày chuyên sâu)

**Câu hỏi:** *"Mentor và buddy của nhân viên mới có thể là cùng một người không? Quản lý trực tiếp có thể làm mentor không?"*

### Error Tree Walkthrough:
1. **Output đúng?** → Đạt yêu cầu nội dung: Chỉ ra rõ Buddy hỗ trợ văn hóa 3 tháng đầu, Mentor hỗ trợ chuyên môn 6 tháng đầu. Mentor và Buddy bắt buộc phải là 2 người khác nhau; Quản lý trực tiếp không được làm Mentor hoặc Buddy.
2. **Context đúng?** → Rất chính xác: Module 2 (Hybrid Search) kết hợp Module 3 (CrossEncoder) đã đẩy đoạn văn chứa quy tắc phân biệt trong `mentor_buddy.md` lên vị trí Rank 1 với `rerank_score > 0.85`.
3. **Query Rewrite OK?** → Tìm kiếm đúng từ khóa phủ định và đa ý ("cùng một người", "quản lý trực tiếp").
4. **Fix ở bước:** Tối ưu hóa prompt generation để phân tách câu trả lời thành 2 ý gạch đầu dòng rõ ràng:
   * (1) *Không thể là cùng một người (Mentor và Buddy phải là 2 người khác nhau).*
   * (2) *Quản lý trực tiếp không được phép làm Mentor hoặc Buddy.*

---

## Nếu có thêm 1 giờ, tôi sẽ tối ưu:
1. **Metadata Filtering theo Versioning:** Thêm bộ lọc metadata thời gian thực để loại bỏ triệt để các tài liệu `status: "deprecated"` (như `nghi_phep_nam_v2023.md`, `mat_khau_v1.md`).
2. **Multi-Hop Query Expansion & Sub-Query Decomposition:** Tách các câu hỏi phức tạp (chứa 2 vế câu hỏi hoặc tính toán số liệu) thành các sub-queries độc lập trước khi truy vấn vector database.
3. **FlashRank Onnx Quantized Reranker:** Tích hợp mô hình reranker lượng tử hóa để giảm độ trễ rerank từ hàng giây xuống dưới 10ms mà không làm giảm độ chính xác.
