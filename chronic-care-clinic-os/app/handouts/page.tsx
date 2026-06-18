import { PageHeader } from "@/components/PageHeader";
import { patients } from "@/lib/seed-data";

export default function HandoutsPage() {
  const patient = patients.find((item) => item.carePlan.status === "APPROVED") ?? patients[0];
  return (
    <>
      <PageHeader
        eyebrow="A5 patient handout"
        title="Loi dan sau kham can bac si duyet"
        actions={
          <>
            <select className="select" aria-label="Template">
              <option>Tang huyet ap</option>
              <option>Dai thao duong</option>
              <option>Benh than man</option>
              <option>Sau xuat vien</option>
            </select>
            <button className="button" type="button">
              In ban da duyet
            </button>
          </>
        }
      />
      <article className="handout">
        <h2>Loi dan sau kham</h2>
        <p>
          <strong>Ten nguoi benh:</strong> {patient.fullName}
        </p>
        <p>
          <strong>Ngay kham:</strong> 18/06/2026
        </p>
        <p>
          <strong>Chan doan chinh:</strong> {patient.conditions.map((condition) => condition.conditionName).join(", ")}
        </p>
        <p>
          <strong>Muc tieu dieu tri:</strong> Theo muc tieu ca the hoa trong care plan da duyet.
        </p>
        <p>
          <strong>Thuoc va luu y:</strong> Dung theo don/huong dan da duoc bac si xac nhan. Khong tu y doi lieu.
        </p>
        <p>
          <strong>Theo doi tai nha:</strong> Ghi nhan huyet ap, duong huyet neu duoc huong dan, dau hieu bat thuong va muc do tuan thu.
        </p>
        <p>
          <strong>Xet nghiem can lam:</strong> Theo lich trong care plan.
        </p>
        <p>
          <strong>Ngay tai kham:</strong> {patient.carePlan.nextFollowUpDate}
        </p>
        <div className="danger-box">
          Khi co dau nguc cap, kho tho cap, dau than kinh khu tru, ngat, lu lan, ha duong huyet nang, non/dau bung/roi loan y thuc
          hoac bat ky trieu chung nguy hiem: can lien he co so y te phu hop hoac cap cuu theo danh gia chuyen mon.
        </div>
        <p className="eyebrow">Ban nhap demo. Can bac si kiem chung va phe duyet truoc khi giao nguoi benh.</p>
      </article>
    </>
  );
}
