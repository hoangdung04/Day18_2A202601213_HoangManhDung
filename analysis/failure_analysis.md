# Failure Analysis — Lab 18: Production RAG

**Tác giả:** Hoàng Mạnh Dũng  
**Module phụ trách:** M1 (Chunking) · M2 (Search) · M3 (Reranking) · M4 (Evaluation) · M5 (Enrichment)

---

## RAGAS Scores

| Metric | Naive Baseline | Production Pipeline | Δ | Đánh giá |
|--------|---------------|---------------------|---|----------|
| **Faithfulness** | 1.0000 | 1.0000 | +0.0000 | ✅ Đạt chuẩn tuyệt đối (≥0.85) |
| **Answer Relevancy** | 0.8948 | 0.8476 | -0.0472 | ✅ Đạt chuẩn cao (≥0.75) |
| **Context Precision** | 0.9234 | 0.8740 | -0.0494 | ✅ Đạt chuẩn cao (≥0.75) |
| **Context Recall** | 0.9490 | 0.8951 | -0.0539 | ✅ Đạt chuẩn cao (≥0.75) |

---

## Bottom-5 Failures Analysis

### #1. Thiết bị giá trị lớn (>50 triệu)
- **Question:** Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?
- **Expected (Ground Truth):** Trên 50 triệu thuộc thẩm quyền Tổng Giám đốc (CEO) phê duyệt và cần có ít nhất 3 báo giá cạnh tranh.
- **Got (Retrieved Top Context):** Đoạn trích từ `mua_sam.md` chứa bảng phân quyền hạn mức mua sắm.
- **Worst metric:** `answer_relevancy` (0.6500)
- **Error Tree:** Output đúng nội dung nhưng format thô → Context đúng → Query OK → **Root cause:** Khi không sử dụng LLM generation mà lấy context trực tiếp, câu trả lời chứa toàn bộ bảng markdown thay vì trích xuất cô đọng đúng chủ thể "Tổng Giám đốc (CEO)".
- **Suggested fix:** Cải thiện Prompt System Instructions trong LLM generation để ép LLM trả lời trực diện vào câu hỏi với định dạng ngắn gọn 1-2 câu.

---

### #2. Lương thử việc cấp bậc Junior
- **Question:** Lương thử việc của nhân viên Junior mức cao nhất là bao nhiêu?
- **Expected (Ground Truth):** Lương Junior là 12-20 triệu VNĐ/tháng, lương thử việc 85% nên mức cao nhất là 17.000.000 VNĐ (85% của 20 triệu).
- **Got (Retrieved Top Context):** Đoạn trích bảng lương cấp bậc `bang_luong_2024.md` và điều khoản lương thử việc 85%.
- **Worst metric:** `answer_relevancy` (0.6577)
- **Error Tree:** Output chứa dữ liệu gốc nhưng thiếu phép tính số học → Context đúng (chứa cả 2 chunk) → Query OK → **Root cause:** Bài toán suy luận số học đa bước (multi-hop reasoning & math computation: lấy trần khung Junior 20tr nhân với 85%).
- **Suggested fix:** Áp dụng Chain-of-Thought (CoT) Prompting hoặc Tool-augmented RAG (Python REPL calculator) khi phát hiện câu hỏi chứa từ khóa tính toán số liệu tài chính.

---

### #3. Chu kỳ thay đổi mật khẩu
- **Question:** Bao lâu phải đổi mật khẩu một lần?
- **Expected (Ground Truth):** Theo chính sách hiện hành (v2.0), mật khẩu phải được thay đổi mỗi 120 ngày. Chính sách cũ yêu cầu 90 ngày nhưng đã bị thay thế.
- **Got (Retrieved Top Context):** Cả `mat_khau_v2.md` (120 ngày) và `mat_khau_v1.md` (90 ngày).
- **Worst metric:** `answer_relevancy` (0.6833)
- **Error Tree:** Output có xung đột thời gian → Context chứa tài liệu cũ + mới → Query OK → **Root cause:** Lỗi Temporal Conflict (Xung đột phiên bản). Cả 2 tài liệu v1.0 và v2.0 đều có độ tương đồng embedding cao với câu hỏi.
- **Suggested fix:** Sử dụng Metadata Filtering dựa trên trường `metadata["status"] != "deprecated"` hoặc gán trọng số thời gian (`effective_date` / `version`) vào giai đoạn Reranking để ưu tiên phiên bản v2.0.

---

### #4. Cấp độ phân loại thông tin lương
- **Question:** Thông tin lương thuộc cấp độ phân loại dữ liệu nào?
- **Expected (Ground Truth):** Thông tin lương là dữ liệu Bí mật (Cấp độ 3), cấm chia sẻ với đồng nghiệp.
- **Got (Retrieved Top Context):** `ky_luong.md` (chứa điều khoản thông tin lương là Bí mật) và `phan_loai_du_lieu.md`.
- **Worst metric:** `answer_relevancy` (0.7346)
- **Error Tree:** Output trích đoạn quy chế chi trả lương → Context đúng → Query OK → **Root cause:** Câu hỏi yêu cầu kết nối chéo giữa quy chế chi trả lương (`ky_luong.md`) và chính sách phân loại an toàn thông tin (`phan_loai_du_lieu.md`).
- **Suggested fix:** Nâng cấp chiến lược Chunking sang Hierarchical Chunking hoặc HyQA Enrichment để tạo cầu nối ngữ nghĩa (Semantic Bridge) giữa thực thể "thông tin lương" và "Cấp độ 3 - Bí mật".

---

### #5. Thẩm quyền duyệt nghỉ không lương 20 ngày
- **Question:** Nghỉ phép không lương 20 ngày cần ai phê duyệt?
- **Expected (Ground Truth):** Nghỉ từ 16-30 ngày cần Tổng Giám đốc (CEO) phê duyệt.
- **Got (Retrieved Top Context):** `nghi_phep_khong_luong.md` phần quy trình phê duyệt các mốc 1-5 ngày, 6-15 ngày, 16-30 ngày.
- **Worst metric:** `answer_relevancy` (0.7574)
- **Error Tree:** Output đúng bảng quy định nhưng dài dòng → Context chính xác 100% → Query OK → **Root cause:** Retrieval lấy chính xác chunk chứa bảng điều kiện nhưng phần trả lời cần cô lập riêng mốc 20 ngày (thuộc khoảng 16-30 ngày).
- **Suggested fix:** Cải tiến prompt generation để trích xuất điều kiện logic chính xác thay vì trả về toàn bộ đoạn văn.

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
