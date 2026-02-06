import "./globals.css";

export const metadata = {
  title: "Free ATS Resume Checker",
  description: "Free ATS resume checker and optimizer with scoring + suggestions."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
