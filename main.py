"""
Assentos UECE — cálculo dos quantitativos de assentos dos Conselhos de
Centro/Faculdade/Instituto (Res. 1779/2022-CONSU, Art. 2º) e geração de PDF.
Interface em Kivy puro e gerador de PDF em Python puro (sem dependências
nativas), para máxima estabilidade no Android.

Regras:
- Membros natos = Direção (editável, padrão 2: Diretor + Vice) + coord. graduação
  + coord. pós stricto sensu + 1 rep. lato sensu (se houver).
- Representantes docentes = 6 (fixo, Art. 2º, I).
- Total de vagas do Conselho = (natos + 6) / 0,70  (natos + docentes = 70%).
- STA = discentes = 15% do total, arredondado PARA CIMA (>= 15% cada; iguais).
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

    sta = int(math.ceil(prop_exata))
    dis = sta
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


# ------------------------------- gerador de PDF (Python puro, sem libs nativas)

AZUL = (11, 61, 107)
AZUL2 = (18, 83, 154)
VERDE = (30, 122, 61)
AMARELO = (242, 194, 0)
CINZA = (90, 100, 115)

_HELV_W = {
    ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667, "'": 191,
    '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278,
    '0': 556, '1': 556, '2': 556, '3': 556, '4': 556, '5': 556, '6': 556, '7': 556,
    '8': 556, '9': 556, ':': 278, ';': 278, '<': 584, '=': 584, '>': 584, '?': 556,
    '@': 1015, 'A': 667, 'B': 667, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778,
    'H': 722, 'I': 278, 'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778,
    'P': 667, 'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944,
    'X': 667, 'Y': 667, 'Z': 611, '[': 278, '\\': 278, ']': 278, '^': 469, '_': 556,
    '`': 333, 'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556, 'f': 278, 'g': 556,
    'h': 556, 'i': 222, 'j': 222, 'k': 500, 'l': 222, 'm': 833, 'n': 556, 'o': 556,
    'p': 556, 'q': 556, 'r': 333, 's': 500, 't': 278, 'u': 556, 'v': 500, 'w': 722,
    'x': 500, 'y': 500, 'z': 500, '{': 334, '|': 260, '}': 334, '~': 584,
}

_ACENTOS = {
    'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a', 'é': 'e', 'ê': 'e', 'è': 'e',
    'ë': 'e', 'í': 'i', 'î': 'i', 'ì': 'i', 'ï': 'i', 'ó': 'o', 'õ': 'o', 'ô': 'o',
    'ò': 'o', 'ö': 'o', 'ú': 'u', 'û': 'u', 'ù': 'u', 'ü': 'u', 'ç': 'c', 'ñ': 'n',
    'Á': 'A', 'Ã': 'A', 'Â': 'A', 'À': 'A', 'É': 'E', 'Ê': 'E', 'Í': 'I', 'Ó': 'O',
    'Õ': 'O', 'Ô': 'O', 'Ú': 'U', 'Ç': 'C', 'º': 'o', 'ª': 'a', '§': 'S', '–': '-',
    '—': '-', '•': '-', '“': '"', '”': '"', '’': "'", '→': '->',
}


def _ascii(s):
    s = "".join(_ACENTOS.get(c, c) for c in str(s))
    return s.encode("ascii", "replace").decode("ascii")


class PDFDoc:
    """Escreve um PDF simples (A4) com retângulos, linhas e texto Helvetica."""

    def __init__(self, w=595.0, h=842.0):
        self.W = w
        self.H = h
        self.ops = []

    def _col(self, c):
        return "%.3f %.3f %.3f" % (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)

    def fill_rect(self, x, y, w, h, color):
        self.ops.append("%s rg %.2f %.2f %.2f %.2f re f"
                        % (self._col(color), x, self.H - y - h, w, h))

    def hline(self, x1, x2, y, color, width=0.5):
        self.ops.append("%s RG %.2f w %.2f %.2f m %.2f %.2f l S"
                        % (self._col(color), width, x1, self.H - y, x2, self.H - y))

    def text_width(self, s, size):
        return sum(_HELV_W.get(c, 556) for c in s) / 1000.0 * size

    def text(self, x, y, s, size, color, bold=False, align="L"):
        s = _ascii(s).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        w = self.text_width(s, size)
        if align == "R":
            x -= w
        elif align == "C":
            x -= w / 2.0
        font = "F2" if bold else "F1"
        base = self.H - y - size
        self.ops.append("BT /%s %.2f Tf %s rg %.2f %.2f Td (%s) Tj ET"
                        % (font, size, self._col(color), x, base, s))

    def save(self, path):
        content = "\n".join(self.ops).encode("latin-1", "replace")
        objs = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.0f %.0f] "
             "/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>"
             % (self.W, self.H)).encode("latin-1"),
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        ]
        out = b"%PDF-1.4\n"
        offsets = []
        for i, o in enumerate(objs, start=1):
            offsets.append(len(out))
            out += ("%d 0 obj\n" % i).encode() + o + b"\nendobj\n"
        xref_pos = len(out)
        out += ("xref\n0 %d\n" % (len(objs) + 1)).encode()
        out += b"0000000000 65535 f \n"
        for off in offsets:
            out += ("%010d 00000 n \n" % off).encode()
        out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF"
                % (len(objs) + 1, xref_pos)).encode()
        with open(path, "wb") as f:
            f.write(out)
        return path


def gerar_pdf(unidade, r, destino):
    unidade = (unidade or "").strip() or "(unidade nao informada)"
    d = PDFDoc()
    W, H, M = d.W, d.H, 48.0

    # faixa superior
    d.fill_rect(0, 0, W, 96, AZUL)
    d.fill_rect(W - 150, 0, 150, 96, VERDE)
    d.fill_rect(0, 96, W, 4, AMARELO)
    d.text(M, 24, "UNIVERSIDADE ESTADUAL DO CEARA - UECE", 9, (255, 255, 255))
    d.text(M, 40, "Quantitativo de Assentos do Conselho", 15, (255, 255, 255), bold=True)
    d.text(M, 66, "Res. no 1779/2022-CONSU, Art. 2o - Representacao de STA e Discentes",
           9.5, (255, 255, 255))

    # unidade
    y = 126
    d.text(M, y, unidade, 12, AZUL, bold=True)
    d.hline(M, W - M, y + 20, (225, 232, 240), 0.6)
    y += 38

    # cartões numéricos
    gap = 12.0
    cw = (W - 2 * M - 3 * gap) / 4.0
    cards = [
        (r["natos"], "Membros natos", AZUL2),
        (r["docentes"], "Rep. docentes", AZUL2),
        (r["sta"], "Assentos STA", VERDE),
        (r["dis"], "Assentos discentes", VERDE),
    ]
    for i, (val, lab, cor) in enumerate(cards):
        x = M + i * (cw + gap)
        d.fill_rect(x, y, cw, 54, (245, 248, 250))
        d.text(x + cw / 2, y + 12, str(val), 22, cor, bold=True, align="C")
        d.text(x + cw / 2, y + 40, lab, 7.6, CINZA, align="C")
    y += 54 + 24

    # tabela
    d.text(M, y, "Composicao do Conselho", 11, AZUL, bold=True)
    y += 18
    col_cat = M + 8
    col_n = W - M - 130
    col_pct = W - M - 8
    d.fill_rect(M, y, W - 2 * M, 20, (241, 245, 249))
    d.text(col_cat, y + 6, "CATEGORIA", 8.5, (51, 65, 85), bold=True)
    d.text(col_n, y + 6, "ASSENTOS", 8.5, (51, 65, 85), bold=True, align="R")
    d.text(col_pct, y + 6, "% DO TOTAL", 8.5, (51, 65, 85), bold=True, align="R")
    y += 20

    linhas = [
        ("Membros natos", r["natos"], r["pct_natos"]),
        ("Representantes docentes (eleitos)", r["docentes"], r["pct_doc"]),
        ("Representantes tecnico-administrativos (STA)", r["sta"], r["pct_sta"]),
        ("Representantes discentes", r["dis"], r["pct_dis"]),
    ]
    for nome, n, pct in linhas:
        d.text(col_cat, y + 5, nome, 9.5, (31, 41, 55))
        d.text(col_n, y + 5, str(n), 9.5, (31, 41, 55), align="R")
        d.text(col_pct, y + 5, fmt(pct) + "%", 9.5, (31, 41, 55), align="R")
        d.hline(M, W - M, y + 20, (230, 235, 242), 0.5)
        y += 20

    # total
    d.fill_rect(M, y, W - 2 * M, 22, (247, 250, 248))
    d.hline(M, W - M, y, VERDE, 1.4)
    d.text(col_cat, y + 6, "Total de vagas do Conselho", 9.5, AZUL, bold=True)
    d.text(col_n, y + 6, str(r["total"]), 9.5, AZUL, bold=True, align="R")
    d.text(col_pct, y + 6, "100%", 9.5, AZUL, bold=True, align="R")
    y += 42

    # memória de cálculo
    d.fill_rect(M, y, W - 2 * M, 104, (251, 252, 254))
    d.fill_rect(M, y, 4, 104, AMARELO)
    d.text(M + 14, y + 10, "Memoria de calculo", 9, CINZA, bold=True)
    mem = [
        "Membros natos = Direcao (%d) + Graduacao (%d) + Stricto sensu (%d) + Lato sensu (%d) = %d."
        % (r["direcao"], r["grad"], r["stricto"], r["lato"], r["natos"]),
        "Total de vagas = (natos %d + 6 docentes) / 0,70 = %s   (natos + docentes = 70%%)."
        % (r["natos"], fmt(r["total_exato"])),
        "15%% sobre o total (Art. 2o, II e III) = %s -> arredondado p/ cima = %d por categoria."
        % (fmt(r["prop_exata"]), r["sta"]),
        "STA + discentes = %d assentos = %s%% do Conselho. Cada categoria = %s%% (>= 15%%)."
        % (r["m"], fmt(r["pct_conjunto"]), fmt(r["pct_sta"])),
    ]
    yy = y + 30
    for t in mem:
        d.text(M + 14, yy, t, 8.6, (70, 80, 95))
        yy += 17
    y += 104 + 20

    d.text(M, y, "Fundamentos: Art. 2o, II, III e paragrafos 2o e 6o da Res. 1779/2022-CONSU;",
           8, CINZA)
    d.text(M, y + 12, "item VI do art. 47 do Regimento Geral da UECE. Quantitativos definidos pelo Conselho.",
           8, CINZA)

    # rodapé
    hy = H - 34
    d.hline(M, W - M, hy, (225, 232, 240), 0.6)
    hoje = datetime.now().strftime("%d/%m/%Y")
    d.text(M, hy + 6,
           "Gerado em %s - UECE - Av. Dr. Silas Munguba, 1700 - Campus do Itaperi - Fortaleza/CE" % hoje,
           7.5, CINZA)

    d.save(destino)
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


def _abrir_pdf(path):
    """Abre o PDF no aplicativo padrao do Android. Retorna True se conseguiu."""
    try:
        from jnius import autoclass  # type: ignore
        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        File = autoclass("java.io.File")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        try:
            StrictMode = autoclass("android.os.StrictMode")
            StrictMode.disableDeathOnFileUriExposure()
        except Exception:
            pass
        intent = Intent(Intent.ACTION_VIEW)
        uri = Uri.fromFile(File(path))
        intent.setDataAndType(uri, "application/pdf")
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_GRANT_READ_URI_PERMISSION)
        activity.startActivity(intent)
        return True
    except Exception:
        return False


def _campo(texto, valor="", numerico=False):
    box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(64), spacing=dp(2))
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

        # abre no leitor de PDF padrao (prefere a copia em Download, legivel por outros apps)
        alvo = paths[-1]
        aberto = _abrir_pdf(alvo)
        msg = "Salvo em:\n" + "\n".join(paths)
        if not aberto:
            msg += "\n\n(Abra o arquivo pelo app Arquivos ou Downloads.)"
        self._popup("PDF gerado com sucesso", msg)

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

