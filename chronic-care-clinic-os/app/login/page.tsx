import { PageHeader } from "@/components/PageHeader";
import { roleLabels } from "@/lib/rbac";

export default function LoginPage() {
  return (
    <>
      <PageHeader eyebrow="Demo authentication" title="Dang nhap theo vai tro mau" />
      <div className="panel">
        <p>
          MVP dung role selector de demo luong nghiep vu. Production phai thay bang Auth.js, session timeout, password
          policy va MFA-ready configuration.
        </p>
        <div className="grid cols-3" style={{ marginTop: 14 }}>
          {Object.entries(roleLabels).map(([role, label]) => (
            <button className="button secondary" key={role}>
              {label}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
