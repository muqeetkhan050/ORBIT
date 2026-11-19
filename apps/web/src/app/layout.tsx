import "./globals.css";

export const metadata = {
  title: "ORBIT",
  description: "Your AI productivity workspace",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/* suppressHydrationWarning: browser extensions (e.g. Grammarly) add attributes to <body>
          before React loads, which would otherwise log a harmless mismatch warning. */}
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
