# PapersWithCode Notification

PapersWithCode の情報を取得して通知する．

## Install

```bash
cp env.template .env
vim .env
docker compose build
docker compose up -d
```

## `trend.py`

PapersWithCode のトップページに表示される trend の論文を slack に通知する．  
`.env`に DeepL か GCP の Translation API の token を設定しておくと，Absruct の日本語訳も一緒に通知される．
