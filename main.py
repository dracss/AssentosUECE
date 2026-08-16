"""
Assentos UECE — cálculo dos quantitativos de assentos dos Conselhos de
Centro/Faculdade/Instituto (Res. 1779/2022-CONSU, Art. 2º) e geração de PDF.
Interface em Kivy puro (sem KivyMD) para máxima estabilidade no Android.

Regras:
- Membros natos = Direção (editável, padrão 2: Diretor + Vice) + coord. graduação
  + coord. pós stricto sensu + 1 rep. lato sensu (se houver).
- Representantes docentes = 6 (fixo, Art. 2º, I).
- Total de vagas do Conselho = (natos + 6) / 0,70  (natos + docentes = 70%).
- STA = discentes = 15% do total, arredondado PARA CIMA (garante no mínimo 15%
  em cada categoria; STA e discentes sempre iguais).
"""
import os
import math
from datetime import datetime

# ---------------------------------------------------------------- lógica pura

def round_half_up(x):
    return int(math.floor(x + 0.5))


def calcular(grad, stricto, lato, direcao=2):
    grad = max(0, int(grad))
    stricto = max(0, int(stricto))
    lato = 1 if lato else 0
    direcao = max(1, int(direcao))
    docentes = 6

    natos = direcao + grad + stricto + lato
    base = natos + docentes
    total_exato = base / 0.70
    prop_exata = 0.15 * total_exato
    soma_exata = 0.30 * total_exato

    sta = int(math.ceil(prop_exata))   # arredonda para cima -> >= 15% por categoria
    dis = sta                          # STA e discentes sempre iguais
    m = sta + dis
    total = natos + docentes + m

    return {
        "direcao": direcao, "grad": grad, "stricto": stricto, "lato": lato,
        "natos": natos, "docentes": docentes, "sta": sta, "dis": dis,
        "m": m, "total": total,
        "total_exato": total_exato, "prop_exata": prop_exata, "soma_exata": soma_exata,
        "pct_natos": natos / total * 100, "pct_doc": docentes / total * 100,
        "pct_sta": sta / total * 100, "pct_dis": dis / total * 100,
        "pct_conjunto": (sta + dis) / total * 100,
    }


def fmt(n):
    s = ("%.2f" % n).rstrip("0").rstrip(".")
    return s.replace(".", ",")


# ---------------------------------------------------------------- geração PDF

AZUL = (11, 61, 107)
AZUL2 = (18, 83, 154)
VERDE = (30, 122, 61)
AMARELO = (242, 194, 0)
CINZA = (90, 100, 115)


def _latin(s):
    repl = {"–": "-", "—": "-", "•": "-", "“": '"', "”": '"', "’": "'",
            "→": "->", "º": "o", "ª": "a", "§": "S"}
    for a, b in repl.items():
        s = s.replace(a, b)
    try:
        s.encode("latin-1"); return s
    except UnicodeEncodeError:
        return s.encode("latin-1", "replace").decode("latin-1")


