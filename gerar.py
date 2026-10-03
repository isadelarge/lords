"""Gera as páginas do site da Lord's Planejados.

Fontes:
  dados/projetos.json   projetos, ambientes e destaques
  modelos/*.html        páginas; arquivos que começam com _ são partes reaproveitadas

Uso:
  python gerar.py

Escreve na raiz: index.html, projetos.html, uma página por ambiente (cozinhas.html...),
atendimento.html, 404.html e projeto/<slug>.html para cada projeto.
"""
import glob
import hashlib
import html
import json
import os
import re
import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
RAIZ = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)

DADOS = json.load(open('dados/projetos.json', encoding='utf-8'))
SITE = DADOS.get('site', '').rstrip('/')
WHATSAPP = DADOS['whatsapp']


def ler(caminho):
    return open(caminho, encoding='utf-8').read()


def versao():
    h = hashlib.md5()
    for f in ('assets/style.css', 'assets/app.js'):
        h.update(open(f, 'rb').read())
    return h.hexdigest()[:8]


VERSAO = versao()


def render(modelo, ctx):
    texto = ler(f'modelos/{modelo}')
    # partes: {{> nome}}
    for _ in range(3):
        texto = re.sub(r'\{\{>\s*(\w+)\s*\}\}', lambda m: ler(f'modelos/_{m.group(1)}.html'), texto)
    base = {'versao': VERSAO, 'robots': '', 'preload': '', 'extra_head': '', 'og_url': '',
            'atual_projetos': '', 'header_classe': ''}
    base.update(ctx)

    def troca(m):
        chave = m.group(1)
        if chave not in base:
            raise KeyError(f'{modelo}: falta "{chave}"')
        return str(base[chave])
    return re.sub(r'\{\{\s*(\w+)\s*\}\}', troca, texto)


def escrever(caminho, conteudo):
    os.makedirs(os.path.dirname(caminho) or '.', exist_ok=True)
    open(caminho, 'w', encoding='utf-8', newline='\n').write(conteudo)


def esc(t):
    return html.escape(t, quote=True)


# ---------- dados ----------

PROJETOS = []
for a in DADOS['ambientes']:
    for p in a['projetos']:
        PROJETOS.append({**p, 'ambiente': a, 'rotulo': p.get('rotulo') or a['rotulo']})
POR_SLUG = {p['slug']: p for p in PROJETOS}
ORDEM_TODOS = [POR_SLUG[s] for s in DADOS['destaque'] if s in POR_SLUG] + \
              [p for p in PROJETOS if p['slug'] not in DADOS['destaque']]

_tamanhos = {}


def tamanho(caminho):
    if caminho not in _tamanhos:
        _tamanhos[caminho] = Image.open(caminho).size
    return _tamanhos[caminho]


def foto(p, n, mini=False):
    pasta = f"assets/fotos/{p['ambiente']['slug']}" + ('/mini' if mini else '')
    return f"{pasta}/{p['slug']}-{n}.jpg"


# ---------- prévia do link (WhatsApp, redes) ----------
# Corte horizontal 1200x630 da capa de cada projeto. "previa" no JSON é a posição do corte:
# 0 = topo (ou esquerda, em foto larga), 0.5 = centro, 1 = base (ou direita).

RAZAO_PREVIA = 1200 / 630


def previa(p):
    return cortar_previa(foto(p, 1), float(p.get('previa', 0.5)), f"assets/previa/{p['slug']}.jpg")


def cortar_previa(origem, pos, destino):
    im = Image.open(origem).convert('RGB')
    w, h = im.size
    if w / h > RAZAO_PREVIA:
        cw = int(h * RAZAO_PREVIA)
        x = int((w - cw) * pos)
        im = im.crop((x, 0, x + cw, h))
    else:
        ch = int(w / RAZAO_PREVIA)
        y = int((h - ch) * pos)
        im = im.crop((0, y, w, y + ch))
    im = im.resize((1200, 630), Image.LANCZOS)
    os.makedirs('assets/previa', exist_ok=True)
    im.save(destino, 'JPEG', quality=84, optimize=True, progressive=True)
    return destino


def img(caminho, raiz, alt='', classe='', lazy=True, extra=''):
    w, h = tamanho(caminho)
    attrs = [f'src="{raiz}{caminho}"', f'alt="{esc(alt)}"', f'width="{w}"', f'height="{h}"', 'decoding="async"']
    if lazy:
        attrs.append('loading="lazy"')
    if classe:
        attrs.append(f'class="{classe}"')
    if extra:
        attrs.append(extra)
    return f"<img {' '.join(attrs)}>"


