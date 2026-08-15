import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";

const sops = [
  "Tiep nhan nguoi benh benh man",
  "Kham lan dau",
  "Tai kham",
  "Do huyet ap",
  "Ra soat thuoc",
  "Nhac tai kham",
  "Co do va chuyen tuyen",
  "Sau xuat vien",
  "Bao mat du lieu",
  "Xu ly su co",
  "Cap nhat clinical rules"
];

export default function SopPage() {
  return (
    <>
      <PageHeader eyebrow="SOP repository" title="Kho quy trinh van hanh" />
      <section className="grid cols-3">
        {sops.map((sop) => (
          <Link className="card" href="/admin/sop" key={sop}>
            <h3>{sop}</h3>
            <p className="eyebrow">Xem ban mau trong docs/sop.</p>
          </Link>
        ))}
      </section>
    </>
  );
}