def gerar_pdf(unidade, r, destino):
    from fpdf import FPDF

    unidade = (unidade or "").strip() or "(unidade nao informada)"
    pdf = FPDF(orientation="P", unit="pt", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    W = pdf.w
    M = 48

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

    y = 128
    pdf.set_text_color(*AZUL)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(M, y); pdf.cell(0, 16, _latin(unidade))
    pdf.set_draw_color(225, 232, 240)
    pdf.line(M, y + 22, W - M, y + 22)
    y += 40

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
        pdf.set_text_color(*cor); pdf.set_font("Helvetica", "B", 22)
        pdf.set_xy(x, y + 8); pdf.cell(cw, 24, str(val), align="C")
        pdf.set_text_color(*CINZA); pdf.set_font("Helvetica", "", 7.6)
        pdf.set_xy(x, y + 36); pdf.cell(cw, 12, _latin(lab), align="C")
    y += 54 + 26

    pdf.set_text_color(*AZUL); pdf.set_font("Helvetica", "B", 11)
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
    pdf.set_text_color(31, 41, 55); pdf.set_font("Helvetica", "", 9.5)
    for nome, n, pct in linhas:
        pdf.set_xy(col_cat, y + 5); pdf.cell(0, 12, _latin(nome))
        pdf.set_xy(col_n - 60, y + 5); pdf.cell(60, 12, str(n), align="R")
        pdf.set_xy(col_pct - 70, y + 5); pdf.cell(70, 12, fmt(pct) + "%", align="R")
        pdf.set_draw_color(230, 235, 242); pdf.line(M, y + 20, W - M, y + 20)
        y += 20

    pdf.set_fill_color(247, 250, 248); pdf.rect(M, y, W - 2 * M, 22, "F")
    pdf.set_draw_color(*VERDE); pdf.set_line_width(1.4)
    pdf.line(M, y, W - M, y); pdf.set_line_width(0.2)
    pdf.set_text_color(*AZUL); pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_xy(col_cat, y + 5); pdf.cell(0, 12, "Total de vagas do Conselho")
    pdf.set_xy(col_n - 60, y + 5); pdf.cell(60, 12, str(r["total"]), align="R")
    pdf.set_xy(col_pct - 70, y + 5); pdf.cell(70, 12, "100%", align="R")
    y += 40

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
        "15%% incidente sobre o total (Art. 2o, II e III) = %s -> arredondado para cima (min. 15%%) = %d por categoria."
        % (fmt(r["prop_exata"]), r["sta"]),
        "STA + discentes = %d assentos = %s%% do Conselho. Cada categoria = %s%% (>= 15%%)."
        % (r["m"], fmt(r["pct_conjunto"]), fmt(r["pct_sta"])),
    ]
    yy = y + 26
    for t in mem:
        pdf.set_xy(M + 14, yy)
        pdf.multi_cell(W - 2 * M - 28, 12, _latin(t))
        yy += 18
    y += 104 + 18

    pdf.set_text_color(*CINZA); pdf.set_font("Helvetica", "I", 8)
    pdf.set_xy(M, y)
    pdf.multi_cell(W - 2 * M, 11, _latin(
        "Fundamentos: Art. 2o, II, III e SS 2o e 6o da Res. 1779/2022-CONSU; item VI do art. 47 do "
        "Regimento Geral da UECE. Os quantitativos finais sao definidos pelo Conselho e apontados no edital."))

    hy = pdf.h - 30
    pdf.set_draw_color(225, 232, 240); pdf.line(M, hy - 8, W - M, hy - 8)
    pdf.set_font("Helvetica", "", 7.5); pdf.set_text_color(*CINZA)
    hoje = datetime.now().strftime("%d/%m/%Y")
    pdf.set_xy(M, hy)
    pdf.cell(0, 10, _latin("Gerado em %s - UECE - Av. Dr. Silas Munguba, 1700 - Campus do Itaperi - Fortaleza/CE" % hoje))

    pdf.output(destino)
    return destino


# ---------------------------------------------------------------- interface (Kivy puro)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.core.window import Window

Window.clearcolor = (0.96, 0.97, 0.98, 1)


def _shared_download_dir():
    try:
        from android.storage import primary_external_storage_path  # type: ignore
        d = os.path.join(primary_external_storage_path(), "Download")
        if os.path.isdir(d):
            return d
    except Exception:
        pass
    return None


def _campo(texto, valor="", numerico=False):
    """Cria um bloco rótulo + TextInput e devolve (box, textinput)."""
    box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(64),
                    spacing=dp(2))
    lbl = Label(text=texto, size_hint_y=None, height=dp(22), halign="left",
                valign="middle", color=(0.2, 0.24, 0.29, 1), font_size=dp(13))
    lbl.bind(size=lambda i, s: setattr(i, "text_size", s))
    ti = TextInput(text=valor, multiline=False, size_hint_y=None, height=dp(40),
                   input_filter="int" if numerico else None,
                   font_size=dp(16), padding=[dp(8), dp(8)])
    box.add_widget(lbl)
    box.add_widget(ti)
    return box, ti


