# Reflection Cá Nhân — Lab 18: Production RAG Pipeline

**Họ và tên:** Hoàng Mạnh Dũng  
**Lớp:** AICB-K34 · **Ngày:** 18/08/2026  
**Module phụ trách:** Toàn bộ 5 Modules (M1 Chunking, M2 Search, M3 Rerank, M4 Eval, M5 Enrichment)

---

## Phần 1: Mapping Bài Giảng vào Code Thực Tế

| Concept trong Bài giảng | Module | Hàm / Lớp cụ thể | Quan sát thực tế & Đánh giá |
|---|:---:|---|---|
| **Semantic Chunking** | M1 | `chunk_semantic()` | Dùng `all-MiniLM-L6-v2` encode từng câu, tính cosine similarity với ngưỡng `threshold=0.85`. Tránh được việc cắt vụn giữa các ý liền kề so với fixed paragraph chunking. |
| **Hierarchical Chunking (Parent-Child)** | M1 | `chunk_hierarchical()` | Chia tài liệu thành parent chunks (2048 chars) và child chunks (256 chars), liên kết qua `parent_id`. Cho phép index các đơn vị nhỏ (tăng retrieval precision) nhưng khi trả về LLM có thể mở rộng ngữ cảnh đầy đủ của parent chunk. |
| **Structure-Aware Chunking** | M1 | `chunk_structure_aware()` | Dùng regex bóc tách markdown headers (`#`, `##`, `###`), giữ trọn vẹn cấu trúc bảng (table) và danh sách (bullet points) của các văn bản quy chế không bị đứt đoạn. |
| **Vietnamese Word Segmentation** | M2 | `segment_vietnamese()` | Dùng `underthesea.word_tokenize(format="text")` và thay thế `_` thành dấu cách space. Giúp BM25 tokenize chính xác các từ ghép tiếng Việt như *"nghỉ phép"*, *"thử việc"*, *"tạm ứng"*. |
| **Dense Vector Search** | M2 | `DenseSearch` (`BAAI/bge-m3` + Qdrant) | Encode embedding đa ngữ 1024 chiều, đẩy vào Qdrant Vector DB (hỗ trợ in-memory fallback), tìm kiếm vector với Cosine Distance qua API `query_points()`. |
| **Reciprocal Rank Fusion (RRF)** | M2 | `reciprocal_rank_fusion()` | Kết hợp danh sách xếp hạng từ BM25 và Dense Search theo công thức $Score(d) = \sum \frac{1}{k + rank + 1}$ ($k=60$), cân bằng giữa tìm kiếm từ khóa chính xác và tương đồng ngữ nghĩa. |
| **Cross-Encoder Reranking** | M3 | `CrossEncoderReranker` (`BAAI/bge-reranker-v2-m3`) | Đưa trực tiếp cặp `(query, document)` qua mô hình CrossEncoder để chấm điểm liên quan. Tối ưu bộ nhớ bằng module-level model caching để giảm thời gian load mô hình lặp lại. |
| **RAGAS Evaluation & Diagnostics** | M4 | `evaluate_ragas()`, `failure_analysis()` | Đánh giá 4 chỉ số vàng (*Faithfulness, Answer Relevancy, Context Precision, Context Recall*). Áp dụng Diagnostic Tree để phân loại nguyên nhân gốc rễ và đề xuất giải pháp sửa chữa. |
| **Pre-retrieval Enrichment** | M5 | `_enrich_single_call()`, `enrich_chunks()` | Tích hợp kỹ thuật Contextual Prepend (theo phong cách Anthropic), sinh câu hỏi giả định (HyQA) và trích xuất Metadata. Chế độ *combined mode* thực hiện 1 single API call cho mỗi chunk giúp tiết kiệm 75% chi phí token. |

---

## Phần 2: Khó Khăn Gặp Phải & Cách Giải Quyết

### 1. Sự cố Xung đột Thư viện Dependencies (NumPy & PyTorch)
* **Lỗi gặp phải:**
  ```text
  ModuleNotFoundError: No module named 'numpy.typing'
  ERROR: pip's dependency resolver does not currently take into account all the packages...
  ```
* **Cách debug:** Khi cài đặt đồng thời `ragas`, `sentence-transformers`, `langchain`, phiên bản `numpy 2.x` không tương thích với `scipy` và `underthesea_core`.
* **Cách giải quyết:** Cố định phiên bản `numpy==1.26.4` tương thích đa nền tảng, cài đặt đồng bộ qua `requirements.txt` và kiểm tra `import` độc lập trước khi chạy pipeline.

