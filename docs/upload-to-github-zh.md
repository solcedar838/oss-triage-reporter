# 上傳到 GitHub 的快速步驟

這份 ZIP 已經幫你改好：

- GitHub 帳號：`solcedar838`
- Repo 名稱：`oss-triage-reporter`
- Python package 名稱：`oss-triage-reporter`
- GitHub Action 使用方式：`solcedar838/oss-triage-reporter@v0.1.0`

## 1. 建立 GitHub repo

在 GitHub 建立一個新的 public repository：

- Repository name: `oss-triage-reporter`
- Visibility: Public
- 不要勾選自動建立 README
- 不要勾選自動建立 `.gitignore`
- 不要勾選自動建立 license

因為這個專案裡已經有 README、`.gitignore` 和 MIT License。

## 2. 本機確認資料夾名稱

解壓縮後，建議資料夾名稱就是：

```text
oss-triage-reporter
```

進入資料夾後，應該會看到：

```text
README.md
pyproject.toml
LICENSE
action.yml
src
tests
docs
.github
```

## 3. 初始化 git 並上傳

在 `oss-triage-reporter` 資料夾裡打開終端機，執行：

```bash
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin https://github.com/solcedar838/oss-triage-reporter.git
git push -u origin main
```

## 4. 建立第一個 release tag

```bash
git tag v0.1.0
git push origin v0.1.0
```

建立 tag 後，別人就可以在 GitHub Actions 裡這樣使用：

```yaml
uses: solcedar838/oss-triage-reporter@v0.1.0
```

## 5. 確認 CI 通過

到 GitHub repo 的 `Actions` 頁面，確認 `CI` workflow 成功。

## 6. 手動跑 weekly report

到 `Actions` 頁面，找到 `Weekly OSS Triage Report`，按 `Run workflow`。

如果成功，它會產生一個 artifact：`oss-triage-report`。

## 7. 建議開幾個真實 issue

為了讓 repo 看起來像真的維護中，可以開幾個合理 issue，例如：

- Add configurable label mapping
- Add markdown template support
- Support posting report as issue comment
- Improve CI log summarization

然後自己處理其中 1-2 個 issue 或 PR，留下真實維護紀錄。
