import sys
from pathlib import Path

# ruff: noqa: E402,E501

# VÁ 15/08/2026 (chốt kiem_tuong_thich_da_nen bắt được — 🔴 duy nhất toàn kho):
# ROOT ghi cứng C:\Users\Admin\... nên tool CHƯA TỪNG chạy được trên Mac — đúng
# họ lỗi ensure_strict_source/run_retraction_and_med_safety đã vá 12-13/08.
# VÁ vòng 27 (2026-09-06): bản vá 15/08 thay MỘT hardcode (path Windows tuyệt
# đối) bằng MỘT hardcode khác — tính ROOT (thư mục CHA của repo) rồi ghép cứng
# chuỗi "medical-ebm-automation" để suy ngược lại vị trí repo, chỉ đúng NẾU
# thư mục checkout thực sự tên đúng y hệt vậy (worktree/clone tên khác sẽ
# ModuleNotFoundError khi import app.reports.evidence_workbench). Dùng đúng
# quy ước bất biến-tên mà tools/verify_evidence_surveillance_deployment.py và
# tools/verify_clinical_evidence_agent_standards.py đã dùng: REPO trước
# (không phụ thuộc tên thư mục), ROOT suy từ REPO (không phải ngược lại).
# VÁ 07/09/2026: `ROOT = REPO.parent` giả định REPO nằm LỒNG bên trong workspace
# gốc — đúng máy thật, SAI trên phiên cloud (REPO là ANH EM của workspace gốc
# dưới cùng thư mục cha). Dùng resolve_workspace_root() — xem
# tools/_workspace_root.py để biết chi tiết.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _workspace_root import resolve_workspace_root  # noqa: E402