### 2. Sự cố Mã hóa Ký tự trên Môi trường Windows (Codepage cp1258 UnicodeEncodeError)
* **Lỗi gặp phải:**
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode characters in position 2-3: character maps to <undefined>
  ```
* **Cách debug:** Môi trường console mặc định trên Windows sử dụng bảng mã `cp1258`, khi gặp các ký tự unicode emoji (`⚠️`, `✓`, `📌`) trong log stdout sẽ khiến script bị crash đột ngột.
* **Cách giải quyết:** Bổ sung cấu hình reconfigure stdout/stderr sang UTF-8 an toàn:
  ```python
  if sys.stdout and hasattr(sys.stdout, "reconfigure"):
      sys.stdout.reconfigure(encoding="utf-8", errors="replace")
  ```

### 3. Tối ưu Bộ nhớ và Thời gian Tải Mô hình CrossEncoder (2.2GB)
* **Khó khăn:** Khởi tạo `CrossEncoderReranker` nhiều lần trong unit test khiến mỗi test phải load lại 2.2GB model weights từ ổ đĩa, gây timeout và tiêu tốn nhiều RAM.
* **Cách giải quyết:** Thiết kế Singleton / Module-level Caching (`_CROSS_ENCODER_CACHE`) trong `m3_rerank.py`, giúp mô hình chỉ nạp vào RAM một lần duy nhất.

---

## Phần 3: Action Plan Áp Dụng vào Dự Án Cá Nhân

```markdown
## Project: Hệ thống Trợ lý Pháp lý & Quy chế Doanh nghiệp Thông minh (Enterprise Policy Assistant)

### Hiện tại
- RAG pipeline hiện tại: Naive RAG (Simple character text splitter + OpenAI text-embedding-3-small + Dense-only search).
- Known issues:
  1. Thường xuyên nhầm lẫn giữa phiên bản quy chế mới và cũ khi có tài liệu cập nhật.
  2. Bỏ sót các quy định dạng bảng biểu, điều khoản chia nhỏ hoặc các câu hỏi chứa phủ định ("không được phép", "ngoại trừ").
  3. Chi phí gọi LLM cao khi ném toàn bộ văn bản dài vào prompt context.

### Plan áp dụng kiến trúc Production RAG
1. [x] **Chunking Strategy:** Chuyển sang kết hợp **Structure-Aware Chunking** (bảo vệ cấu trúc văn bản pháp luật, chương, điều, khoản) và **Hierarchical Chunking** (lưu trữ parent chunk 2048 ký tự để đảm bảo ngữ cảnh toàn diện khi trích xuất).
2. [x] **Search Strategy:** Áp dụng **Hybrid Search** kết hợp `BM25Okapi` (qua `underthesea` tách từ tiếng Việt) và `BAAI/bge-m3` qua Qdrant, dung hợp điểm số bằng **RRF** ($k=60$).
3. [x] **Reranking:** Tích hợp `BAAI/bge-reranker-v2-m3` để chọn lọc top-20 xuống top-3 ngữ cảnh tinh gọn nhất trước khi đưa vào LLM.
4. [x] **Enrichment:** Sử dụng **Contextual Prepend** để gắn tên tài liệu và điều khoản cha vào đầu mỗi chunk; tự động sinh metadata `version`, `effective_date`, `status` để lọc tài liệu hết hiệu lực.
5. [x] **Evaluation:** Xây dựng bộ test set benchmark tự động bằng **RAGAS** chạy định kỳ trong CI/CD pipeline để giám sát chất lượng retrieval & generation.

### Timeline Triển khai
- **Tuần 1:** Chuẩn hóa dữ liệu corpus, xây dựng Module Structure-aware Chunking và thiết lập Vector DB Qdrant.
- **Tuần 2:** Triển khai Hybrid Search (BM25 tiếng Việt + Dense) và tối ưu hóa bộ tham số RRF.
- **Tuần 3:** Tích hợp CrossEncoder Reranker, đo lường latency và áp dụng mô hình lượng tử hóa FlashRank.
- **Tuần 4:** Thiết lập quy trình đánh giá RAGAS, viết dashboard giám sát chất lượng và triển khai Production.
```
