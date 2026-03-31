"use client";

import { useEffect, useState } from "react";

import AppShell from "@/components/app-shell";
import { TenderFlowSnapshot } from "@/types/tender";

export default function ResultsPage() {
  const [snapshot, setSnapshot] = useState<TenderFlowSnapshot | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("latestTenderFlow");
    if (!raw) {
      return;
    }

    try {
      setSnapshot(JSON.parse(raw) as TenderFlowSnapshot);
    } catch {
      localStorage.removeItem("latestTenderFlow");
    }
  }, []);

  return (
    <AppShell>
      <section className="panel">
        <span className="badge">Results</span>
        <h1>结果页</h1>
        <p>展示最近一次执行主链路后的结构化结果和标书初稿内容。</p>

        {!snapshot ? (
          <div className="placeholder-box">
            <h2 className="section-title">暂无结果</h2>
            <p className="muted">请先在招标上传页执行一次主链路，再回到这里查看结果。</p>
          </div>
        ) : (
          <>
            <div className="placeholder-box">
              <h2 className="section-title">解析文本预览</h2>
              <pre className="text-block">{snapshot.parse.text}</pre>
            </div>

            <div className="placeholder-box">
              <h2 className="section-title">核心字段抽取结果</h2>
              <div className="result-grid">
                <div className="result-item">
                  <strong>项目名称</strong>
                  <p>{snapshot.extract.project_name || "未识别"}</p>
                </div>
                <div className="result-item">
                  <strong>招标单位</strong>
                  <p>{snapshot.extract.tender_company || "未识别"}</p>
                </div>
                <div className="result-item">
                  <strong>预算金额</strong>
                  <p>{snapshot.extract.budget || "未识别"}</p>
                </div>
                <div className="result-item">
                  <strong>截止时间</strong>
                  <p>{snapshot.extract.deadline || "未识别"}</p>
                </div>
              </div>
              <p>
                <strong>资质要求：</strong>
                {snapshot.extract.qualification_requirements.join("；") || "未识别"}
              </p>
              <p>
                <strong>交付要求：</strong>
                {snapshot.extract.delivery_requirements.join("；") || "未识别"}
              </p>
              <p>
                <strong>评分重点：</strong>
                {snapshot.extract.scoring_focus.join("；") || "未识别"}
              </p>
            </div>

            <div className="placeholder-box">
              <h2 className="section-title">投标建议</h2>
              <p>
                <strong>建议结果：</strong>
                {snapshot.judge.should_bid ? "建议投标" : "建议谨慎评估"}
              </p>
              <p>
                <strong>判断理由：</strong>
                {snapshot.judge.reason}
              </p>
              <p>
                <strong>风险提示：</strong>
                {snapshot.judge.risks.join("；") || "暂无"}
              </p>
              <p>
                <strong>引用知识：</strong>
                {snapshot.judge.knowledge_used?.map((item) => `${item.category}/${item.document_title}/${item.section_title}`).join("；") ||
                  "未引用"}
              </p>
            </div>

            <div className="placeholder-box">
              <h2 className="section-title">标书初稿内容</h2>
              <pre className="text-block">{snapshot.generate.company_intro}</pre>
              <pre className="text-block">{snapshot.generate.project_cases}</pre>
              <pre className="text-block">{snapshot.generate.implementation_plan}</pre>
              <pre className="text-block">{snapshot.generate.business_response}</pre>
              <p>
                <strong>引用知识：</strong>
                {snapshot.generate.knowledge_used
                  ?.map((item) => `${item.category}/${item.document_title}/${item.section_title}`)
                  .join("；") || "未引用"}
              </p>
            </div>
          </>
        )}
      </section>
    </AppShell>
  );
}
