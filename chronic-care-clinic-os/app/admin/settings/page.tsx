import { PageHeader } from "@/components/PageHeader";

export default function SettingsPage() {
  return (
    <>
      <PageHeader eyebrow="System settings" title="Cai dat he thong" />
      <section className="grid cols-2">
        <div className="panel">
          <h2>Security</h2>
          <p>Session timeout: 30 phut</p>
          <p>MFA-ready: planned</p>
          <p>Hard delete clinical record: disabled</p>
        </div>
        <div className="panel">
          <h2>AI draft assistance</h2>
          <p>Production default: disabled</p>
          <p>Khong tu ky note, khong tu gui tin nhan, khong tu thay doi du lieu goc.</p>
        </div>
        <div className="panel">
          <h2>Backup</h2>
          <p>Can cau hinh lich backup PostgreSQL truoc production.</p>
        </div>
        <div className="panel">
          <h2>Deployment</h2>
          <p>Local Docker Compose, san sang private server/on-premise.</p>
        </div>
      </section>
    </>
  );
}
