// Lee el JSON del reporter de Playwright y falla si hubo retries/flaky
const fs = require("fs");
const file = process.argv[2] || "playwright-report/results.json";

if (!fs.existsSync(file)) {
    console.error(`❌ No existe el reporte JSON: ${file}`);
    process.exit(1);
}

const data = JSON.parse(fs.readFileSync(file, "utf8"));
const flaky = [];
const failed = [];

function walkSuite(suite) {
    (suite.suites || []).forEach(walkSuite);
    (suite.specs || []).forEach((spec) => {
        (spec.tests || []).forEach((t) => {
            const attempts = (t.results || []).length;
            const hadRetries = (t.results || []).some((r) => (r.retry || 0) > 0);
            const last = t.results?.[t.results.length - 1];
            const status = t.outcome || t.status || last?.status;
            if (attempts > 1 || hadRetries || status === "flaky") {
                flaky.push({ title: spec.title, project: t.projectName, attempts, status });
            }
            if (status === "failed") {
                failed.push({ title: spec.title, project: t.projectName });
            }
        });
    });
}

(data.suites || []).forEach(walkSuite);

if (flaky.length) {
    console.error("❌ Flaky/retried tests detectados:");
    console.error(JSON.stringify(flaky, null, 2));
    process.exit(2);
}
if (failed.length) {
    console.error("❌ Tests fallidos:");
    console.error(JSON.stringify(failed, null, 2));
    process.exit(1);
}
console.log("✅ Sin flaky ni fallos.");