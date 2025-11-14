# MarkItDown HTTP API - Versão Corrigida

✅ **Correção aplicada**: Usa biblioteca Python diretamente (não CLI subprocess)

## 🔧 Diferenças da Versão Anterior

**Problema original**:
- Usava `spawn("markitdown")` subprocess
- Falhava com `UnsupportedFormatException` em stdin vazio

**Solução aplicada**:
- Usa `MarkItDown()` biblioteca Python diretamente
- Não depende do CLI
- Mais estável e rápido

## 📦 Arquivos Incluídos

- `app.py` - API FastAPI corrigida
- `Dockerfile` - Container otimizado
- `requirements.txt` - Dependências Python
- `README.md` - Este arquivo

## 🚀 Deploy no EasyPanel

### Passo 1: Atualizar Repositório

```bash
# Se já tem repo Git
cd markitdown-api

# Substituir arquivos
cp /caminho/para/app.py .
cp /caminho/para/Dockerfile .
cp /caminho/para/requirements.txt .

# Commit e push
git add .
git commit -m "Fix: Use MarkItDown Python library directly"
git push
```

### Passo 2: Redeploy no EasyPanel

1. EasyPanel → `markitdown-api` → **Settings**
2. Click "**Redeploy**"
3. ✅ Check "**Force Rebuild**" (importante!)
4. Click "**Deploy**"

### Passo 3: Aguardar Build

- Build deve levar ~5-10 minutos
- Acompanhe em **Logs** → **Build Logs**
- Aguarde mensagem: `Successfully built`

### Passo 4: Verificar Logs de Runtime

EasyPanel → **Logs** → **Runtime Logs**

**Deve aparecer**:
```
[STARTUP] Starting MarkItDown API on port 8000
[STARTUP] Max file size: 50.0MB
[STARTUP] CORS origins: ['*']
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Passo 5: Testar

```bash
# Health check
curl https://markitdown-markitdown.3j5ljv.easypanel.host/health

# Deve retornar:
{
  "status": "healthy",
  "version": "1.0.1",
  "uptime_seconds": 123
}
```

## 🧪 Teste de Conversão

```bash
# Baixar PDF de teste
curl -o test.pdf https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf

# Converter
curl -X POST https://markitdown-markitdown.3j5ljv.easypanel.host/convert \
  -H "Authorization: Bearer 5vi2Y+LzHqYxMmU+/wSQJfex6VnQvEIKunsFMzER4eY=" \
  -F "file=@test.pdf" \
  | jq .

# Resposta esperada:
{
  "success": true,
  "markdown": "# Dummy PDF file...",
  "plain_text": "Dummy PDF file...",
  "metadata": {
    "file_name": "test.pdf",
    "file_size_bytes": 13264,
    "characters": 234,
    "words": 45,
    "estimated_pages": 1,
    "detected_format": "document"
  },
  "processing_time_ms": 1234
}
```

## ⚙️ Variáveis de Ambiente

Configure no EasyPanel → Environment:

| Variável | Valor | Obrigatório |
|----------|-------|-------------|
| `PORT` | `8000` | ✅ Sim |
| `API_TOKEN` | `5vi2Y+LzHq...` | ✅ Sim |
| `MAX_FILE_SIZE` | `52428800` | ❌ Opcional (default: 50MB) |
| `ALLOWED_ORIGINS` | `*` | ❌ Opcional (default: *) |

## 📊 Recursos Recomendados

- **RAM**: 2 GB (mínimo) → 4 GB (recomendado)
- **CPU**: 1 vCore (mínimo) → 2 vCores (recomendado)
- **Disco**: 10 GB

## ✅ Checklist Pós-Deploy

- [ ] Container está "Running" (verde)
- [ ] Logs mostram "Uvicorn running on http://0.0.0.0:8000"
- [ ] `/health` retorna 200 OK
- [ ] Teste de conversão PDF funciona
- [ ] Token de autenticação funciona
- [ ] CORS configurado (se necessário)

## 🐛 Troubleshooting

### Container reinicia constantemente

**Causa**: Memória insuficiente

**Solução**: Aumentar RAM para 4GB

### Build falha com "No module named 'markitdown'"

**Causa**: `requirements.txt` não foi copiado

**Solução**: Verificar se arquivo existe no repo

### "Service is not reachable"

**Causa**: App não iniciou

**Solução**: Ver logs completos no EasyPanel

## 📞 Suporte

Se ainda tiver problemas:
1. Copie logs completos (últimas 50 linhas)
2. Tire screenshot do status
3. Me envie para diagnóstico

---

**Versão**: 1.0.1 (Corrigida)
**Data**: 2025-11-14
