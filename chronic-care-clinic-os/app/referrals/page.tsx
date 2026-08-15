import { PageHeader } from "@/components/PageHeader";
import { patients } from "@/lib/seed-data";

export default function ReferralsPage() {
  const referrals = patients.flatMap((patient) => patient.referrals.map((referral) => ({ patient, referral })));
  return (
    <>
      <PageHeader eyebrow="Referral workflow" title="Chuyen tuyen can bac si xac nhan" />
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Nguoi benh</th>
              <th>Loai</th>
              <th>Noi den</th>
              <th>Chuyen khoa</th>
              <th>Ly do</th>
              <th>Trang thai</th>
            </tr>
          </thead>
          <tbody>
            {referrals.map(({ patient, referral }) => (
              <tr key={referral.id}>
                <td>{patient.fullName}</td>
                <td>{referral.referralType}</td>
                <td>{referral.destination}</td>
                <td>{referral.specialty}</td>
                <td>{referral.reason}</td>
                <td>{referral.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
