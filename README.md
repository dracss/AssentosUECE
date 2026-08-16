# Assentos UECE — app Android

Aplicativo que calcula os quantitativos de assentos dos Conselhos de
Centro/Faculdade/Instituto (Resolução nº 1779/2022-CONSU, Art. 2º) e gera um PDF
com o resultado. Mesma lógica da página HTML:

- Membros natos = Direção (2: Diretor + Vice) + coord. graduação + coord. stricto sensu + 1 rep. lato sensu (se houver)
- Representantes docentes = 6 (fixo, Art. 2º, I)
- Total do Conselho = (natos + 6) ÷ 0,70
- STA + discentes = proporção global de 30% (Art. 2º, §6º), repartida igualmente (15% cada)

## Arquivos
- `main.py` — o app (KivyMD). A lógica de cálculo e a geração de PDF são funções puras (`calcular`, `gerar_pdf`).
- `buildozer.spec` — configuração do build (dependências, permissões, API).
- `.github/workflows/android-build.yml` — compila o APK no GitHub.

## Como gerar o APK (GitHub Actions)

1. Crie um repositório no GitHub e envie esta pasta:
   ```bash
   cd AssentosUECE
   git init && git add -A && git commit -m "Assentos UECE"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/AssentosUECE.git
   git push -u origin main
   ```
   (ou crie o repositório pelo site e faça upload dos arquivos)

2. O build roda automaticamente ao dar push. Também dá para disparar manualmente
   na aba **Actions → Build Android APK → Run workflow**. O primeiro build leva ~15–25 min.

3. Quando ficar verde, abra a execução, role até **Artifacts** e baixe **apk**
   (um zip com o `.apk` dentro).

4. (Opcional) Para um link permanente de download no celular, crie um Release e
   anexe o `.apk`.

## Instalar no celular
Transfira o `.apk`, habilite "Instalar apps desconhecidos" para o app que vai abri-lo
(Arquivos ou navegador), toque no APK e instale. O PDF gerado é salvo na pasta privada
do app e, quando possível, também em **Download**.

> APK debug é autoassinado — perfeito para uso pessoal/sideload. Publicação na Play
> Store exige build release assinado.
