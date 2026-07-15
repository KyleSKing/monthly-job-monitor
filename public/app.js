// 信息安全合规职位监控 — 纯 JS 单页应用
// 四视图:全部职位 / Top 20 / 职位详情 / 搜索过滤(复用列表视图)
// 数据源:GET /api/jobs (统一 job shape,含 score)

// 数据源:GET /api/latest-report (返回 {jobs:[...]},统一 job shape,含 score)
// 注:不用 /api/jobs —— 它在 Vercel serverless 上 sibling import 失败(500)。

const API_REPORT = "/api/latest-report";
const API_RESCRAPE = "/api/rescrape";

let allJobs = [];       // 已加载的全量职位
let filter = { title: "", company: "" };

// ---------- 数据 ----------

async function loadJobs() {
  const res = await fetch(API_REPORT);
  if (!res.ok) throw new Error(`加载失败: ${res.status}`);
  const report = await res.json();
  const jobs = report.jobs || [];
  // 按 score 降序
  allJobs = jobs.slice().sort((a, b) => (b.score || 0) - (a.score || 0));
}

function applyFilter(jobs) {
  const t = filter.title.trim().toLowerCase();
  const c = filter.company.trim().toLowerCase();
  return jobs.filter((j) => {
    const okT = !t || (j.title || "").toLowerCase().includes(t);
    const okC = !c || (j.company || "").toLowerCase().includes(c);
    return okT && okC;
  });
}

// ---------- 渲染 ----------

function jobCard(job) {
  const hi = (job.score || 0) >= 7 ? "hi" : "";
  return `
    <div class="card" data-id="${job.id}">
      <div class="row">
        <div>
          <h3>${escape(job.title)}</h3>
          <div class="meta">${escape(job.company)} · ${escape(job.location)}${
    job.salaryRange ? " · " + escape(job.salaryRange) : ""
  }</div>
        </div>
        <span class="badge ${hi}">${job.score ?? 0}</span>
      </div>
    </div>`;
}

function renderList(jobs, emptyMsg) {
  const view = document.getElementById("view");
  const list = applyFilter(jobs);
  if (!list.length) {
    view.innerHTML = `<div class="empty">${emptyMsg}</div>`;
    return;
  }
  view.innerHTML = list.map(jobCard).join("");
  view.querySelectorAll(".card").forEach((el) => {
    el.addEventListener("click", () => {
      location.hash = `#/job/${el.dataset.id}`;
    });
  });
}

function renderDetail(id) {
  const view = document.getElementById("view");
  const job = allJobs.find((j) => String(j.id) === String(id));
  if (!job) {
    view.innerHTML = `<div class="empty">未找到该职位</div>`;
    return;
  }
  view.innerHTML = `
    <span class="back" id="back">← 返回列表</span>
    <div class="detail">
      <h2>${escape(job.title)}</h2>
      <div class="kv">公司：${escape(job.company)}</div>
      <div class="kv">地点：${escape(job.location)}</div>
      <div class="kv">薪资：${escape(job.salaryRange || "未提供")}</div>
      <div class="kv">来源：${escape(job.source || "-")}</div>
      <div class="kv">匹配分数：${job.score ?? 0} / 10</div>
      <div class="summary">${escape(job.summary || "暂无描述")}</div>
      ${job.url ? `<a class="apply" href="${escape(job.url)}" target="_blank" rel="noopener">查看职位 →</a>` : ""}
    </div>`;
  document.getElementById("back").addEventListener("click", () => {
    history.back();
  });
}

// ---------- 路由 ----------

function router() {
  const hash = location.hash || "#/all";
  const toolbar = document.getElementById("toolbar");
  setActiveNav(hash);

  if (hash.startsWith("#/job/")) {
    toolbar.style.display = "none";
    renderDetail(hash.slice("#/job/".length));
  } else if (hash.startsWith("#/top")) {
    toolbar.style.display = "flex";
    renderList(allJobs.slice(0, 20), "暂无职位");
  } else {
    toolbar.style.display = "flex";
    renderList(allJobs, "暂无职位");
  }
}

function setActiveNav(hash) {
  document.querySelectorAll("nav a[data-nav]").forEach((a) => {
    const match =
      (hash.startsWith("#/top") && a.getAttribute("href") === "#/top") ||
      (!hash.startsWith("#/top") && a.getAttribute("href") === "#/all");
    a.classList.toggle("active", match);
  });
}

// ---------- 交互 ----------

function wireToolbar() {
  document.getElementById("btn-search").addEventListener("click", () => {
    filter.title = document.getElementById("q-title").value;
    filter.company = document.getElementById("q-company").value;
    router();
  });
  document.getElementById("btn-clear").addEventListener("click", () => {
    filter = { title: "", company: "" };
    document.getElementById("q-title").value = "";
    document.getElementById("q-company").value = "";
    router();
  });
  document.getElementById("btn-refresh").addEventListener("click", refresh);
  document.getElementById("btn-rescrape").addEventListener("click", rescrape);
}

async function refresh() {
  const status = document.getElementById("rescrape-status");
  status.textContent = "正在刷新…";
  try {
    await loadJobs();
    router();
    status.textContent = `✅ 已刷新，共 ${allJobs.length} 条`;
  } catch (e) {
    status.textContent = "刷新失败：" + e.message;
  }
}

async function rescrape() {
  const status = document.getElementById("rescrape-status");
  status.textContent = "正在触发…";
  try {
    const res = await fetch(API_RESCRAPE, { method: "POST" });
    if (res.status === 202) {
      status.textContent = "✅ 已触发爬取,完成后数据会自动更新";
    } else if (res.status === 501) {
      status.textContent = "⚠️ 服务端未配置爬取(缺 GITHUB_TOKEN)";
    } else {
      status.textContent = `触发失败:${res.status}`;
    }
  } catch (e) {
    status.textContent = "触发失败:网络错误";
  }
}

function escape(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// ---------- 启动 ----------

async function init() {
  wireToolbar();
  window.addEventListener("hashchange", router);
  try {
    await loadJobs();
  } catch (e) {
    document.getElementById("view").innerHTML = `<div class="empty">${escape(e.message)}</div>`;
    return;
  }
  router();
}

init();
