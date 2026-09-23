# QOR design system

The landing and primary workspace controls use Russian copy. Supplier names,
source column keys, SKU codes and audit JSON retain their original technical
values. The generated reference image named in the brief was not accessible;
the page follows its described dark navy and electric blue direction.

| Token | Value | Use |
|---|---|---|
| Canvas | `#0B1424` | App background |
| Surface | `#18283D` | Native cards and inputs |
| Preview | `#152B4B` → `#0B1930` | Static illustrative product panel |
| Primary | `#2563EB` | Actions and selected states |
| Link | `#93C5FD` | Navigation on dark backgrounds |
| Main text | `#F3F7FC` | Headings and body |
| Secondary text | `#B7C6D9` | Supporting copy |
| Border | `#38526E` | Separation without heavy dividers |

White on the primary action exceeds 4.5:1 contrast; pale blue links and main
text have stronger contrast on the canvas. Streamlit owns visible keyboard focus
for the native links, buttons and form controls. No CSS removes outlines. The
static preview has no clickable pseudo-controls.

Base text is 16 px system sans-serif. Streamlit theme heading sizes are 2.7,
1.85, 1.4, 1.2, 1 and 0.9 rem. The hero uses a single H1. Subsequent sections
use H2, and card titles use H3. Native columns stack on narrow screens; the
preview's three values become a two-column then full-width card below 560 px.
No fixed pixel page width or horizontal scroll is required. Numeric examples
show the physical unit. Source tables use scrollable native dataframes.

The hero CTA and final CTA are native page links to `/workspace`. The preview
and 188 − (28 + 40) = 120 example are explicitly synthetic. Its pack multiple
is 20. It does not call the planner or imply a real shipment ETA. Four capability
cards describe implemented mechanisms, while the boundary section states missing
real SE files, current IEK stock and live model access. No testimonials or
accuracy/savings claims appear.

The current Vercel Web Interface Guidelines were read during review. Static
preview markup has a section description; actions use native Streamlit links
and controls with labels and keyboard behavior. There is no motion, autoplay,
zoom suppression or icon-only action. Pixel inspection on desktop/mobile remains
unverified because the available computer-use browser inventory exposed no
browser; AppTest route and copy checks passed.
