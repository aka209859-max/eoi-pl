# 🚀 Webアプリ ビルドエラー解決ガイド

**エラー**: `Cannot find module '@hono/vite-dev-server'`

---

## ✅ **解決方法**

### **Step 1: vite.config.ts を修正**

```powershell
notepad E:\eoi-pl\webapp\vite.config.ts
```

**すべて削除して、以下をコピペ:**

```typescript
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    target: 'esnext',
    minify: true,
    rollupOptions: {
      input: 'src/index.tsx',
      output: {
        entryFileNames: '_worker.js',
        format: 'es'
      }
    }
  }
})
```

**保存して閉じる（Ctrl+S → Alt+F4）**

---

### **Step 2: 再ビルド**

```powershell
npm run build
```

---

### **Step 3: 成功したら PM2で起動**

```powershell
# ポートクリーンアップ
fuser -k 3000/tcp 2>$null

# PM2起動
pm2 start ecosystem.config.cjs

# ブラウザでアクセス
start http://localhost:3000
```

---

**Play to Win!** 🏇