def abs_url(caminho):
    return f'{SITE}/{caminho}' if SITE else caminho


def ctx_pagina(raiz, titulo, descricao, og_imagem, url, eh_home=False, og_alt='Projeto de móveis planejados da Lord’s Planejados'):
    return {
        'raiz': raiz,
        'inicio': (raiz or './') if not eh_home else './',
        'ancora': '' if eh_home else (raiz or './'),
        'titulo': esc(titulo),
        'descricao': esc(descricao),
        'og_imagem': abs_url(og_imagem) if SITE else f'{raiz}{og_imagem}',
        'og_alt': esc(og_alt),
        'og_url': f'<meta property="og:url" content="{abs_url(url)}">' if SITE else '',
    }


def card(p, raiz, eager=False):
    fotos = '1 foto' if p['fotos'] == 1 else f"{p['fotos']} fotos"
    return f'''
        <li class="card" data-ambiente="{p['ambiente']['slug']}">
          <a class="card__link" href="{raiz}projeto/{p['slug']}.html">
            <span class="card__media">{img(foto(p, 1, mini=True), raiz, lazy=not eager)}</span>
            <span class="card__meta"><span class="label">{esc(p['rotulo'])} · {fotos}</span><span class="card__title">{esc(p['titulo'])}</span></span>
          </a>
        </li>'''


# ---------- home ----------

def gerar_home():
    salas = []
    for a in DADOS['ambientes']:
        capa = f"assets/fotos/{a['slug']}/mini/{a['capa']}.jpg"
        salas.append(f'''
        <li class="room">
          <a class="room__link" href="{a['slug']}.html">
            <span class="room__media">{img(capa, '')}</span>
            <span class="room__name">{esc(a['nome'])}</span>
            <svg class="i room__arrow" aria-hidden="true"><use href="#i-arrow"/></svg>
          </a>
        </li>''')

    feats = []
    for i, s in enumerate(DADOS['home_destaques']):
        p = POR_SLUG[s]
        largo = i in (0, 3)
        feats.append(f'''
        <li class="feat__item{' feat__item--wide' if largo else ''}">
          <a class="feat__link" href="projeto/{p['slug']}.html">
            <span class="feat__media">{img(foto(p, 1), '')}</span>
            <span class="feat__meta">
              <span class="label label--light">{esc(p['rotulo'])}</span>
              <span class="feat__title">{esc(p['titulo'])}</span>
            </span>
          </a>
        </li>''')

    ctx = ctx_pagina('', 'Lord’s Planejados · Móveis planejados em Londrina',
                     'Móveis planejados sob medida em Londrina e região. Cozinhas, dormitórios, salas, banheiros e ambientes comerciais, com visita e medição sem custo e parcelamento em até 18x.',
                     'assets/og.jpg', '', eh_home=True)
    ctx.update({
        'header_classe': 'header--over',
        'preload': '<link rel="preload" as="image" href="assets/fotos/dormitorios/grafite-cabeceira-1.jpg">',
        'extra_head': ler('modelos/_schema.html'),
        'ambientes': ''.join(salas),
        'destaques': ''.join(feats),
        'img_arquitetos': img('assets/fotos/comercial/sala-reuniao-1.jpg', '', alt='Sala de reunião com painel amadeirado, mesa grafite e frisos de LED'),
    })
    escrever('index.html', render('index.html', ctx))


# ---------- catálogo (todos e por ambiente) ----------

def abas(atual):
    itens = [('projetos.html', 'Todos', 'todos')] + [(f"{a['slug']}.html", a['nome'], a['slug']) for a in DADOS['ambientes']]
    return ''.join(
        f'<a href="{href}"{" aria-current=\"page\"" if slug == atual else ""}>{esc(nome)}</a>'
        for href, nome, slug in itens)


def gerar_catalogos():
    paginas = [('projetos.html', 'todos', 'Projetos entregues', 'Projetos',
                'Ambientes que a Lord’s projetou e montou em Londrina e região. Escolha um projeto para ver todas as fotos.',
                ORDEM_TODOS, 'Projetos · Lord’s Planejados',
                'Projetos de móveis planejados entregues pela Lord’s em Londrina e região.', 'assets/og.jpg')]
    for a in DADOS['ambientes']:
        lista = [p for p in PROJETOS if p['ambiente']['slug'] == a['slug']]
        paginas.append((f"{a['slug']}.html", a['slug'], a['nome'], 'Projetos',
                        a.get('texto') or f"{a['frase']} sob medida que a Lord’s entregou em Londrina e região.",
                        lista, f"{a['frase']} · Lord’s Planejados",
                        f"Veja {a['frase'].lower()} sob medida pela Lord’s em Londrina e região.",
                        f"assets/previa/{a['capa'].rsplit('-', 1)[0]}.jpg"))
    for arq, slug, h1, rotulo, texto, lista, titulo, desc, og in paginas:
        ctx = ctx_pagina('', titulo, desc, og, arq)
        ctx.update({
            'atual_projetos': ' aria-current="page"',
            'h1': esc(h1), 'rotulo': rotulo, 'texto': esc(texto),
            'abas': abas(slug),
            'cards': ''.join(card(p, '', eager=i < 6) for i, p in enumerate(lista)),
        })
        escrever(arq, render('catalogo.html', ctx))


