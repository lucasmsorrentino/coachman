#!/usr/bin/env node
// Renderiza docs/diagramas/*.mmd em docs/img/diagramas/*.svg e *.png.
//
//   npm install mermaid@11 playwright
//   node tools/render_diagrams.js
//
// Usa o Mermaid dentro de um Chromium sem janela (Playwright), o mesmo motor
// que o GitHub usa para desenhar os blocos ```mermaid do DIAGRAMAS.md.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const SRC = path.join(ROOT, "docs", "diagramas");
const OUT = path.join(ROOT, "docs", "img", "diagramas");

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  await page.setContent('<html><body style="margin:0;background:#fff"><div id="out"></div></body></html>');
  await page.addScriptTag({ path: require.resolve("mermaid/dist/mermaid.min.js") });
  await page.evaluate(() =>
    mermaid.initialize({
      startOnLoad: false,
      theme: "default",
      maxTextSize: 500000,
      maxEdges: 2000,
      htmlLabels: false, // texto SVG puro: abre em qualquer visualizador (sem foreignObject)
      class: { hideEmptyMembersBox: true, htmlLabels: false },
      themeVariables: { fontFamily: "Arial, Helvetica, sans-serif" },
    })
  );
  for (const file of fs.readdirSync(SRC).filter((f) => f.endsWith(".mmd")).sort()) {
    const name = path.basename(file, ".mmd");
    const code = fs.readFileSync(path.join(SRC, file), "utf8");
    const svg = await page.evaluate(async ([id, src]) => (await mermaid.render(id, src)).svg, [`d-${name}`, code]);
    fs.writeFileSync(path.join(OUT, `${name}.svg`), svg);
    // tamanho natural do desenho (sem encolher para a largura da página)
    const size = await page.evaluate((s) => {
      const out = document.getElementById("out");
      out.innerHTML = s;
      const el = out.querySelector("svg");
      const box = el.viewBox.baseVal;
      el.style.maxWidth = "none";
      el.setAttribute("width", box.width);
      el.setAttribute("height", box.height);
      return { width: Math.ceil(box.width), height: Math.ceil(box.height) };
    }, svg);
    await page.setViewportSize({ width: Math.max(800, size.width), height: Math.max(600, size.height) });
    const element = await page.$("#out svg");
    await element.screenshot({ path: path.join(OUT, `${name}.png`) });
    console.log("ok", name);
  }
  await browser.close();
})();
