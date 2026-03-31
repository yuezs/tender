import AppShell from "@/components/app-shell";

const modules = [
  {
    title: "招标文件上传",
    description: "上传 PDF、DOCX、TXT 招标文件，进入解析与抽取流程。"
  },
  {
    title: "投标建议",
    description: "展示是否建议投标、理由说明和风险提示。"
  },
  {
    title: "标书初稿",
    description: "输出公司介绍、项目案例、实施方案和商务响应草稿。"
  },
  {
    title: "企业知识库",
    description: "管理公司资料、资质、案例和模板，后续接入生成链路。"
  }
];

export default function HomePage() {
  return (
    <AppShell>
      <section className="hero">
        <span className="badge">MVP Skeleton</span>
        <h1>面向投标流程的最小可运行骨架</h1>
        <p>
          当前版本先打通页面结构、后端 API 骨架和统一响应格式。
          Agent 编排、知识检索和真实业务处理将在后续迭代接入。
        </p>
      </section>

      <section className="card-grid">
        {modules.map((item) => (
          <article className="card" key={item.title}>
            <h2>{item.title}</h2>
            <p className="muted">{item.description}</p>
          </article>
        ))}
      </section>
    </AppShell>
  );
}
