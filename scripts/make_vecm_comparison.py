"""Appendix figures comparing the paper's VECM figures with our reproduction, aligned panel by panel.

Usage, from the repository root:  python scripts/make_vecm_comparison.py [path/to/2006.13922v3.pdf]

Inputs: the paper's Figures 11-14, read as vector graphics from the arXiv version of the paper
(https://arxiv.org/abs/2006.13922v3; not redistributed here: download it to figures/paper/2006.13922v3.pdf,
which Git ignores, or pass its path), and our Stata output in results/vecm/ (DAI.pdf, USDC.pdf,
I_CDAI_R_DDAIADAI.pdf, I_CUSDC_R_DUSDCAUSDC.pdf: the same figures from the authors' do-file,
scripts/vecm_replication.do, run on the authors' data). Needs PyMuPDF (pip install pymupdf).
Each figure of the paper is located below its caption's column: the area above the caption that holds the
figure's drawings and small text. All panels are rendered at the same width in pixels, then cut so that their
y-axis and x-axis lines sit at the same relative position and scaled to one size, so that the axes of all
panels in a figure coincide (within each figure the plot areas' aspect ratios differ by about 1%, so the
scaling changes no visible shape). Output: figures/appx_vecm_rates.pdf (Figures 11-12) and
figures/appx_vecm_irf.pdf (Figures 13-14).
"""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pymupdf
from PIL import Image

from make_report_figures import FULL_WIDTH, STYLE

PAPER = sys.argv[1] if len(sys.argv) > 1 else 'figures/paper/2006.13922v3.pdf'
PAPER_FIGS = [11, 12, 13, 14]                                 # the paper's figure numbers, in the order of the rows
OURS = ['results/vecm/DAI.pdf', 'results/vecm/USDC.pdf',       # Stata output, in the order of the rows
        'results/vecm/I_CDAI_R_DDAIADAI.pdf', 'results/vecm/I_CUSDC_R_DUSDCAUSDC.pdf']
WIDTH = 1600                                                  # every panel is rendered this many pixels wide
INK = 200                                                     # grey level below which a pixel is content


def axis_lines(grey):
    """Pixel position of the leftmost y-axis line and the lowest x-axis line in one panel."""
    ink = grey < INK
    h, w = ink.shape
    ax_x = np.where(ink.sum(0) > 0.55 * h)[0].min()
    # the x-axis is where the y-axis line ends: the bottom of the longest unbroken run in that column
    # (a legend box below the plot can be as wide as the axis, so the widest low row is not used)
    col = ink[:, ax_x:ax_x + 3].any(1)
    best, run, end = 0, 0, 0
    for y, v in enumerate(col):
        run = run + 1 if v else 0
        if run > best:
            best, end = run, y
    return ax_x, end


def render(page, clip):
    """Render one area of a PDF page, WIDTH pixels wide."""
    zoom = WIDTH / clip.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip, alpha=False)
    return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)


def load_pdf(path):
    """First page of a PDF, cut to its drawn content."""
    page = pymupdf.open(path)[0]
    return render(page, page.rect)


def paper_figure(doc, n):
    """The paper's Figure n: the area above its caption, in the caption's column, that holds the figure's
    drawings and small text (axis labels are under 6.5 pt; captions, body text and running heads are larger)."""
    for page in doc:
        hits = page.search_for(f'Figure {n}:')
        if hits:
            break
    else:
        raise SystemExit(f'Figure {n} not found in {PAPER}')
    cap, mid = hits[0], page.rect.width / 2
    x0, x1 = (0, mid) if cap.x0 < mid else (mid, page.rect.width)
    inside = lambda r: r.x0 >= x0 - 1 and r.x1 <= x1 + 1 and r.y1 <= cap.y0
    spans = [(pymupdf.Rect(s['bbox']), s['size']) for b in page.get_text('dict')['blocks']
             for line in b.get('lines', []) for s in line['spans'] if s['text'].strip()]
    top = max([r.y1 for r, size in spans if size >= 6.5 and inside(r) and r.y1 < cap.y0 - 1] + [0])
    box = None
    for r in [d['rect'] for d in page.get_drawings()] + [r for r, size in spans if size < 6.5]:
        if inside(r) and r.y0 >= top:
            box = r if box is None else box | r
    return render(page, box)


