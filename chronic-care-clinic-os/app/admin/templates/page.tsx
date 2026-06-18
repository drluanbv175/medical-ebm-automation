import { PageHeader } from "@/components/PageHeader";

const templates = ["Tang huyet ap", "Dai thao duong", "Roi loan lipid", "Benh than man", "Suy tim on dinh", "COPD", "Hen", "Da thuoc o nguoi cao tuoi", "Sau xuat vien"];

export default function TemplatesPage() {
  return (
    <>
      <PageHeader eyebrow="Template management" title="Quan ly mau loi dan va checklist" actions={<button className="button">Tao template draft</button>} />
      <section className="grid cols-3">
        {templates.map((template) => (
          <div className="card" key={template}>
            <h3>{template}</h3>
            <p className="eyebrow">Trang thai: draft governance, can bac si duyet truoc production.</p>
          </div>
        ))}
      </section>
    </>
  );
}
