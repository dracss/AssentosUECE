"""
Assentos UECE — cálculo dos quantitativos de assentos dos Conselhos de
Centro/Faculdade/Instituto (Res. 1779/2022-CONSU, Art. 2º) e geração de PDF.

Regras (idênticas à página HTML):
- Membros natos = Direção (2: Diretor + Vice) + coord. graduação
  + coord. pós stricto sensu + 1 rep. lato sensu (se houver).
- Representantes docentes = 6 (fixo, Art. 2º, I).
- Total de vagas do Conselho = (natos + 6) / 0,70  (natos + docentes = 70%).
- STA + discentes = proporção global de 30% (Art. 2º, §6º): fixa-se o total
  conjunto no inteiro mais próximo de 30% e reparte-se igualmente (15% cada);
  em total ímpar o assento extra vai aos discentes.
"""
import os
import math
from datetime import datetime

# ---------------------------------------------------------------- lógica pura

def round_half_up(x):
    """Arredondamento 'metade para cima' (igual ao Math.round do JavaScript)."""
    return int(math.floor(x + 0.5))


def calcular(grad, stricto, lato, direcao=2):
    """Recebe inteiros >=0, um bool/int lato e a direção (>=1). Devolve dict."""
    grad = max(0, int(grad))
    stricto = max(0, int(stricto))
    lato = 1 if lato else 0

    direcao = max(1, int(direcao))   # Diretor (+ Vice, se houver) — Art. 2º, §2º
    docentes = 6         # fixo (Art. 2º, I)
    natos = direcao + grad + stricto + lato
    base = natos + docentes                      # 70% do Conselho

    total_exato = base / 0.70
    soma_exata = 0.30 * total_exato              # 30% conjunto
    prop_exata = 0.15 * total_exato              # 15% por categoria

    # Art. 2º, II e III: 15% do total para cada categoria. Como os assentos são
    # inteiros, arredonda-se PARA CIMA para garantir no mínimo 15% em cada categoria.
    # STA e discentes recebem SEMPRE o mesmo número de assentos.
    sta = int(math.ceil(prop_exata))
    dis = sta
    m = sta + dis                                # conjunto STA + discentes (>= 30%)
    total = natos + docentes + m

    return {
        "direcao": direcao, "grad": grad, "stricto": stricto, "lato": lato,
        "natos": natos, "docentes": docentes, "sta": sta, "dis": dis,
        "m": m, "total": total,
        "total_exato": total_exato, "soma_exata": soma_exata, "prop_exata": prop_exata,
        "pct_natos": natos / total * 100, "pct_doc": docentes / total * 100,
        "pct_sta": sta / total * 100, "pct_dis": dis / total * 100,
        "pct_conjunto": (sta + dis) / total * 100,
    }


def fmt(n):
    """Formata número no padrão pt-BR com até 2 casas, sem zeros à toa."""
    s = ("%.2f" % n).rstrip("0").rstrip(".")
    return s.replace(".", ",")


# ---------------------------------------------------------------- geração PDF

AZUL = (11, 61, 107)
AZUL2 = (18, 83, 154)
VERDE = (30, 122, 61)
AMARELO = (242, 194, 0)
CINZA = (90, 100, 115)


