import AppShell from "@/components/app-shell";

const categories = [
  "company_profile",
  "qualifications",
  "project_cases",
  "templates"
];

export default function KnowledgePage() {
  return (
    <AppShell>
      <section className="panel">
        <span className="badge">Knowledge Base</span>
        <h1>知识库页面</h1>
        <p>当前是知识库模块空壳，先提供类别展示和后续接口接入位置。</p>

        <div className="card-grid">
          {categories.map((category) => (
            <article className="card" key={category}>
              <h2>{category}</h2>
              <p className="muted">后续接入上传、列表、处理、检索接口。</p>
            </article>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
