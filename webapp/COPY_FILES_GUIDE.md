# 🚀 Webアプリ ファイル上書きガイド

**作成日**: 2026-02-01  
**Phase**: 1-2 Backend API実装完了

---

## 📋 **CEOの操作手順**

### **Step 1: 作成したファイルを上書き**

以下のファイルを sandbox から CEO の PC にコピーします:

```powershell
# PowerShell で実行

# src/index.tsx を上書き
notepad E:\eoi-pl\webapp\src\index.tsx
# → 以下のURLからコピー: https://www.genspark.ai (ファイル内容は後で提供)

# public/static/app.js を上書き
notepad E:\eoi-pl\webapp\public\static\app.js
# → 以下のURLからコピー: https://www.genspark.ai (ファイル内容は後で提供)

# package.json を上書き
notepad E:\eoi-pl\webapp\package.json
# → 以下のURLからコピー: https://www.genspark.ai (ファイル内容は後で提供)

# ecosystem.config.cjs を作成
notepad E:\eoi-pl\webapp\ecosystem.config.cjs
# → 以下のURLからコピー: https://www.genspark.ai (ファイル内容は後で提供)
```

---

## 📄 **ファイル一覧**

### **1. src/index.tsx**
- Backend API エンドポイント
- メインページHTML
- CORS設定

### **2. public/static/app.js**
- Frontend JavaScript
- 予想表示ロジック
- note/Discord用コピー機能

### **3. package.json**
- 依存関係
- ビルドスクリプト

### **4. ecosystem.config.cjs**
- PM2設定（開発環境）

---

## 🚀 **次のステップ**

```powershell
# Step 1: 依存関係をインストール
cd E:\eoi-pl\webapp
npm install

# Step 2: ビルド
npm run build

# Step 3: PM2で起動
pm2 start ecosystem.config.cjs

# Step 4: ブラウザでアクセス
start http://localhost:3000
```

---

**準備完了です！次のファイル内容を提供します。** 🏇