def gerar_pdf(unidade, r, destino):
    """Gera o PDF de resposta em 'destino' (caminho .pdf). Requer fpdf2."""
    from fpdf import FPDF

    unidade = (unidade or "").strip() or "(unidade não informada)"
    pdf = FPDF(orientation="P", unit="pt", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    W = pdf.w
    M = 48

    # faixa superior
    pdf.set_fill_color(*AZUL); pdf.rect(0, 0, W, 96, "F")
    pdf.set_fill_color(*VERDE); pdf.rect(W - 150, 0, 150, 96, "F")
    pdf.set_fill_color(*AMARELO); pdf.rect(0, 96, W, 4, "F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(M, 22); pdf.cell(0, 12, "UNIVERSIDADE ESTADUAL DO CEARA - UECE")
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(M, 40); pdf.cell(0, 18, "Quantitativo de Assentos do Conselho")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_xy(M, 64)
    pdf.cell(0, 14, "Res. no 1779/2022-CONSU, Art. 2o - Representacao de STA e Discentes")

    # unidade
    y = 128
    pdf.set_text_color(*AZUL)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(M, y); pdf.cell(0, 16, _latin(unidade))
    pdf.set_draw_color(225, 232, 240)
    pdf.line(M, y + 22, W - M, y + 22)
    y += 40

    # cartões numéricos
    gap = 12
    cw = (W - 2 * M - 3 * gap) / 4
    cards = [
        (r["natos"], "Membros natos", AZUL2),
        (r["docentes"], "Rep. docentes", AZUL2),
        (r["sta"], "Assentos STA", VERDE),
        (r["dis"], "Assentos discentes", VERDE),
    ]
    for i, (val, lab, cor) in enumerate(cards):
        x = M + i * (cw + gap)
        pdf.set_fill_color(245, 248, 250)
        pdf.rect(x, y, cw, 54, "F")
        pdf.set_text_color(*cor)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_xy(x, y + 8); pdf.cell(cw, 24, str(val), align="C")
        pdf.set_text_color(*CINZA)
        pdf.set_font("Helvetica", "", 7.6)
        pdf.set_xy(x, y + 36); pdf.cell(cw, 12, _latin(lab), align="C")
    y += 54 + 26

    # tabela
    pdf.set_text_color(*AZUL)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(M, y); pdf.cell(0, 14, "Composicao do Conselho")
    y += 18

    col_cat = M + 8
    col_n = W - M - 130
    col_pct = W - M - 8
    pdf.set_fill_color(241, 245, 249); pdf.rect(M, y, W - 2 * M, 20, "F")
    pdf.set_text_color(51, 65, 85); pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_xy(col_cat, y + 6); pdf.cell(0, 10, "CATEGORIA")
    pdf.set_xy(col_n - 60, y + 6); pdf.cell(60, 10, "ASSENTOS", align="R")
    pdf.set_xy(col_pct - 70, y + 6); pdf.cell(70, 10, "% DO TOTAL", align="R")
    y += 20

    linhas = [
        ("Membros natos", r["natos"], r["pct_natos"]),
        ("Representantes docentes (eleitos)", r["docentes"], r["pct_doc"]),
        ("Representantes tecnico-administrativos (STA)", r["sta"], r["pct_sta"]),
        ("Representantes discentes", r["dis"], r["pct_dis"]),
    ]
    pdf.set_text_color(31, 41, 55)
    pdf.set_font("Helvetica", "", 9.5)
    for nome, n, pct in linhas:
        pdf.set_xy(col_cat, y + 5); pdf.cell(0, 12, _latin(nome))
        pdf.set_xy(col_n - 60, y + 5); pdf.cell(60, 12, str(n), align="R")
        pdf.set_xy(col_pct - 70, y + 5); pdf.cell(70, 12, fmt(pct) + "%", align="R")
        pdf.set_draw_color(230, 235, 242); pdf.line(M, y + 20, W - M, y + 20)
        y += 20

    # total
    pdf.set_fill_color(247, 250, 248); pdf.rect(M, y, W - 2 * M, 22, "F")
    pdf.set_draw_color(*VERDE); pdf.set_line_width(1.4)
    pdf.line(M, y, W - M, y); pdf.set_line_width(0.2)
    pdf.set_text_color(*AZUL); pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_xy(col_cat, y + 5); pdf.cell(0, 12, "Total de vagas do Conselho")
    pdf.set_xy(col_n - 60, y + 5); pdf.cell(60, 12, str(r["total"]), align="R")
    pdf.set_xy(col_pct - 70, y + 5); pdf.cell(70, 12, "100%", align="R")
    y += 40

    # memória de cálculo
    pdf.set_fill_color(251, 252, 254); pdf.rect(M, y, W - 2 * M, 104, "F")
    pdf.set_fill_color(*AMARELO); pdf.rect(M, y, 4, 104, "F")
    pdf.set_text_color(*CINZA); pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(M + 14, y + 8); pdf.cell(0, 12, "Memoria de calculo")
    pdf.set_font("Helvetica", "", 8.6)
    mem = [
        "Membros natos = Direcao (%d) + Graduacao (%d) + Stricto sensu (%d) + Lato sensu (%d) = %d."
        % (r["direcao"], r["grad"], r["stricto"], r["lato"], r["natos"]),
        "Total de vagas do Conselho = (natos %d + 6 docentes) / 0,70 = %s  (natos + docentes = 70%%)."
        % (r["natos"], fmt(r["total_exato"])),
        "15%% incidente sobre o total (Art. 2o, II e III) = %s -> arredondado para cima (min. 15%%) = %d para cada categoria (STA = discentes)."
        % (fmt(r["prop_exata"]), r["sta"]),
        "STA + discentes = %d assentos = %s%% do Conselho. Cada categoria = %s%% (>= 15%%)."
        % (r["m"], fmt(r["pct_conjunto"]), fmt(r["pct_sta"])),
    ]
    yy = y + 26
    pdf.set_xy(M + 14, yy)
    for t in mem:
        pdf.set_xy(M + 14, yy)
        pdf.multi_cell(W - 2 * M - 28, 12, _latin(t))
        yy += 18
    y += 104 + 18

    pdf.set_text_color(*CINZA); pdf.set_font("Helvetica", "I", 8)
    pdf.set_xy(M, y)
    pdf.multi_cell(
        W - 2 * M, 11,
        _latin("Fundamentos: Art. 2o, II, III e §§2o e 6o da Res. 1779/2022-CONSU; item VI do art. 47 "
               "do Regimento Geral da UECE. Os quantitativos finais sao definidos pelo Conselho e "
               "apontados no edital (Art. 2o, §6o)."))

    # rodapé
    hy = pdf.h - 30
    pdf.set_draw_color(225, 232, 240); pdf.line(M, hy - 8, W - M, hy - 8)
    pdf.set_font("Helvetica", "", 7.5); pdf.set_text_color(*CINZA)
    hoje = datetime.now().strftime("%d/%m/%Y")
    pdf.set_xy(M, hy)
    pdf.cell(0, 10, _latin("Gerado em %s - UECE - Av. Dr. Silas Munguba, 1700 - Campus do Itaperi - Fortaleza/CE" % hoje))

    pdf.output(destino)
    return destino


def _latin(s):
    """fpdf2 core fonts usam latin-1; troca o que não couber por equivalente ASCII."""
    repl = {"–": "-", "—": "-", "•": "-", "“": '"', "”": '"', "’": "'", "→": "->"}
    for a, b in repl.items():
        s = s.replace(a, b)
    try:
        s.encode("latin-1")
        return s
    except UnicodeEncodeError:
        return s.encode("latin-1", "replace").decode("latin-1")


# ---------------------------------------------------------------- interface

try:
    from kivymd.app import MDApp
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.card import MDCard
    from kivymd.uix.label import MDLabel
    from kivymd.uix.button import MDRaisedButton, MDFlatButton
    from kivymd.uix.textfield import MDTextField
    from kivymd.uix.selectioncontrol import MDCheckbox
    from kivymd.uix.toolbar import MDTopAppBar
    from kivymd.uix.dialog import MDDialog
    from kivy.uix.scrollview import ScrollView
    from kivy.metrics import dp
    from kivy.core.window import Window
    _KIVY_OK = True
except Exception:  # rodando fora do ambiente Kivy (ex.: testes)
    _KIVY_OK = False


def _shared_download_dir():
    """No Android tenta a pasta pública Download; caso contrário devolve None."""
    try:
        from android.storage import primary_external_storage_path  # type: ignore
        d = os.path.join(primary_external_storage_path(), "Download")
        if os.path.isdir(d):
            return d
    except Exception:
        pass
    return None


if _KIVY_OK:

    class AssentosApp(MDApp):
        def build(self):
            self.title = "Assentos UECE"
            self.theme_cls.primary_palette = "Blue"
            self.theme_cls.theme_style = "Light"
            self.resultado = None

            root = MDBoxLayout(orientation="vertical")
            root.add_widget(MDTopAppBar(title="Assentos UECE", elevation=2))

            scroll = ScrollView()
            self.form = MDBoxLayout(
                orientation="vertical", padding=dp(16), spacing=dp(12),
                adaptive_height=True, size_hint_y=None)
            self.form.bind(minimum_height=self.form.setter("height"))

            self.form.add_widget(MDLabel(
                text="Res. 1779/2022-CONSU, Art. 2o - preencha os membros natos:",
                theme_text_color="Secondary", adaptive_height=True, size_hint_y=None,
                height=dp(24)))

            self.unidade = MDTextField(hint_text="Centro / Faculdade / Instituto")
            self.direcao = MDTextField(
                hint_text="Direcao (Diretor + Vice; use 1 se nao houver Vice)",
                input_filter="int", text="2")
            self.grad = MDTextField(hint_text="Coordenadores de Graduacao",
                                    input_filter="int", text="0")
            self.stricto = MDTextField(hint_text="Coordenadores de Pos Stricto Sensu",
                                       input_filter="int", text="0")
            for w in (self.unidade, self.direcao, self.grad, self.stricto):
                self.form.add_widget(w)

            # lato sensu (checkbox + rótulo)
            lato_row = MDBoxLayout(orientation="horizontal", adaptive_height=True,
                                   size_hint_y=None, height=dp(40), spacing=dp(6))
            self.lato = MDCheckbox(size_hint=(None, None), size=(dp(40), dp(40)))
            lato_row.add_widget(self.lato)
            lato_row.add_widget(MDLabel(text="Oferta Pos-Graduacao Lato Sensu?",
                                        adaptive_height=True))
            self.form.add_widget(lato_row)

            self.form.add_widget(MDLabel(
                text="Docentes = 6 (fixo, Art. 2o, I). Direcao editavel (padrao 2).",
                theme_text_color="Hint", adaptive_height=True, size_hint_y=None,
                height=dp(22)))

            btns = MDBoxLayout(orientation="horizontal", adaptive_height=True,
                               size_hint_y=None, height=dp(48), spacing=dp(12))
            btns.add_widget(MDRaisedButton(text="Calcular", on_release=self.on_calcular))
            self.btn_pdf = MDRaisedButton(text="Gerar PDF", on_release=self.on_pdf,
                                          md_bg_color=(0.12, 0.48, 0.24, 1), disabled=True)
            btns.add_widget(self.btn_pdf)
            self.form.add_widget(btns)

            # cartão de resultado
            self.card = MDCard(orientation="vertical", padding=dp(14), spacing=dp(6),
                               size_hint_y=None, adaptive_height=True, elevation=1,
                               md_bg_color=(0.95, 0.97, 0.95, 1))
            self.res_label = MDLabel(text="", adaptive_height=True, size_hint_y=None)
            self.res_label.bind(texture_size=lambda i, v: setattr(i, "height", v[1]))
            self.card.add_widget(self.res_label)
            self.card.height = dp(1)
            self.card.opacity = 0
            self.form.add_widget(self.card)

            scroll.add_widget(self.form)
            root.add_widget(scroll)
            return root

        def on_start(self):
            try:
                from android.permissions import request_permissions, Permission  # type: ignore
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                                     Permission.READ_EXTERNAL_STORAGE])
            except Exception:
                pass

        def _int(self, w):
            try:
                return max(0, int(w.text or "0"))
            except ValueError:
                return 0

        def on_calcular(self, *_):
            r = calcular(self._int(self.grad), self._int(self.stricto),
                         self.lato.active, max(1, self._int(self.direcao)))
            self.resultado = r
            self.res_label.text = (
                "[b]Composicao do Conselho[/b]\n"
                "Membros natos: %d\n"
                "Representantes docentes: %d\n"
                "Assentos STA: %d  (%s%%)\n"
                "Assentos discentes: %d  (%s%%)\n"
                "[b]Total de vagas: %d[/b]\n"
                "STA + discentes = %s%% do Conselho (meta: 30%%)."
                % (r["natos"], r["docentes"], r["sta"], fmt(r["pct_sta"]),
                   r["dis"], fmt(r["pct_dis"]), r["total"], fmt(r["pct_conjunto"]))
            )
            self.res_label.markup = True
            self.card.opacity = 1
            self.card.height = self.res_label.height + dp(28)
            self.btn_pdf.disabled = False

        def on_pdf(self, *_):
            if not self.resultado:
                return
            nome = (self.unidade.text or "unidade").strip()
            safe = "".join(c if c.isalnum() else "_" for c in nome)[:40] or "unidade"
            fname = "assentos_%s.pdf" % safe

            # caminho primário: sempre gravável (privado do app)
            paths = []
            priv = os.path.join(self.user_data_dir, fname)
            try:
                gerar_pdf(self.unidade.text, self.resultado, priv)
                paths.append(priv)
            except Exception as e:
                self._dialog("Erro ao gerar PDF", str(e))
                return

            # tenta também copiar para Download (visível no app Arquivos)
            shared = _shared_download_dir()
            if shared:
                try:
                    dest = os.path.join(shared, fname)
                    with open(priv, "rb") as a, open(dest, "wb") as b:
                        b.write(a.read())
                    paths.append(dest)
                except Exception:
                    pass

            msg = "PDF gerado:\n" + "\n".join(paths)
            self._dialog("Concluido", msg)

        def _dialog(self, titulo, texto):
            d = MDDialog(title=titulo, text=texto,
                         buttons=[MDFlatButton(text="OK",
                                               on_release=lambda *_: d.dismiss())])
            d.open()


if __name__ == "__main__":
    if _KIVY_OK:
        AssentosApp().run()
    else:
        # execução de linha de comando para testes rápidos
        r = calcular(3, 1, 1)
        print(r)