def white_crop(img, box):
    """Crop, filling any part of the box outside the image with white."""
    box = tuple(int(round(v)) for v in box)
    out = Image.new('RGB', (box[2] - box[0], box[3] - box[1]), 'white')
    out.paste(img.crop((max(box[0], 0), max(box[1], 0), min(box[2], img.width), min(box[3], img.height))),
              (max(-box[0], 0), max(-box[1], 0)))
    return out


def measure(img):
    """Content box and axis lines of one panel image."""
    g = np.asarray(img.convert('L'))
    ink = g < INK
    ys, xs = np.where(ink.any(1))[0], np.where(ink.any(0))[0]
    ax_x, ax_y = axis_lines(g)
    return dict(left=xs[0], top=ys[0], right=xs[-1] + 1, bottom=ys[-1] + 1, ax_x=ax_x, ax_y=ax_y)


def panels(rows):
    """Crop every panel so that its y-axis and x-axis fall at the same relative positions, then scale all
    panels to one size: the axes of all panels in the figure then coincide."""
    doc = pymupdf.open(PAPER)
    imgs = []
    for k in rows:
        imgs.append(paper_figure(doc, PAPER_FIGS[k]))
        imgs.append(load_pdf(OURS[k]))
    info = [measure(im) for im in imgs]
    # space to keep, as fractions of the plot span, so that no label or legend is cut in any panel
    a = max((d['ax_x'] - d['left']) / (d['right'] - d['ax_x']) for d in info)
    b = max((d['bottom'] - d['ax_y']) / (d['ax_y'] - d['top']) for d in info)
    crops, ratios = [], []
    for im, d in zip(imgs, info):
        span_x, span_y = d['right'] - d['ax_x'], d['ax_y'] - d['top']
        crops.append(white_crop(im, (d['ax_x'] - a * span_x, d['top'], d['right'], d['ax_y'] + b * span_y)))
        ratios.append(span_x / span_y)
    print(f'plot-area aspect ratios {min(ratios):.3f}-{max(ratios):.3f} '
          f'(largest difference {100 * (max(ratios) / min(ratios) - 1):.1f}%)')
    w = int(np.median([c.size[0] for c in crops]))
    h = int(np.median([c.size[1] for c in crops]))
    scaled = [c.resize((w, h), Image.LANCZOS) for c in crops]
    return [scaled[k:k + 2] for k in range(0, len(scaled), 2)]


def compose(rows, labels, path):
    plt.rcParams.update(STYLE)
    w, h = rows[0][0].size
    fig_w = FULL_WIDTH
    gap, title, side = 0.18, 0.34, 0.04                       # inches: between columns; title band; edges
    cell_w = (fig_w - gap - 2 * side) / 2
    cell_h = cell_w * h / w
    row_gap = 0.26
    fig_h = title + len(rows) * cell_h + (len(rows) - 1) * row_gap
    fig = plt.figure(figsize=(fig_w, fig_h))
    for i, (row, label) in enumerate(zip(rows, labels)):
        top = fig_h - title - i * (cell_h + row_gap)
        for j, panel in enumerate(row):
            ax = fig.add_axes([(side + j * (cell_w + gap)) / fig_w, (top - cell_h) / fig_h,
                               cell_w / fig_w, cell_h / fig_h])
            ax.imshow(panel, interpolation='none')     # embedded at full resolution
            ax.set_axis_off()
        fig.text(side / fig_w, (top + 0.04) / fig_h, label, va='bottom', ha='left', fontsize=6.5, color='0.35')
    for j, name in enumerate(['Paper', 'Reproduction']):
        fig.text((side + j * (cell_w + gap) + cell_w / 2) / fig_w, 1 - 0.02 / fig_h, name, ha='center', va='top',
                 fontsize=8)
    fig.savefig(path, dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    # rate series and impulse responses have different layouts, so each figure is aligned on its own
    compose(panels([0, 1]), ["Paper's Figure 11 (DAI)", "Paper's Figure 12 (USDC)"], 'figures/appx_vecm_rates.pdf')
    compose(panels([2, 3]), ["Paper's Figure 13 (DAI)", "Paper's Figure 14 (USDC)"], 'figures/appx_vecm_irf.pdf')
    print('Saved figures/appx_vecm_rates.pdf and figures/appx_vecm_irf.pdf')