ROOT = resolve_workspace_root(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from app.reports.evidence_workbench import TEMPLATE, render_html

HTML_PATH = ROOT / "EBM-Dashboards" / "WebDashboard_EBM_VanDeCuThe_MachMauNao_20260723.html"


DATA = {
    "meta": {
        "eyebrow": "Cập nhật chứng cứ · Thần kinh mạch máu",
        "question": "Tiếp cận chẩn đoán và điều trị bệnh lý mạch máu não",
        "pico": {
            "P": "Người bệnh nghi ngờ hoặc đã xác định bệnh lý mạch máu não",
            "I": "Chẩn đoán nhanh, tái tưới máu, kiểm soát xuất huyết, dự phòng tái phát",
            "C": "Thực hành chưa phân tầng cơ chế bệnh",
            "O": "Giảm tử vong, tàn phế, tái phát và biến cố chảy máu",
        },
        "updated": "2026-07-23",
    },
    "summary": {
        "conclusion": (
            "Gói cập nhật gồm tám nhóm chứng cứ và hướng dẫn chính cho nhồi máu não cấp, "
            "dự phòng tái phát, xuất huyết não, xuất huyết dưới nhện, dự phòng nguyên phát, "
            "rung nhĩ, huyết khối tĩnh mạch não và thai kỳ/hậu sản."
        ),
        "doNow": [
            "Ghi thời điểm cuối cùng còn bình thường, đo đường huyết, đánh giá mức độ thiếu sót thần kinh và chụp não ngay khi nghi đột quỵ.",
            "Chụp mạch đầu-cổ nếu nghi tắc mạch lớn hoặc cần đánh giá hệ động mạch não.",
            "Tìm cơ chế bệnh sau giai đoạn cấp để chọn thuốc chống huyết khối hoặc can thiệp mạch phù hợp.",
            "Kiểm soát huyết áp, mỡ máu, đường huyết, thuốc lá và rung nhĩ để dự phòng tái phát.",
        ],
        "dontDo": [
            "Không dùng aspirin thay thế kháng đông khi rung nhĩ có chỉ định kháng đông.",
            "Không dùng kháng kết tập kép dài hạn thường quy sau đột quỵ hoặc cơn thiếu máu não thoáng qua.",
            "Không dùng kháng đông kinh nghiệm cho nhồi máu não không rõ nguồn thuyên tắc khi chưa có chỉ định rõ.",
            "Không trì hoãn cấp cứu đột quỵ vì chờ đủ xét nghiệm thường quy.",
        ],
        "redFlags": [
            "Yếu liệt, nói khó hoặc mất thị lực đột ngột.",
            "Đau đầu sét đánh hoặc đau đầu dữ dội nhất đời.",
            "Rối loạn ý thức, co giật mới hoặc đang dùng kháng đông.",
            "Thai kỳ hoặc hậu sản kèm đau đầu, tăng huyết áp, co giật hoặc dấu thần kinh khu trú.",
        ],
    },
    "items": [
        {
            "id": "ITEM-01",
            "title": "Nhồi máu não cấp: tái tưới máu và xử trí ban đầu",
            "source": "AHA/ASA",
            "org": "AHA/ASA",
            "dateVersion": "2026",
            "design": "Guideline",
            "population": "Nhồi máu não cấp",
            "pico": {
                "P": ["Người bệnh thiếu sót thần kinh cấp nghi nhồi máu não", "match"],
                "I": ["Chụp não, chụp mạch nhanh, tiêu sợi huyết phù hợp và lấy huyết khối khi tắc mạch lớn", "match"],
                "C": ["Không tái tưới máu hoặc chậm chuyển tuyến", "match"],
                "O": ["Cải thiện kết cục chức năng nếu chọn đúng bệnh nhân và đúng thời gian", "match"],
            },
            "effectText": "Cửa sổ tiêu sợi huyết thường là bốn giờ rưỡi; lấy huyết khối có thể đến hai mươi bốn giờ ở ca chọn lọc.",
            "gradeSource": "Khuyến cáo hướng dẫn AHA/ASA 2026",
            "gradeLevel": "na",
            "decision": "apply",
            "groups": ["tim-mach", "cao-tuoi"],
            "action": "Ghi thời điểm cuối cùng còn bình thường, đo đường huyết, đánh giá mức độ thiếu sót thần kinh, chụp não và chụp mạch nếu nghi tắc mạch lớn.",
            "monitoring": "Theo dõi huyết áp, xuất huyết chuyển dạng, phù não và biến chứng thủ thuật.",
            "vn": "Đối chiếu phác đồ đột quỵ tại đơn vị, năng lực chụp mạch, tiêu sợi huyết và chuyển tuyến.",
            "references": ["AHA/ASA. 2026 AIS Guideline. PMID 41582814. DOI:10.1161/STR.0000000000000513."],
            "doi": "10.1161/STR.0000000000000513",
        },
        {
            "id": "ITEM-02",
            "title": "Dự phòng tái phát sau đột quỵ hoặc thiếu máu não thoáng qua",
            "source": "AHA/ASA",
            "org": "AHA/ASA",
            "dateVersion": "2021",
            "design": "Guideline",
            "population": "Sau đột quỵ",
            "pico": {
                "P": ["Người bệnh sau đột quỵ hoặc thiếu máu não thoáng qua", "match"],
                "I": ["Kiểm soát yếu tố nguy cơ và điều trị theo cơ chế bệnh", "match"],
                "C": ["Điều trị chung không phân tầng cơ chế", "match"],
                "O": ["Giảm tái phát đột quỵ và biến cố tim mạch", "match"],
            },
            "effectText": "Mục tiêu thường dùng: huyết áp dưới 130/80 mmHg nếu dung nạp; mỡ máu xấu dưới 70 mg/dL ở bệnh do xơ vữa.",
            "gradeSource": "Khuyến cáo hướng dẫn AHA/ASA 2021",
            "gradeLevel": "na",
            "decision": "apply",
            "groups": ["tim-mach", "dtd", "ckd"],
            "action": "Tìm cơ chế bệnh; kiểm soát huyết áp, mỡ máu, đường huyết, thuốc lá, rung nhĩ và lối sống.",
            "monitoring": "Theo dõi tuân thủ, huyết áp tại nhà, mỡ máu, đường huyết, chức năng thận và nguy cơ chảy máu.",
            "vn": "Cá thể hóa theo thuốc sẵn có, chi phí, bảo hiểm y tế và nguy cơ chảy máu.",
            "references": ["AHA/ASA. 2021 Secondary Prevention Guideline. PMID 34024117. DOI:10.1161/STR.0000000000000375."],
            "doi": "10.1161/STR.0000000000000375",
        },
        {
            "id": "ITEM-03",
            "title": "Xuất huyết não tự phát: kiểm soát huyết áp và đảo ngược kháng đông",
            "source": "AHA/ASA",
            "org": "AHA/ASA",
            "dateVersion": "2022",
            "design": "Guideline",
            "population": "Xuất huyết não",
            "pico": {
                "P": ["Người bệnh xuất huyết não tự phát", "match"],
                "I": ["Kiểm soát huyết áp êm và bền, đảo ngược kháng đông, hội chẩn ngoại thần kinh", "match"],
                "C": ["Chậm đảo ngược hoặc dao động huyết áp lớn", "match"],
                "O": ["Giảm lan rộng tụ máu và biến chứng", "match"],
            },
            "effectText": "Không dùng thang điểm tiên lượng nặng như lý do duy nhất để giới hạn điều trị.",
            "gradeSource": "Khuyến cáo hướng dẫn AHA/ASA 2022",
            "gradeLevel": "na",
            "decision": "apply",
            "groups": ["tim-mach", "cao-tuoi", "ckd"],
            "action": "Chụp não xác nhận xuất huyết, kiểm soát huyết áp, đảo ngược kháng đông sớm và đánh giá tụ máu vùng nguy hiểm hoặc chèn ép.",
            "monitoring": "Theo dõi tri giác, huyết áp, lan rộng tụ máu, não úng thủy và rối loạn đông máu.",
            "vn": "Cần đường chuyển tuyến ngoại thần kinh và thuốc đảo ngược kháng đông theo danh mục đơn vị.",
            "references": ["AHA/ASA. 2022 Spontaneous ICH Guideline. PMID 35579034. DOI:10.1161/STR.0000000000000407."],
            "doi": "10.1161/STR.0000000000000407",
        },
        {
            "id": "ITEM-04",
            "title": "Xuất huyết dưới nhện do phình mạch",
            "source": "AHA/ASA",
            "org": "AHA/ASA",
            "dateVersion": "2023",
            "design": "Guideline",
            "population": "Đau đầu sét đánh",
            "pico": {
                "P": ["Người bệnh đau đầu sét đánh hoặc nghi xuất huyết dưới nhện", "match"],
                "I": ["Chụp não sớm, chụp mạch, bít phình, nimodipine và theo dõi co thắt mạch", "match"],
                "C": ["Chẩn đoán muộn hoặc chưa xử trí phình mạch", "match"],
                "O": ["Giảm tái vỡ và thiếu máu não muộn", "match"],
            },
            "effectText": "Đau đầu sét đánh cần loại trừ xuất huyết dưới nhện dù triệu chứng thoáng qua.",
            "gradeSource": "Khuyến cáo hướng dẫn AHA/ASA 2023",
            "gradeLevel": "na",
            "decision": "apply",
            "groups": [],
            "action": "Chụp não sớm; nếu vẫn nghi cao dù hình ảnh ban đầu âm tính, cân nhắc chọc dò dịch não tủy hoặc chụp mạch; chuyển trung tâm thần kinh mạch máu.",
            "monitoring": "Theo dõi tái vỡ, não úng thủy, co thắt mạch và thiếu máu não muộn.",
            "vn": "Đối chiếu khả năng chụp mạch, can thiệp nội mạch và ngoại thần kinh tại khu vực.",
            "references": ["AHA/ASA. 2023 aSAH Guideline. PMID 37212182. DOI:10.1161/STR.0000000000000436."],
            "doi": "10.1161/STR.0000000000000436",
        },
        {
            "id": "ITEM-05",
            "title": "Dự phòng nguyên phát đột quỵ",
            "source": "AHA/ASA",
            "org": "AHA/ASA",
            "dateVersion": "2024",
            "design": "Guideline",
            "population": "Người có nguy cơ",
            "pico": {
                "P": ["Người chưa từng đột quỵ nhưng có yếu tố nguy cơ", "match"],
                "I": ["Kiểm soát huyết áp, mỡ máu, đường huyết, hút thuốc, lối sống và yếu tố đặc thù giới", "match"],
                "C": ["Chỉ điều trị sau biến cố", "match"],
                "O": ["Giảm đột quỵ lần đầu", "match"],
            },
            "effectText": "Tăng huyết áp là yếu tố nguy cơ quan trọng nhất có thể điều chỉnh.",
            "gradeSource": "Khuyến cáo hướng dẫn AHA/ASA 2024",
            "gradeLevel": "na",
            "decision": "apply",
            "groups": ["tim-mach", "dtd", "ckd"],
            "action": "Phân tầng nguy cơ và can thiệp sớm: huyết áp, mỡ máu, đường huyết, thuốc lá, cân nặng, vận động và giấc ngủ.",
            "monitoring": "Theo dõi huyết áp, mỡ máu, đường huyết, cân nặng, thuốc lá và ngưng thở khi ngủ.",
            "vn": "Ưu tiên các can thiệp có thể thực hiện tại ngoại trú và theo dõi dài hạn.",
            "references": ["AHA/ASA. 2024 Primary Prevention of Stroke Guideline. PMID 39429201. DOI:10.1161/STR.0000000000000475."],
            "doi": "10.1161/STR.0000000000000475",
        },
        {
            "id": "ITEM-06",
            "title": "Rung nhĩ: kháng đông phòng đột quỵ",
            "source": "ACC/AHA/ACCP/HRS",
            "org": "ACC/AHA",
            "dateVersion": "2023",
            "design": "Guideline",
            "population": "Rung nhĩ",
            "pico": {
                "P": ["Người bệnh rung nhĩ có nguy cơ thuyên tắc", "match"],
                "I": ["Kháng đông đường uống trực tiếp hoặc warfarin theo chỉ định", "match"],
                "C": ["Aspirin đơn thuần", "match"],
                "O": ["Giảm đột quỵ do thuyên tắc từ tim", "match"],
            },
            "effectText": "Kháng đông đường uống trực tiếp thường ưu tiên hơn warfarin nếu không có van cơ học hoặc hẹp van hai lá trung bình-nặng.",
            "gradeSource": "Khuyến cáo hướng dẫn rung nhĩ 2023",
            "gradeLevel": "na",
            "decision": "apply",
            "groups": ["tim-mach", "cao-tuoi", "ckd"],
            "action": "Đánh giá chỉ định kháng đông; chỉnh liều theo chức năng thận, tuổi, cân nặng và tương tác thuốc.",
            "monitoring": "Theo dõi chảy máu, chức năng thận, huyết sắc tố và tương tác thuốc; không dùng aspirin thay kháng đông.",
            "vn": "Rà soát khả năng tuân thủ, chi phí và tương tác thuốc trong từng bệnh nhân.",
            "references": ["ACC/AHA/ACCP/HRS. 2023 AF Guideline. PMID 38033089. DOI:10.1161/CIR.0000000000001193."],
            "doi": "10.1161/CIR.0000000000001193",
        },
        {
            "id": "ITEM-07",
            "title": "Huyết khối tĩnh mạch não",
            "source": "European Stroke Organization",
            "org": "ESO",
            "dateVersion": "2017",
            "design": "Guideline",
            "population": "Huyết khối tĩnh mạch não",
            "pico": {
                "P": ["Đau đầu bán cấp, co giật, phù gai thị hoặc dấu thần kinh dao động", "match"],
                "I": ["Chụp hệ tĩnh mạch não và kháng đông bằng heparin", "match"],
                "C": ["Chẩn đoán nhầm đau đầu thông thường", "match"],
                "O": ["Giảm tiến triển huyết khối và biến chứng", "match"],
            },
            "effectText": "Có thể kháng đông kể cả khi có xuất huyết tĩnh mạch nhỏ nếu không có chống chỉ định đặc biệt.",
            "gradeSource": "Khuyến cáo European Stroke Organization 2017",
            "gradeLevel": "na",
            "decision": "apply",
            "groups": ["da-thuoc"],
            "action": "Nghi huyết khối tĩnh mạch não ở người hậu sản, dùng nội tiết hoặc có tăng đông kèm đau đầu-co giật; chụp hệ tĩnh mạch não và kháng đông phù hợp.",
            "monitoring": "Theo dõi co giật, tăng áp lực nội sọ, xuất huyết và nguyên nhân tăng đông.",
            "vn": "Phối hợp thần kinh, sản khoa hoặc huyết học khi có thai kỳ, hậu sản hoặc rối loạn đông máu.",
            "references": ["European Stroke Organization. CVT Guideline. PMID 28833980. DOI:10.1177/2396987317719364."],
            "doi": "10.1177/2396987317719364",
        },
        {
            "id": "ITEM-08",
            "title": "Đột quỵ trong thai kỳ và hậu sản",
            "source": "AHA",
            "org": "AHA",
            "dateVersion": "2026",
            "design": "Scientific Statement",
            "population": "Thai kỳ và hậu sản",
            "pico": {
                "P": ["Thai phụ hoặc người hậu sản có triệu chứng thần kinh cấp", "match"],
                "I": ["Không trì hoãn đánh giá đột quỵ; kiểm soát tăng huyết áp; chọn thuốc an toàn thai kỳ", "match"],
                "C": ["Quy triệu chứng cho đau đầu lành tính", "match"],
                "O": ["Giảm tử vong mẹ và biến chứng thần kinh", "match"],
            },
            "effectText": "Thai kỳ và hậu sản có nguy cơ đặc thù: tiền sản giật, sản giật, tăng đông, huyết khối tĩnh mạch não và bệnh tim.",
            "gradeSource": "Tuyên bố khoa học AHA 2026",
            "gradeLevel": "na",
            "decision": "apply",
            "groups": [],
            "action": "Xử trí như cấp cứu đột quỵ; phối hợp sản khoa, thần kinh và hồi sức; ưu tiên heparin trọng lượng phân tử thấp khi cần kháng đông trong thai kỳ.",
            "monitoring": "Theo dõi huyết áp, co giật, dấu thần kinh, xuất huyết và an toàn mẹ-thai.",
            "vn": "Luôn phối hợp sản khoa và thần kinh; không trì hoãn hình ảnh học khi nghi đột quỵ.",
            "references": ["AHA. Maternal Stroke in Pregnancy and Postpartum. PMID 41603019. DOI:10.1161/STR.0000000000000514."],
            "doi": "10.1161/STR.0000000000000514",
        },
    ],
}


def main() -> None:
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(render_html(DATA, TEMPLATE), encoding="utf-8", newline="\n")
    print(HTML_PATH)


if __name__ == "__main__":
    main()
