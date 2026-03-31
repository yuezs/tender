import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 招投标助手",
  description: "AI 招投标助手 MVP 骨架"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
