import type { Metadata } from "next";
import Link from "next/link";
import { navItems } from "@/lib/navigation";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chronic Care Clinic OS",
  description: "Internal chronic care clinic workflow system"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <div className="shell">
          <aside className="sidebar">
            <div className="brand">
              <strong>Chronic Care Clinic OS</strong>
              <span className="eyebrow">Noi bo phong kham benh man</span>
            </div>
            <nav className="nav" aria-label="Dieu huong chinh">
              {navItems.map((item) => (
                <Link href={item.href} key={item.href}>
                  {item.label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
