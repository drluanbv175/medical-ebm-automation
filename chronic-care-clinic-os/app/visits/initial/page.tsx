import { PageHeader } from "@/components/PageHeader";
import { WorkflowChecklist } from "@/components/WorkflowChecklist";

export default function InitialVisitPage() {
  return (
    <>
      <PageHeader eyebrow="Luồng khám lần đầu" title="Tiep nhan -> Care plan -> Tai kham" />
      <section className="grid cols-2">
        <div className="panel">
          <WorkflowChecklist
            steps={[
              { label: "Le tan dang ky", done: true },
              { label: "Dieu duong tiep nhan", done: true },
              { label: "Do sinh hieu", done: true },
              { label: "Sang loc co do", done: false, note: "Can hoan tat truoc khi bac si chot" },
              { label: "Ra soat thuoc dang dung", done: false },
              { label: "Bac si kham", done: false },
              { label: "Phan tang nguy co", done: false, note: "Khong cho hoan tat neu thieu" },
              { label: "Lap care plan", done: false },
              { label: "Giao loi dan A5", done: false },
              { label: "Dat lich tai kham", done: false, note: "Bat buoc hoac ghi ly do khong hen" }
            ]}
          />
        </div>
        <div className="panel">
          <h2>Safety gates</h2>
          <div className="danger-box">
            Khong cho hoan tat buoi kham neu chua co phan tang nguy co va ke hoach tai kham hoac ly do khong hen.
          </div>
          <p>
            Neu co dau nguc cap, kho tho cap, dau than kinh khu tru, ngat, lu lan, ha duong huyet nang hoac bat ky
            trieu chung can cap cuu, he thong chi hien canh bao can bac si danh gia truc tiep ngay.
          </p>
        </div>
      </section>
    </>
  );
}
