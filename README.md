# Lord's Planejados · Site

Portfólio de móveis planejados com orçamento pelo WhatsApp. HTML, CSS e JavaScript puros; as páginas são montadas por um script em Python a partir dos modelos e dos dados.

## Estrutura e navegação

| Página | Para quem | O que faz |
| --- | --- | --- |
| `index.html` | Clientes e arquitetos | Apresentação, ambientes, projetos em destaque, como funciona, área para arquitetos, avaliações, contato e dúvidas |
| `projetos.html` | Todos | Catálogo completo com abas por ambiente |
| `cozinhas.html`, `dormitorios.html`, `salas.html`, `banheiros.html`, `comercial.html` | Todos | Catálogo de cada ambiente, com endereço próprio para enviar |
| `projeto/<slug>.html` | Todos | Página de cada projeto, com fotos, botão de orçamento já citando o projeto, compartilhar e anterior/próximo |
| `atendimento.html` | Equipe da marcenaria | Busca e links prontos para copiar ou enviar pelo WhatsApp (fora do Google) |
| `404.html` | Todos | Página de endereço não encontrado |

Cada projeto tem endereço próprio, então o link enviado pelo WhatsApp abre direto nele e o botão voltar do celular funciona como o cliente espera. Links antigos no formato `projetos.html?ambiente=` e `projetos.html?projeto=` são redirecionados.

## Como editar

1. Projetos, ambientes e destaques ficam em `dados/projetos.json`. Cada projeto tem `slug`, `fotos` (quantidade), `titulo`, `texto` e, se fizer parte de um imóvel com outros ambientes, `obra`.
2. Os textos e o layout ficam em `modelos/`. Arquivos que começam com `_` são partes repetidas em todas as páginas (cabeçalho, rodapé, ícones).
3. Depois de qualquer mudança, rode:

```bash
python gerar.py
```

O script recria todas as páginas e atualiza a versão dos arquivos de estilo e script. Não edite os `.html` da raiz nem os de `projeto/` direto, porque eles são sobrescritos.

As fotos ficam em `assets/fotos/<ambiente>/` (até 1600 px) e as miniaturas em `assets/fotos/<ambiente>/mini/` (800 px de largura), com o nome `<slug>-1.jpg`, `<slug>-2.jpg`... Os originais continuam em `Nova pasta/`.

## Prévia do link (WhatsApp)

Cada projeto tem uma imagem de prévia horizontal (1200x630) em `assets/previa/`, recortada da primeira foto. O campo `"previa"` de cada projeto em `dados/projetos.json` diz onde fica o corte: `0` pega o topo da foto, `0.5` o centro e `1` a base. As páginas de ambiente usam a prévia da foto de capa do ambiente. A home e o catálogo geral usam `assets/og.jpg`, definida em `"home_previa"` (foto e posição do corte). O gerador recria todas essas imagens a cada execução.

## Avaliações do Google

A nota (5,0) e a quantidade (3 avaliações) estão escritas em `modelos/index.html`. Quando entrarem avaliações novas, atualize os números e rode o gerador.

## Rodar localmente

```bash
python -m http.server 4335
```

## Antes de publicar

Preencha `"site"` em `dados/projetos.json` com o endereço completo (por exemplo `https://lordsplanejados.com.br`) e rode `python gerar.py`. Isso faz a prévia dos links no WhatsApp mostrar a foto de cada projeto e cria o `sitemap.xml`.
