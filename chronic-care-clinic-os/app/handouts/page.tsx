import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/Badge";
import { WorkflowChecklist } from "@/components/WorkflowChecklist";
import { buildPatientEducationReleasePackage, buildPatientEducationReleaseQueue } from "@/lib/patient-education";
import { patients } from "@/lib/seed-data";
import { previewReleasePatientHandoutAction } from "@/lib/workflow-actions";

export default function HandoutsPage() {
  const patient = patients.find((item) => item.carePlan.status === "APPROVED") ?? patients[0];
  const releasePackage = buildPatientEducationReleasePackage(patient);
  const queue = buildPatientEducationReleaseQueue(patients);
  const releaseAction = previewReleasePatientHandoutAction(releasePackage, {
    actorName: "BS Nguyen Minh",
    actorRole: "PHYSICIAN",
    accessContext: { role: "PHYSICIAN", organizationId: "org-demo", clinicSiteId: "site-demo" },
    resourceScope: { organizationId: "org-demo", clinicSiteId: "site-demo" },
    confirmationChecked: true,
    reason: "Demo preview hop dong server action cho phat hanh loi dan A5."
  });
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
      <section className="grid cols-2" style={{ marginBottom: 16 }}>
        <div className="panel">
          <h2>Dieu kien phat hanh</h2>
          <p>
            Trang thai: <StatusBadge>{releasePackage.releaseStatus}</StatusBadge>
          </p>
          <p>{releasePackage.safetyBoundary}</p>
          <WorkflowChecklist
            steps={[
              {
                label: "Template giao duc da duyet",
                done: releasePackage.template.status === "APPROVED",
                note: `${releasePackage.template.title} - ${releasePackage.template.version}`
              },
              {
                label: "Care plan da APPROVED",
                done: patient.carePlan.status === "APPROVED",
                note: patient.carePlan.status
              },
              {
                label: "Consent giao tiep hop le",
                done: patient.consentStatus === "SIGNED",
                note: patient.consentStatus
              },
              {
                label: "Dieu kien giao tiep bang template",
                done: releasePackage.patientMessageAllowed,
                note: releasePackage.patientMessageAllowed
                  ? "Du dieu kien template/consent; demo van khong tu dong gui"
                  : "Chi in/preview trong demo"
              }
            ]}
          />
        </div>
        <div className="panel">
          <h2>Hang doi loi dan</h2>
          <p>San sang in: {queue.filter((item) => item.printAllowed).length}</p>
          <p>Can bo sung dieu kien: {queue.filter((item) => !item.printAllowed).length}</p>
          <p>Audit preview: {releasePackage.auditPreview.summary}</p>
          <p>Template review date: {releasePackage.template.reviewDate}</p>
          <h3>Server action preview</h3>
          <p>
            <StatusBadge>{releaseAction.status}</StatusBadge> {releaseAction.serverActionName}
          </p>
          <p>Persistence: {releaseAction.persistenceMode}</p>
          <p>Backend guard: {releaseAction.backendGuard.reason}</p>
          <p>{releaseAction.safetyBoundary}</p>
        </div>
      </section>
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
        {releasePackage.handoutSections.slice(4).map((section) => (
          <p key={section}>{section}</p>
        ))}
        <div className="danger-box">
          Khi co dau nguc cap, kho tho cap, dau than kinh khu tru, ngat, lu lan, ha duong huyet nang, non/dau bung/roi loan y thuc
          hoac bat ky trieu chung nguy hiem: can lien he co so y te phu hop hoac cap cuu theo danh gia chuyen mon.
        </div>
        <p className="eyebrow">Ban nhap demo. Can bac si kiem chung va phe duyet truoc khi giao nguoi benh.</p>
      </article>
    </>
  );
}
