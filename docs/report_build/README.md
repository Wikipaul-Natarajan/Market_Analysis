# Report build files

The final project report (`outputs/final_project_report_20261018/AgriSight_Final_Project_Report.docx`)
is generated from these files with the `docx` npm package:

```bash
cd docs/report_build
npm install docx
node build.js
```

`facts.json` holds the numbers taken from the pipeline outputs; `ch*.js` hold the chapter text; `lib.js`
holds the Anna University formatting (A4, Times New Roman 12 pt, 1.5 line spacing). Figures are read from
`outputs/figures/`. After opening the .docx in Word, accept the prompt to update fields (or press
Ctrl+A, then F9) to fill in the Table of Contents and the Lists of Tables and Figures.
