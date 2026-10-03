(() => {
  const WHATSAPP = '5543996042401';
  const MSG_GERAL = 'Olá! Vim pelo site da Lord’s Planejados e gostaria de um orçamento.';
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const reduzMovimento = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const celular = matchMedia('(max-width: 900px)');

  // links antigos do catálogo (?ambiente= e ?projeto=) levam para as páginas novas
  const q = new URLSearchParams(location.search);
  if (/projetos\.html$/.test(location.pathname)) {
    if (q.get('projeto')) { location.replace(`projeto/${q.get('projeto')}.html`); return; }
    if (q.get('ambiente')) { location.replace(`${q.get('ambiente')}.html`); return; }
  }

  // ---------- WhatsApp e ano ----------

  $$('[data-wa]').forEach((a) => {
    a.href = `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(a.dataset.msg || MSG_GERAL)}`;
    a.target = '_blank';
    a.rel = 'noopener';
  });
  $$('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });

  // ---------- Sem palavra sozinha na última linha ----------
  // Troca o último espaço de cada bloco de texto por um espaço que não quebra,
  // assim as duas últimas palavras sempre descem juntas.

  const NBSP = ' ';
  const amarrar = (el) => {
    const nos = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) nos.push(walker.currentNode);
    const texto = nos.map((n) => n.data).join('');
    // com duas palavras só, juntar as duas impediria a quebra de linha
    if (texto.trim().split(/\s+/).length < 3) return;
    const m = texto.match(/\S([ \t\r\n]+)\S+\s*$/);
    if (!m) return;
    const ini = m.index + 1;
    const fim = ini + m[1].length;
    // espaço que separa dois blocos não é espaço entre palavras
    const blocos = (n) => [n.previousSibling, n.nextSibling].some((v) => v && v.nodeType === 1 && getComputedStyle(v).display !== 'inline');
    let p0 = 0;
    for (const n of nos) {
      const a = p0;
      p0 += n.data.length;
      if (p0 > ini && a < fim && !n.data.trim() && blocos(n)) return;
    }
    const originais = nos.map((n) => n.data);
    let pos = 0;
    let feito = false;
    nos.forEach((n) => {
      const a = pos;
      const b = pos + n.data.length;
      pos = b;
      if (b <= ini || a >= fim) return;
      const s = Math.max(ini, a) - a;
      const e = Math.min(fim, b) - a;
      n.data = n.data.slice(0, s) + (feito ? '' : NBSP) + n.data.slice(e);
      feito = true;
    });
    // se as duas palavras juntas não cabem na largura, volta ao texto original
    if (el.scrollWidth > el.clientWidth + 1) nos.forEach((n, i) => { n.data = originais[i]; });
  };
  $$('h1, h2, h3, p, figcaption, dd, .label, summary > span, .card__title, .feat__title, .room__name, .row__title, .btn > span, .link > span').forEach(amarrar);

  // ---------- Cabeçalho e menu ----------

  const header = $('[data-header]');
  const menu = $('[data-menu]');
  const menuBtn = $('[data-menu-btn]');
  const fab = $('[data-fab]');
  const hero = $('.hero');
  const fora = $$('main, footer, .fab');
  let menuAberto = false;

  const ocultar = (sim) => {
    header.classList.toggle('is-hidden', sim);
    document.documentElement.classList.toggle('header-oculto', sim);
  };

  // na home o cabeçalho fica transparente enquanto está sobre a foto
  const atualizarSobreHero = () => {
    const sobre = header.classList.contains('header--over') && hero && !menuAberto &&
      window.scrollY < hero.offsetHeight - header.offsetHeight;
    header.classList.toggle('is-over', Boolean(sobre));
  };

  const abrirMenu = (abrir, peloTeclado = false) => {
    menuAberto = abrir;
    menu.classList.toggle('is-open', abrir);
    header.classList.toggle('is-menu', abrir);
    ocultar(false);
    menuBtn.setAttribute('aria-expanded', String(abrir));
    menuBtn.setAttribute('aria-label', abrir ? 'Fechar menu' : 'Abrir menu');
    document.documentElement.style.overflow = abrir ? 'hidden' : '';
    fora.forEach((el) => { el.inert = abrir; });
    if (abrir && peloTeclado) $('a', menu).focus({ preventScroll: true });
    atualizarSobreHero();
    atualizarFab();
  };
  // detail 0 = ativado pelo teclado; só nesse caso o foco pula para o primeiro link
  menuBtn.addEventListener('click', (e) => abrirMenu(!menuAberto, e.detail === 0));
  menu.addEventListener('click', (e) => { if (e.target.closest('a')) abrirMenu(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menuAberto) { abrirMenu(false); menuBtn.focus(); }
  });
  celular.addEventListener('change', () => {
    if (!celular.matches && menuAberto) abrirMenu(false);
    ocultar(false);
    atualizarSobreHero();
  });

  // no celular o cabeçalho sobe ao rolar para baixo e volta ao rolar para cima
  let ultimoY = window.scrollY;
  const onScroll = () => {
    const y = window.scrollY;
    atualizarSobreHero();
    if (celular.matches && !menuAberto) {
      if (y > ultimoY + 6 && y > header.offsetHeight) ocultar(true);
      else if (y < ultimoY - 6 || y <= header.offsetHeight) ocultar(false);
    }
    ultimoY = y;
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ---------- Botão flutuante do WhatsApp ----------
  // Some quando já existe outro botão de WhatsApp na tela e volta quando não há nenhum.

  const visiveis = new Set();
  function atualizarFab() {
    fab.classList.toggle('is-on', visiveis.size === 0 && !menuAberto);
  }
  const botoesWa = $$('.btn[data-wa]').filter((b) => !b.closest('.header, .menu'));
  if ('IntersectionObserver' in window) {
    const ioWa = new IntersectionObserver((entries) => {
      entries.forEach((en) => (en.isIntersecting ? visiveis.add(en.target) : visiveis.delete(en.target)));
      atualizarFab();
    });
    botoesWa.forEach((b) => ioWa.observe(b));
    atualizarFab();
  } else {
    fab.classList.add('is-on');
  }

  // ---------- Entradas ----------

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    $$('.reveal').forEach((el) => io.observe(el));
  } else {
    $$('.reveal').forEach((el) => el.classList.add('is-in'));
  }

  // ---------- Perguntas: abrir e fechar com suavidade ----------

  $$('.qa').forEach((d) => {
    const resumo = $('summary', d);
    const corpo = $('.qa__body', d);
    if (!corpo) return;
    d.classList.toggle('is-open', d.open);
    let anim = null;
    resumo.addEventListener('click', (e) => {
      e.preventDefault();
      const abrir = !d.classList.contains('is-open');
      d.classList.toggle('is-open', abrir);
      if (anim) anim.cancel();
      if (reduzMovimento) { d.open = abrir; return; }
      const altura = corpo.offsetHeight;
      if (abrir) {
        d.open = true;
        const alvo = corpo.scrollHeight;
        anim = corpo.animate(
          [{ height: `${altura && altura < alvo ? altura : 0}px`, opacity: 0 }, { height: `${alvo}px`, opacity: 1 }],
          { duration: 420, easing: 'cubic-bezier(.2, .7, .2, 1)' }
        );
      } else {
        anim = corpo.animate(
          [{ height: `${altura}px`, opacity: 1 }, { height: '0px', opacity: 0 }],
          { duration: 320, easing: 'cubic-bezier(.4, 0, .2, 1)' }
        );
      }
      anim.onfinish = abrir ? () => { anim = null; } : () => { d.open = false; anim = null; };
    });
  });

  // ---------- Hero: troca de fotos ----------

  const slidesEl = $('[data-slides]');
  if (slidesEl) {
    const slides = $$('[data-slide]', slidesEl);
    const num = $('[data-slide-num]');
    const barra = $('[data-slide-bar]');
    const TEMPO = 6500;
    let atual = 0;
    const ir = (i) => {
      atual = (i + slides.length) % slides.length;
      slides.forEach((s, k) => s.classList.toggle('is-active', k === atual));
      $('img', slides[atual]).loading = 'eager';
      if (num) num.textContent = String(atual + 1).padStart(2, '0');
      if (barra && !reduzMovimento) {
        barra.classList.remove('is-running');
        void barra.offsetWidth;
        barra.style.setProperty('--dur', `${TEMPO}ms`);
        barra.classList.add('is-running');
      }
    };
    let timer = null;
    const tocar = () => {
      clearInterval(timer);
      if (reduzMovimento) return;
      timer = setInterval(() => ir(atual + 1), TEMPO);
    };
    document.addEventListener('visibilitychange', () => (document.hidden ? clearInterval(timer) : tocar()));
    window.addEventListener('load', () => slides.forEach((s) => { $('img', s).loading = 'eager'; }));
    ir(0);
    tocar();
  }

  // ---------- Carrossel de fotos do projeto (celular) ----------

  $$('[data-carousel]').forEach((trilho) => {
    const nav = trilho.parentElement.querySelector('[data-carousel-nav]');
    if (!nav) return;
    const marcas = $$('button', nav);
    const atual = () => Math.round(trilho.scrollLeft / (trilho.clientWidth || 1));
    let quadro = 0;
    const marcar = () => {
      quadro = 0;
      const i = atual();
      marcas.forEach((b, k) => b.setAttribute('aria-current', String(k === i)));
    };
    trilho.addEventListener('scroll', () => { if (!quadro) quadro = requestAnimationFrame(marcar); }, { passive: true });
    marcas.forEach((b, k) => b.addEventListener('click', () => {
      trilho.scrollTo({ left: k * trilho.clientWidth, behavior: reduzMovimento ? 'auto' : 'smooth' });
    }));
    // setas do teclado quando o carrossel está em foco
    trilho.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      if (trilho.scrollWidth <= trilho.clientWidth) return;
      e.preventDefault();
      const alvo = Math.max(0, Math.min(marcas.length - 1, atual() + (e.key === 'ArrowRight' ? 1 : -1)));
      trilho.scrollTo({ left: alvo * trilho.clientWidth, behavior: reduzMovimento ? 'auto' : 'smooth' });
    });
  });

  // ---------- Copiar e compartilhar ----------

  const copiar = async (texto) => {
    try {
      await navigator.clipboard.writeText(texto);
      return true;
    } catch (err) {
      const t = document.createElement('textarea');
      t.value = texto;
      t.style.cssText = 'position:fixed;opacity:0';
      document.body.appendChild(t);
      t.select();
      const ok = document.execCommand('copy');
      t.remove();
      return ok;
    }
  };
  const avisar = (el, texto) => {
    const alvo = $('span', el) || el;
    const antes = alvo.dataset.original || alvo.textContent;
    alvo.dataset.original = antes;
    alvo.textContent = texto;
    clearTimeout(el.aviso);
    el.aviso = setTimeout(() => { alvo.textContent = antes; }, 2200);
  };

  // página de projeto: no celular abre o compartilhar do aparelho; no computador copia o link
  $$('[data-share]').forEach((b) => b.addEventListener('click', async () => {
    const url = location.href.split('#')[0];
    if (navigator.share && matchMedia('(pointer: coarse)').matches) {
      try { await navigator.share({ title: b.dataset.title, text: `${b.dataset.title} · Lord’s Planejados`, url }); } catch (e) { /* cancelado */ }
      return;
    }
    avisar(b, (await copiar(url)) ? 'Link copiado' : 'Não foi possível copiar');
  }));

  // ---------- Área de atendimento ----------

  const absoluto = (caminho) => new URL(caminho, location.href).href;
  $$('[data-copiar]').forEach((b) => b.addEventListener('click', async () => {
    avisar(b, (await copiar(absoluto(b.dataset.copiar))) ? 'Copiado' : 'Erro ao copiar');
  }));
  // wa.me sem número abre o WhatsApp para escolher o contato
  $$('[data-enviar]').forEach((b) => b.addEventListener('click', () => {
    const msg = `${b.dataset.texto} ${absoluto(b.dataset.enviar)}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`, '_blank', 'noopener');
  }));

  const campo = $('[data-busca-campo]');
  if (campo) {
    const normalizar = (t) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    const linhas = $$('[data-busca]').map((li) => ({ li, texto: normalizar(`${li.dataset.busca} ${li.textContent}`) }));
    const vazio = $('[data-busca-vazio]');
    campo.addEventListener('input', () => {
      const termos = normalizar(campo.value).split(/\s+/).filter(Boolean);
      let total = 0;
      linhas.forEach(({ li, texto }) => {
        const ok = termos.every((t) => texto.includes(t));
        li.hidden = !ok;
        if (ok) total++;
      });
      $$('[data-grupo]').forEach((g) => { g.hidden = !$$('[data-busca]:not([hidden])', g).length; });
      vazio.hidden = total > 0;
    });
  }
})();
