import { StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { roleLabels } from "@/lib/rbac";
import { previewInviteUserAction } from "@/lib/workflow-actions";

const demoUsers = [
  { name: "Admin Demo", email: "admin.demo@example.test", role: "SUPER_ADMIN" },
  { name: "BS Nguyen Minh", email: "doctor.demo@example.test", role: "PHYSICIAN" },
  { name: "DD Tran Lan", email: "nurse.demo@example.test", role: "NURSE_COORDINATOR" },
  { name: "Le tan Demo", email: "frontdesk.demo@example.test", role: "RECEPTIONIST" },
  { name: "DS Le Hoa", email: "pharmacist.demo@example.test", role: "PHARMACIST" },
  { name: "QLCL Pham An", email: "quality.demo@example.test", role: "QUALITY_MANAGER" }
] as const;

export default function UsersPage() {
  const inviteAction = previewInviteUserAction(
    {
      name: "Dieu phoi vien Demo",
      email: "care.coordinator.demo@example.test",
      role: "CARE_COORDINATOR",
      organizationId: "org-demo",
      clinicSiteId: "site-demo",
      invitationReason: "Moi dieu phoi vien phu trach hang doi benh man."
    },
    {
      actorName: "Admin Phong Kham",
      actorRole: "CLINIC_ADMIN",
      accessContext: { role: "CLINIC_ADMIN", organizationId: "org-demo", clinicSiteId: "site-demo" },
      resourceScope: { organizationId: "org-demo", clinicSiteId: "site-demo" },
      confirmationChecked: true,
      reason: "Demo preview hop dong server action cho moi nguoi dung noi bo."
    }
  );

  return (
    <>
      <PageHeader eyebrow="User management" title="Quan ly nguoi dung va phan quyen" actions={<button className="button">Moi nguoi dung</button>} />
      <section className="panel" style={{ marginBottom: 16 }}>
        <h2>User invite preview</h2>
        <p>
          <StatusBadge>{inviteAction.status}</StatusBadge> {inviteAction.serverActionName}
        </p>
        <p>Backend guard: {inviteAction.backendGuard.reason}</p>
        <p>Persistence: {inviteAction.persistenceMode}</p>
        <p>{inviteAction.safetyBoundary}</p>
      </section>
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Ten</th>
              <th>Email</th>
              <th>Vai tro</th>
              <th>Trang thai</th>
            </tr>
          </thead>
          <tbody>
            {demoUsers.map((user) => (
              <tr key={user.email}>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>{roleLabels[user.role]}</td>
                <td>ACTIVE</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