# ---------- páginas de projeto ----------

def gerar_projetos():
    for antigo in glob.glob('projeto/*.html'):
        os.remove(antigo)
    for p in PROJETOS:
        a = p['ambiente']
        irmaos = [x for x in PROJETOS if x['ambiente']['slug'] == a['slug']]
        i = irmaos.index(p)
        ant, prox = irmaos[i - 1], irmaos[(i + 1) % len(irmaos)]

        galeria = ''.join(
            f'<figure class="project__photo">{img(foto(p, n), "../", alt=f"{p["titulo"]}, foto {n} de {p["fotos"]}", lazy=n > 1)}</figure>'
            for n in range(1, p['fotos'] + 1))

        obra = ''
        if p.get('obra'):
            outros = [x for x in PROJETOS if x.get('obra') == p['obra'] and x['slug'] != p['slug']]
            if outros:
                links = ''.join(f'<a href="{x["slug"]}.html">{esc(x["rotulo"])}</a>' for x in outros)
                obra = f'<div class="project__obra"><p class="label">Outros ambientes deste imóvel</p><div class="project__obra-links">{links}</div></div>'

        pager = ''
        if len(irmaos) > 1:
            pager = f'''
    <nav class="pager" aria-label="Outros projetos de {esc(a['nome'].lower())}">
      <a class="pager__btn" href="{ant['slug']}.html" aria-label="Projeto anterior: {esc(ant['titulo'])}" title="Projeto anterior"><svg class="i" aria-hidden="true"><use href="#i-arrow-l"/></svg></a>
      <a class="pager__btn" href="{prox['slug']}.html" aria-label="Próximo projeto: {esc(prox['titulo'])}" title="Próximo projeto"><svg class="i" aria-hidden="true"><use href="#i-arrow"/></svg></a>
    </nav>'''

        indicadores = ''
        if p['fotos'] > 1:
            botoes = ''.join(
                f'<button type="button" aria-label="Ver foto {n}"{" aria-current=\"true\"" if n == 1 else ""}></button>'
                for n in range(1, p['fotos'] + 1))
            indicadores = f'<div class="carousel-nav" data-carousel-nav>{botoes}</div>'

        rel = [x for x in irmaos if x['slug'] != p['slug']][:3]
        rel += [x for x in ORDEM_TODOS if x not in rel and x['slug'] != p['slug'] and x['ambiente']['slug'] != a['slug']][:3 - len(rel)]

        msg = f'Olá! Vi o projeto “{p["titulo"]}” no site da Lord’s Planejados e gostaria de um orçamento para algo parecido.'
        ctx = ctx_pagina('../', f"{p['titulo']} · Lord’s Planejados", p['texto'], f"assets/previa/{p['slug']}.jpg", f"projeto/{p['slug']}.html",
                         og_alt=p['titulo'])
        ctx.update({
            'atual_projetos': ' aria-current="page"',
            'preload': f'<link rel="preload" as="image" href="../{foto(p, 1)}">',
            'amb_slug': a['slug'], 'amb_nome': esc(a['nome']),
            'rotulo': esc(p['rotulo']), 'titulo_projeto': esc(p['titulo']), 'texto': esc(p['texto']),
            'n_fotos': '1 foto' if p['fotos'] == 1 else f"{p['fotos']} fotos",
            'msg': esc(msg), 'galeria': galeria, 'obra': obra, 'pager': pager, 'indicadores': indicadores,
            'relacionados': ''.join(card(x, '../') for x in rel),
        })
        escrever(f"projeto/{p['slug']}.html", render('projeto.html', ctx))


# ---------- área de atendimento ----------

