"""
Test đơn vị cho detect_specialty() của cổng G5 (tools/run_g5_auto.py).

Bug nghiêm trọng nhất phát hiện trong dự án (2026-07-02): logic "khớp từ khóa
ĐẦU TIÊN thắng" khiến 1 đề tài về bệnh thận mạn bị gán nhầm chuyên khoa tim
mạch vì từ khóa dùng chung "sglt2" khai báo trước trong dict. Guardrail cấu
trúc PASS bình thường vì đây là lỗi NỘI DUNG, không phải lỗi cấu trúc — chỉ
bộ test này (so nội dung sinh ra với chủ đề) mới bắt được loại bug đó.
"""
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g5_auto import _SPECIALTY_KEYWORDS, detect_specialty  # noqa: E402


ALL_SPECIALTIES = list(_SPECIALTY_KEYWORDS.keys())


class TestIsolatedSpecialtyDetection:
    """Mỗi chuyên khoa PHẢI tự thắng khi chủ đề chỉ chứa từ khóa của riêng nó."""

    def test_all_specialties_are_reachable(self):
        """Không chuyên khoa nào bị 'từ khóa dùng chung của chuyên khoa khác' lấn át vĩnh viễn."""
        for specialty, keywords in _SPECIALTY_KEYWORDS.items():
            longest_kw = max(keywords, key=lambda k: len(k.split()))
            topic = f"Nghiên cứu về {longest_kw} ở bệnh nhân ngoại trú"
            assert detect_specialty(topic) == specialty, (
                f"Chuyên khoa '{specialty}' không tự thắng được với từ khóa "
                f"đặc hiệu nhất của chính nó ({longest_kw!r})"
            )

    def test_cardiology_hf(self):
        assert detect_specialty("Nghiên cứu về suy tim HFpEF ở người cao tuổi") == "cardiology_hf"

    def test_metabolic_diabetes(self):
        assert detect_specialty("Kiểm soát đường huyết ở bệnh nhân tiền đái tháo đường") == "metabolic_diabetes"

    def test_nephrology_ckd(self):
        assert detect_specialty("Tiến triển bệnh thận mạn (CKD) giai đoạn G3-G4") == "nephrology_ckd"

    def test_pulmonology(self):
        assert detect_specialty("Kiểm soát đợt cấp COPD ở bệnh nhân ngoại trú") == "pulmonology_copd_asthma"

    def test_neurology_stroke(self):
        assert detect_specialty("Dự phòng tái phát đột quỵ nhồi máu não") == "neurology_stroke"

    def test_musculoskeletal_pain(self):
        assert detect_specialty("Quản lý đau lưng mạn tính bằng vật lý trị liệu") == "musculoskeletal_pain"

    def test_psychiatry(self):
        assert detect_specialty("Điều trị trầm cảm kèm lo âu ở người trưởng thành") == "psychiatry_depression_anxiety"

    def test_gastroenterology(self):
        assert detect_specialty("Theo dõi xơ gan mất bù bằng thang Child-Pugh") == "gastroenterology"

    def test_no_match_falls_back_to_generic(self):
        assert detect_specialty("Đánh giá hiệu quả một loại vitamin tổng hợp") == "generic"

    def test_empty_or_none_falls_back_to_generic(self):
        assert detect_specialty("") == "generic"
        assert detect_specialty(None) == "generic"


class TestSpecificityScoring:
    """
    Bug đã sửa: chủ đề nhắc "SGLT2" (từ khóa dùng chung, khai trong cardiology_hf)
    CÙNG với "bệnh thận mạn"/"CKD" (từ khóa đặc hiệu nephrology_ckd) phải chọn
    nephrology_ckd — vì cụm từ đặc hiệu dài hơn phải thắng từ khóa ngắn dùng chung,
    KHÔNG phải "khớp trước trong dict thắng" như logic cũ.
    """

    def test_regression_sglt2_ckd_topic_picks_nephrology(self):
        topic = (
            "Hiệu quả ức chế SGLT2 trong làm chậm tiến triển bệnh thận mạn "
            "(CKD) ở bệnh nhân đái tháo đường týp 2"
        )
        assert detect_specialty(topic) == "nephrology_ckd"

    def test_sglt2_alone_still_picks_cardiology(self):
        """Không có tín hiệu chuyên khoa khác → sglt2 đơn độc vẫn hợp lý về tim mạch."""
        topic = "Hiệu quả thuốc ức chế SGLT2 trên tái nhập viện do suy tim ở bệnh nhân HFpEF"
        assert detect_specialty(topic) == "cardiology_hf"

    def test_no_hidden_bias_toward_declaration_order(self):
        """
        Mọi cặp chuyên khoa: khi B có từ khóa DÀI HƠN (đặc hiệu hơn) xuất hiện
        trong chủ đề, B phải thắng A dù A được khai báo TRƯỚC B trong dict.
        Vét cạn C(n,2) cặp bằng từ khóa dài nhất của mỗi chuyên khoa.
        """
        for i, sp_a in enumerate(ALL_SPECIALTIES):
            for sp_b in ALL_SPECIALTIES[i + 1:]:
                kw_b = max(_SPECIALTY_KEYWORDS[sp_b], key=lambda k: len(k.split()))
                if len(kw_b.split()) < 2:
                    continue  # chỉ kiểm khi B có cụm từ đặc hiệu thật sự (>=2 từ)
                kw_a_short = min(_SPECIALTY_KEYWORDS[sp_a], key=lambda k: len(k.split()))
                if len(kw_a_short.split()) > 1:
                    continue  # cần A có ít nhất 1 từ khóa NGẮN (1 từ) để test có ý nghĩa
                topic = f"{kw_a_short} và {kw_b}"
                result = detect_specialty(topic)
                assert result == sp_b, (
                    f"'{kw_b}' (đặc hiệu, {sp_b}) lẽ ra phải thắng '{kw_a_short}' "
                    f"(ngắn, {sp_a}) nhưng kết quả là {result!r}"
                )