class Raiz(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation="vertical", **kw)
        self.app = app
        self.resultado = None

        # cabeçalho
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70),
                           padding=[dp(16), dp(10)])
        with header.canvas.before:
            from kivy.graphics import Color, Rectangle
            self._hc = Color(11 / 255, 61 / 255, 107 / 255, 1)
            self._hr = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(self._hr, "pos", v),
                    size=lambda i, v: setattr(self._hr, "size", v))
        t1 = Label(text="Assentos UECE", bold=True, font_size=dp(20),
                   color=(1, 1, 1, 1), halign="left", valign="middle")
        t1.bind(size=lambda i, s: setattr(i, "text_size", s))
        t2 = Label(text="Res. 1779/2022-CONSU, Art. 2o", font_size=dp(12),
                   color=(0.85, 0.9, 0.95, 1), halign="left", valign="middle")
        t2.bind(size=lambda i, s: setattr(i, "text_size", s))
        header.add_widget(t1)
        header.add_widget(t2)
        self.add_widget(header)

        # formulário rolável
        scroll = ScrollView()
        form = BoxLayout(orientation="vertical", size_hint_y=None,
                         padding=dp(16), spacing=dp(8))
        form.bind(minimum_height=form.setter("height"))

        bu, self.unidade = _campo("Centro / Faculdade / Instituto")
        bd, self.direcao = _campo("Direcao (Diretor + Vice; use 1 se nao houver Vice)", "2", True)
        bg, self.grad = _campo("Coordenadores de Graduacao", "0", True)
        bs, self.stricto = _campo("Coordenadores de Pos Stricto Sensu", "0", True)
        for b in (bu, bd, bg, bs):
            form.add_widget(b)

        # lato sensu (botão alterna Sim/Nao)
        self.lato_on = False
        self.btn_lato = Button(text="Oferta Lato Sensu?  NAO", size_hint_y=None,
                               height=dp(44), background_color=(0.8, 0.83, 0.87, 1),
                               color=(0.1, 0.12, 0.15, 1))
        self.btn_lato.bind(on_release=self._toggle_lato)
        form.add_widget(self.btn_lato)

        info = Label(text="Fixo: Docentes = 6 (Art. 2o, I).", size_hint_y=None,
                     height=dp(22), color=(0.4, 0.45, 0.5, 1), font_size=dp(12),
                     halign="left", valign="middle")
        info.bind(size=lambda i, s: setattr(i, "text_size", s))
        form.add_widget(info)

        # botões
        linha = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        b_calc = Button(text="Calcular", background_color=(0.07, 0.32, 0.6, 1),
                        color=(1, 1, 1, 1), bold=True)
        b_calc.bind(on_release=self.on_calcular)
        self.b_pdf = Button(text="Gerar PDF", background_color=(0.12, 0.48, 0.24, 1),
                            color=(1, 1, 1, 1), bold=True, disabled=True)
        self.b_pdf.bind(on_release=self.on_pdf)
        linha.add_widget(b_calc)
        linha.add_widget(self.b_pdf)
        form.add_widget(linha)

        # resultado
        self.res = Label(text="", size_hint_y=None, markup=True, font_size=dp(14),
                         color=(0.12, 0.15, 0.18, 1), halign="left", valign="top")
        self.res.bind(width=lambda i, w: setattr(i, "text_size", (w, None)),
                      texture_size=lambda i, s: setattr(i, "height", s[1]))
        form.add_widget(self.res)

        scroll.add_widget(form)
        self.add_widget(scroll)

    def _toggle_lato(self, *_):
        self.lato_on = not self.lato_on
        self.btn_lato.text = "Oferta Lato Sensu?  " + ("SIM" if self.lato_on else "NAO")
        self.btn_lato.background_color = ((0.12, 0.48, 0.24, 1) if self.lato_on
                                          else (0.8, 0.83, 0.87, 1))
        self.btn_lato.color = ((1, 1, 1, 1) if self.lato_on else (0.1, 0.12, 0.15, 1))

    def _int(self, ti):
        try:
            return max(0, int(ti.text or "0"))
        except ValueError:
            return 0

    def on_calcular(self, *_):
        r = calcular(self._int(self.grad), self._int(self.stricto),
                     self.lato_on, max(1, self._int(self.direcao)))
        self.resultado = r
        self.res.text = (
            "[b]Composicao do Conselho[/b]\n"
            "Membros natos: %d\n"
            "Representantes docentes: %d\n"
            "Assentos STA: %d  (%s%%)\n"
            "Assentos discentes: %d  (%s%%)\n"
            "[b]Total de vagas: %d[/b]\n"
            "STA + discentes = %s%% do Conselho."
            % (r["natos"], r["docentes"], r["sta"], fmt(r["pct_sta"]),
               r["dis"], fmt(r["pct_dis"]), r["total"], fmt(r["pct_conjunto"]))
        )
        self.b_pdf.disabled = False

    def on_pdf(self, *_):
        if not self.resultado:
            return
        nome = (self.unidade.text or "unidade").strip()
        safe = "".join(c if c.isalnum() else "_" for c in nome)[:40] or "unidade"
        fname = "assentos_%s.pdf" % safe

        paths = []
        priv = os.path.join(self.app.user_data_dir, fname)
        try:
            gerar_pdf(self.unidade.text, self.resultado, priv)
            paths.append(priv)
        except Exception as e:
            self._popup("Erro ao gerar PDF", str(e))
            return

        shared = _shared_download_dir()
        if shared:
            try:
                dest = os.path.join(shared, fname)
                with open(priv, "rb") as a, open(dest, "wb") as b:
                    b.write(a.read())
                paths.append(dest)
            except Exception:
                pass

        self._popup("PDF gerado", "\n".join(paths))

    def _popup(self, titulo, texto):
        lbl = Label(text=texto, halign="left", valign="top")
        lbl.bind(size=lambda i, s: setattr(i, "text_size", s))
        Popup(title=titulo, content=lbl, size_hint=(0.9, 0.5)).open()


class AssentosApp(App):
    title = "Assentos UECE"

    def build(self):
        return Raiz(self)

    def on_start(self):
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                                 Permission.READ_EXTERNAL_STORAGE])
        except Exception:
            pass


if __name__ == "__main__":
    AssentosApp().run()