def linha(thumb, rotulo, titulo, href, texto, busca):
    return f'''
        <li class="row" data-busca="{esc(busca.lower())}">
          {thumb}
          <div class="row__text"><span class="label">{esc(rotulo)}</span><span class="row__title">{esc(titulo)}</span></div>
          <div class="row__actions">
            <a class="btn btn--sm btn--outline" href="{href}" target="_blank" rel="noopener">Abrir</a>
            <button class="btn btn--sm btn--outline" type="button" data-copiar="{href}"><span>Copiar link</span></button>
            <button class="btn btn--sm btn--black" type="button" data-enviar="{href}" data-texto="{esc(texto)}"><svg class="i" aria-hidden="true"><use href="#i-wa"/></svg><span>Enviar</span></button>
          </div>
        </li>'''


def gerar_atendimento():
    gerais = [
        linha('<span class="row__thumb row__thumb--marca"><svg aria-hidden="true"><use href="#marca"/></svg></span>', 'Site', 'Página inicial', './',
              'Conheça a Lord’s Planejados, móveis planejados sob medida em Londrina:', 'inicio site home'),
        linha('<span class="row__thumb row__thumb--marca"><svg aria-hidden="true"><use href="#marca"/></svg></span>', 'Catálogo', 'Todos os projetos', 'projetos.html',
              'Veja os projetos que a Lord’s Planejados já entregou:', 'todos projetos catalogo'),
        linha('<span class="row__thumb row__thumb--marca"><svg aria-hidden="true"><use href="#marca"/></svg></span>', 'Atendimento', 'Como funciona e formas de pagamento', './#como-funciona',
              'Veja como funciona o atendimento da Lord’s Planejados, da visita sem custo à montagem:', 'como funciona pagamento visita medicao 18x'),
        linha('<span class="row__thumb row__thumb--marca"><svg aria-hidden="true"><use href="#marca"/></svg></span>', 'Arquitetos', 'Página para arquitetos e designers', './#arquitetos',
              'Informações da Lord’s Planejados para arquitetos e designers:', 'arquitetos designers parceria'),
    ]
    ambientes = []
    for a in DADOS['ambientes']:
        capa = f"assets/fotos/{a['slug']}/mini/{a['capa']}.jpg"
        ambientes.append(linha(img(capa, '', classe='row__thumb'), 'Ambiente', a['nome'], f"{a['slug']}.html",
                               f"Veja {a['frase'].lower()} que a Lord’s Planejados já entregou:", a['nome']))
    projetos = []
    for p in ORDEM_TODOS:
        projetos.append(linha(img(foto(p, 1, mini=True), '', classe='row__thumb'), p['rotulo'], p['titulo'],
                              f"projeto/{p['slug']}.html", f"Veja este projeto da Lord’s Planejados, {p['titulo'].lower()}:",
                              f"{p['titulo']} {p['rotulo']} {p['ambiente']['nome']} {p['texto']}"))
    ctx = ctx_pagina('', 'Área de atendimento · Lord’s Planejados', 'Links prontos para a equipe enviar aos clientes.', 'assets/og.jpg', 'atendimento.html')
    ctx.update({
        'robots': '<meta name="robots" content="noindex">',
        'gerais': ''.join(gerais), 'lista_ambientes': ''.join(ambientes), 'lista_projetos': ''.join(projetos),
    })
    escrever('atendimento.html', render('atendimento.html', ctx))


def gerar_404():
    ctx = ctx_pagina('/', 'Página não encontrada · Lord’s Planejados', 'Esta página não existe ou mudou de endereço.', 'assets/og.jpg', '404.html')
    ctx.update({'robots': '<meta name="robots" content="noindex">'})
    escrever('404.html', render('404.html', ctx))


def gerar_sitemap():
    if not SITE:
        return
    urls = ['', 'projetos.html'] + [f"{a['slug']}.html" for a in DADOS['ambientes']] + [f"projeto/{p['slug']}.html" for p in PROJETOS]
    corpo = ''.join(f'  <url><loc>{SITE}/{u}</loc></url>\n' for u in urls)
    escrever('sitemap.xml', f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{corpo}</urlset>\n')


if __name__ == '__main__':
    for p in PROJETOS:
        previa(p)
    # prévia da home e do catálogo geral: "home_previa" indica a foto e a posição do corte
    hp = DADOS['home_previa']
    cortar_previa(f"assets/fotos/{hp['foto']}.jpg", float(hp.get('posicao', 0.5)), 'assets/og.jpg')
    gerar_home()
    gerar_catalogos()
    gerar_projetos()
    gerar_atendimento()
    gerar_404()
    gerar_sitemap()
    print(f'Pronto: home, {len(DADOS["ambientes"]) + 1} catálogos, {len(PROJETOS)} projetos, atendimento e 404 (versão {VERSAO}).')
