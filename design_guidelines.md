{
  "project": {
    "name": "Collector Parfum (Storefront Only)",
    "goal": "Enchant the UI into a dark, cinematic, editorial luxury perfume storefront with STRONG 3D frosted-glass across all storefront surfaces (cards, buttons, panels, drawers, modals), while retaining existing brand accents (brass/champagne/paper) and typography cues. Keep product bottle artwork inside product cards unchanged; redesign the card frame + controls in glass. Fix sticky header gap (header must stick at top:0).",
    "non_goals": ["Do not redesign /admin backoffice", "Do not break routes, API patterns, or existing data-testid attributes"],
    "audience": "Indonesian premium perfume shoppers (mobile-heavy), aspirational, sensorial, luxury"
  },

  "brand_attributes": [
    "Cinematic", 
    "Editorial", 
    "Sensory", 
    "Premium", 
    "Trustworthy", 
    "Tactile (glass + metal)",
    "Minimal copy, maximal atmosphere"
  ],

  "inspiration_refs": {
    "search_refs": [
      {
        "title": "Bliss Fragrance – Perfume Store Full Website UI (Figma community)",
        "url": "https://www.figma.com/community/file/1491357559970864270/bliss-fragrance-perfume-store-full-website-ui-design-5-figma-pages",
        "use": "Page composition ideas: hero + PLP + PDP + cart/checkout hierarchy"
      },
      {
        "title": "PARFS – Perfume Ecommerce Website (Behance)",
        "url": "https://www.behance.net/gallery/235097547/PARFS-Perfume-Ecommerce-Website-Web-Design-Figma?locale=en_US",
        "use": "Luxury editorial spacing, product storytelling blocks"
      },
      {
        "title": "Dribbble – Frosted Glass UI search", 
        "url": "https://dribbble.com/search/frosted-glass-ui",
        "use": "Glass edge highlights, layered depth, dark backdrops"
      },
      {
        "title": "Backdrop-filter / glassmorphism implementation notes", 
        "url": "https://www.joshwcomeau.com/css/backdrop-filter/",
        "use": "Practical constraints: blur works only with rich backdrops; performance considerations"
      }
    ],
    "local_images_available": {
      "base_path": "/images/home/",
      "assets": [
        "hero-main", "hero-float", "media-large", "media-card-1", "media-card-2",
        "featured-woody", "featured-floral", "featured-promo", "featured-men", "featured-women",
        "video-poster", "faq",
        "cat-amber", "cat-citrus", "cat-floral", "cat-fresh", "cat-gourmand", "cat-woody"
      ],
      "direction": "Reuse these everywhere possible as page headers + section backdrops. Keep imagery dark/model-focused; add subtle film grain overlay and vignette."
    }
  },

  "typography": {
    "keep_existing": {
      "display": "DM Serif Display (cp-headline)",
      "body": "Manrope",
      "mono": "Azeret Mono (cp-mono, uppercase tracked)"
    },
    "scale": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl (cp-headline, tracking-[-0.015em], leading-[0.95])",
      "h2": "text-base md:text-lg (cp-mono eyebrow or Manrope subhead; keep restrained)",
      "body": "text-sm sm:text-base (Manrope, leading-relaxed)",
      "small": "text-xs sm:text-sm (cp-mono for labels; Manrope for helper text)"
    },
    "editorial_rules": [
      "Use cp-mono eyebrow above every major section title (adds luxury cadence).",
      "Keep paragraphs short (2–3 lines) and use more whitespace than feels comfortable.",
      "On dark backdrops, prefer warm paper text (cp-paper-warm) at 85–92% opacity for long reading."
    ]
  },

  "color_system": {
    "keep_brand_accents": {
      "cp-paper": "#f7f3ea",
      "cp-paper-warm": "#fffcf6",
      "cp-paper-fog": "#eee7dc",
      "cp-ink": "#141414",
      "cp-ink-soft": "#2a2a2a",
      "cp-champagne": "#d6c3a3",
      "cp-brass": "#b89b6a"
    },
    "new_dark_cinematic_tokens_to_add_in_index_css": {
      "note": "Add these as CSS variables under :root (and optionally .dark) without removing existing cp-* tokens. Use them for storefront surfaces only.",
      "tokens": {
        "--cp-night": "#070708",
        "--cp-night-2": "#0B0B0C",
        "--cp-graphite": "#101114",
        "--cp-smoke": "#17181C",
        "--cp-ash": "#23242A",

        "--cp-text-on-night": "rgba(255, 252, 246, 0.92)",
        "--cp-text-muted-on-night": "rgba(255, 252, 246, 0.72)",
        "--cp-hairline-on-night": "rgba(255, 255, 255, 0.10)",

        "--cp-glass-bg": "rgba(16, 17, 20, 0.46)",
        "--cp-glass-bg-strong": "rgba(10, 10, 12, 0.58)",
        "--cp-glass-border": "rgba(255, 255, 255, 0.14)",
        "--cp-glass-border-soft": "rgba(255, 255, 255, 0.08)",
        "--cp-glass-highlight": "rgba(255, 255, 255, 0.18)",
        "--cp-glass-specular": "rgba(214, 195, 163, 0.22)",

        "--cp-shadow-1": "0 1px 0 rgba(255,255,255,0.06) inset",
        "--cp-shadow-2": "0 10px 30px rgba(0,0,0,0.40)",
        "--cp-shadow-3": "0 2px 10px rgba(0,0,0,0.28)",
        "--cp-shadow-4": "0 40px 90px rgba(0,0,0,0.55)",

        "--cp-ring": "rgba(214, 195, 163, 0.55)",
        "--cp-ring-2": "rgba(184, 155, 106, 0.55)",

        "--cp-radius-lg": "22px",
        "--cp-radius-xl": "28px"
      },
      "allowed_gradients": {
        "restriction": "No saturated purple/pink/blue gradients. Gradients max 20% viewport; only for section backdrops/hero overlays.",
        "gradients": {
          "--cp-hero-wash": "radial-gradient(1200px 700px at 20% 10%, rgba(214,195,163,0.10), transparent 55%), radial-gradient(900px 600px at 80% 0%, rgba(184,155,106,0.10), transparent 60%), linear-gradient(180deg, rgba(7,7,8,0.10), rgba(7,7,8,0.92))",
          "--cp-vignette": "radial-gradient(1200px 800px at 50% 20%, transparent 40%, rgba(0,0,0,0.55) 100%)"
        }
      }
    },
    "usage_priority": [
      "Page background: cp-night/cp-night-2 with subtle noise overlay.",
      "Reading surfaces: glass panels (cp-glass-bg) rather than solid dark blocks.",
      "Accents: cp-brass/cp-champagne only for rings, separators, tiny highlights, price, and primary CTA emphasis."
    ]
  },

  "design_tokens_css_scaffold": {
    "add_to_index_css": "/* === Collector Parfum: Cinematic Glass Tokens (Storefront) === */\n:root {\n  --cp-night: #070708;\n  --cp-night-2: #0B0B0C;\n  --cp-graphite: #101114;\n  --cp-smoke: #17181C;\n  --cp-ash: #23242A;\n\n  --cp-text-on-night: rgba(255, 252, 246, 0.92);\n  --cp-text-muted-on-night: rgba(255, 252, 246, 0.72);\n  --cp-hairline-on-night: rgba(255, 255, 255, 0.10);\n\n  --cp-glass-bg: rgba(16, 17, 20, 0.46);\n  --cp-glass-bg-strong: rgba(10, 10, 12, 0.58);\n  --cp-glass-border: rgba(255, 255, 255, 0.14);\n  --cp-glass-border-soft: rgba(255, 255, 255, 0.08);\n  --cp-glass-highlight: rgba(255, 255, 255, 0.18);\n  --cp-glass-specular: rgba(214, 195, 163, 0.22);\n\n  --cp-ring: rgba(214, 195, 163, 0.55);\n  --cp-ring-2: rgba(184, 155, 106, 0.55);\n\n  --cp-radius-lg: 22px;\n  --cp-radius-xl: 28px;\n\n  --cp-hero-wash: radial-gradient(1200px 700px at 20% 10%, rgba(214,195,163,0.10), transparent 55%),\n                  radial-gradient(900px 600px at 80% 0%, rgba(184,155,106,0.10), transparent 60%),\n                  linear-gradient(180deg, rgba(7,7,8,0.10), rgba(7,7,8,0.92));\n  --cp-vignette: radial-gradient(1200px 800px at 50% 20%, transparent 40%, rgba(0,0,0,0.55) 100%);\n}\n\n/* Storefront dark backdrop helper */\n.cp-night-bg { background: var(--cp-night); color: var(--cp-text-on-night); }\n",
    "tailwind_usage_note": "Use arbitrary values to reference CSS vars: bg-[var(--cp-glass-bg)] border-[var(--cp-glass-border)] text-[var(--cp-text-on-night)]."
  },

  "glass_recipe": {
    "goal": "Strong frosted glass with 3D depth: translucent fill + backdrop blur + glossy top highlight + double edge + shadow ladder + subtle hover lift.",
    "performance_note": "Backdrop blur is expensive. Use strong blur only on key panels (hero floating card, nav, drawers, modals, product cards). For dense grids on low-end mobile, reduce blur (12–14px) and rely more on shadows + translucent fill.",
    "utility_classes_to_create": {
      "add_to_index_css_utilities": {
        ".cp-glass": "position: relative; background: var(--cp-glass-bg); border: 1px solid transparent; border-radius: var(--cp-radius-lg); backdrop-filter: blur(18px) saturate(165%) brightness(1.06); -webkit-backdrop-filter: blur(18px) saturate(165%) brightness(1.06); box-shadow: var(--cp-shadow-1), var(--cp-shadow-2), var(--cp-shadow-3), var(--cp-shadow-4); overflow: hidden;",
        ".cp-glass::before": "content: ''; position: absolute; inset: 0; pointer-events: none; background: linear-gradient(180deg, var(--cp-glass-highlight), transparent 30%);",
        ".cp-glass::after": "content: ''; position: absolute; inset: 1px; border-radius: inherit; pointer-events: none; border: 1px solid var(--cp-glass-border-soft);",
        ".cp-glass-border": "background: linear-gradient(var(--cp-glass-bg), var(--cp-glass-bg)) padding-box, linear-gradient(135deg, rgba(255,255,255,0.22), rgba(214,195,163,0.18), rgba(255,255,255,0.10)) border-box; border: 1px solid transparent;",
        ".cp-glass-hover": "transition: box-shadow 260ms cubic-bezier(0.22,1,0.36,1), background-color 260ms cubic-bezier(0.22,1,0.36,1), border-color 260ms cubic-bezier(0.22,1,0.36,1);",
        ".cp-glass-hover:hover": "box-shadow: 0 1px 0 rgba(255,255,255,0.08) inset, 0 18px 40px rgba(0,0,0,0.45), 0 60px 120px rgba(0,0,0,0.60);",
        ".cp-glass-tilt": "transform: translateZ(0);",
        ".cp-glass-tilt:hover": "transform: translateY(-2px);"
      },
      "tailwind_composition_example": "className=\"cp-glass cp-glass-border cp-glass-hover cp-glass-tilt\""
    },
    "do_not": [
      "Do not use transition: all.",
      "Do not put heavy gradients behind text-heavy reading areas.",
      "Do not use saturated purple/pink gradients anywhere."
    ]
  },

  "buttons": {
    "component_path": "/app/frontend/src/components/ui/button.jsx",
    "variants_to_add": [
      {
        "name": "glassPrimary",
        "use": "Main CTAs: Tambah ke Keranjang, Checkout, Bayar, Apply Voucher",
        "tailwind": "bg-[rgba(214,195,163,0.14)] text-[var(--cp-text-on-night)] border border-[rgba(214,195,163,0.28)] shadow-[0_1px_0_rgba(255,255,255,0.10)_inset,0_18px_40px_rgba(0,0,0,0.45)] backdrop-blur-[14px] hover:bg-[rgba(214,195,163,0.18)] hover:border-[rgba(214,195,163,0.40)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cp-ring)] focus-visible:ring-offset-0",
        "shape": "rounded-[14px] h-11 px-5",
        "micro_interaction": "On hover: slight lift (translateY -1px) + specular highlight intensifies; on active: scale-95 (no transform transitions globally)."
      },
      {
        "name": "glassSecondary",
        "use": "Secondary actions: Quick View, Lihat Detail, Simpan ke Wishlist",
        "tailwind": "bg-[rgba(16,17,20,0.40)] text-[var(--cp-text-on-night)] border border-[var(--cp-glass-border)] shadow-[0_1px_0_rgba(255,255,255,0.08)_inset,0_14px_34px_rgba(0,0,0,0.42)] backdrop-blur-[16px] hover:bg-[rgba(16,17,20,0.52)] hover:border-[rgba(255,255,255,0.18)]",
        "shape": "rounded-[14px] h-11 px-5"
      },
      {
        "name": "glassPill",
        "use": "Filter chips, size/concentration selectors, promo pills",
        "tailwind": "rounded-full h-9 px-4 bg-[rgba(16,17,20,0.38)] border border-[rgba(255,255,255,0.14)] backdrop-blur-[14px] hover:bg-[rgba(16,17,20,0.50)]",
        "state": "selected: border-[rgba(214,195,163,0.45)] bg-[rgba(214,195,163,0.12)]"
      }
    ],
    "data_testid_rule": "Every Button usage must include data-testid (e.g., data-testid=\"product-card-add-to-cart-button\")."
  },

  "cards_and_panels": {
    "component_paths": {
      "card": "/app/frontend/src/components/ui/card.jsx",
      "badge": "/app/frontend/src/components/ui/badge.jsx",
      "separator": "/app/frontend/src/components/ui/separator.jsx",
      "accordion": "/app/frontend/src/components/ui/accordion.jsx",
      "dialog": "/app/frontend/src/components/ui/dialog.jsx",
      "drawer": "/app/frontend/src/components/ui/drawer.jsx",
      "sheet": "/app/frontend/src/components/ui/sheet.jsx"
    },
    "global_rule": "All storefront cards/panels become cp-glass + cp-glass-border. Use darker page backdrops so glass pops.",
    "product_card_redesign": {
      "must_keep": "Inner bottle artwork image area stays as-is (do not restyle the image itself).",
      "frame": "Wrap the existing media area inside a glass frame with inner padding and a subtle inner border. Add a top specular highlight and a bottom shadow to feel like a display case.",
      "layout": {
        "mobile": "2-col grid, tall cards; actions pinned to bottom",
        "desktop": "3–4 col grid; hover reveals secondary actions"
      },
      "tailwind_skeleton": {
        "outer": "group relative cp-glass cp-glass-border cp-glass-hover rounded-[var(--cp-radius-xl)] p-3 sm:p-4",
        "media_frame": "relative rounded-[18px] bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.10)] overflow-hidden",
        "media_keep": "(existing bottle artwork component unchanged)",
        "meta": "mt-3 space-y-1",
        "title": "cp-display text-[15px] sm:text-base text-[var(--cp-text-on-night)]",
        "price": "cp-mono text-xs tracking-[0.18em] text-[rgba(214,195,163,0.92)]",
        "actions": "mt-3 grid grid-cols-2 gap-2"
      },
      "buttons_in_card": {
        "primary": "use Button variant glassPrimary",
        "secondary": "use Button variant glassSecondary or ghost with glass border"
      },
      "micro_interactions": [
        "Card hover: translateY(-2px) + shadow deepens.",
        "Media frame: subtle parallax on mouse move (desktop only) via framer-motion; disable on prefers-reduced-motion.",
        "Wishlist heart: hover glow using brass/champagne ring."
      ]
    },
    "other_cards": {
      "testimonial": "Glass card with avatar + rating; use cp-mono for source label (Google Review).",
      "location": "Glass card with map thumbnail + address; CTA button glassSecondary.",
      "cart_line_item": "Glass row with image, qty stepper, remove icon button in glass.",
      "faq": "Accordion inside a glass panel; triggers use cp-mono label + chevron icon."
    }
  },

  "layout_and_grids": {
    "container": "Use existing .cp-container (max-w 1240).",
    "section_spacing": "Use existing .cp-section; increase whitespace on editorial sections (manifesto, video, media grid) by +10–20% on desktop.",
    "grid_rules": {
      "homepage": {
        "hero": "Full-bleed image with vignette + hero wash overlay; floating glass product card anchored bottom-right on desktop, bottom on mobile.",
        "category_grid": "2 cols mobile, 3 cols tablet, 6 cols desktop; each category is an image card with glass label chip.",
        "best_sellers": "2 cols mobile, 3 cols md, 4 cols lg; keep dense but breathable gaps (gap-3 sm:gap-4 lg:gap-6).",
        "media_grid": "Asymmetric editorial grid: 1 large + 2 stacked cards; all with glass captions.",
        "manifesto": "Turn into immersive scrollytelling: big typography over moving image strips + glass quote cards.",
        "video": "Poster image with glass play button + glass caption panel; on play open Dialog with embedded video."
      },
      "shop_plp": {
        "header": "Full-bleed editorial header image + glass filter summary bar.",
        "filters": "Left sidebar as glass panel (Sheet on mobile).",
        "sort_toggle": "Glass pill toggles; grid/list toggle uses ToggleGroup."
      },
      "pdp": {
        "gallery": "Large image area on dark backdrop; thumbnails in glass chips.",
        "buy_box": "Right column glass panel with variant selectors (RadioGroup/Select) and glassPrimary CTA.",
        "sticky_buy_bar": "Mobile sticky glass bar with price + CTA; ensure safe-area padding."
      }
    },
    "avoid": ["Do not center-align entire app container."]
  },

  "section_by_section_immersion": {
    "global_backdrop_pattern": {
      "pattern": "Every page gets a full-bleed editorial image header OR a dark cinematic gradient wash + noise. Then content sits in glass panels.",
      "implementation": "Use absolute background image + overlay: cp-hero-wash + cp-vignette + cp-noise."
    },
    "manifesto_section_upgrade": {
      "current": "Plain big scrolling typographic manifesto",
      "new": "Cinematic manifesto: alternating full-bleed image strips (from /images/home/media-*) with oversized serif lines; interleave 2–3 glass quote cards and a brass hairline separator.",
      "motion": "On scroll: fade/slide in lines; subtle horizontal drift of background image (parallax) using framer-motion; respect prefers-reduced-motion."
    },
    "video_bts_section": {
      "new": "Poster image (video-poster) with glass play control (circular glass button) + caption panel. Add subtle animated light sweep across the play button on hover."
    },
    "page_headers": {
      "apply_to": ["Shop", "About", "Contact", "Wishlist", "Voucher", "Order Success", "Store Locations"],
      "pattern": "Full-bleed header image + glass breadcrumb + page title panel. Use Breadcrumb component in glass."
    }
  },

  "navigation_and_global_shell": {
    "sticky_header_gap_fix": {
      "problem": "Header sticks at top:40px while announcement bar scrolls away, leaving a gap.",
      "fix": "Make SiteHeader sticky top-0. Keep AnnouncementBar as its own element above; when it scrolls away, header remains flush.",
      "implementation_note": "If header currently uses style top: var(--announcement-h), remove it and use top:0. If you need spacing when announcement is visible, handle via layout flow (announcement occupies space above header) rather than sticky offset."
    },
    "header_style": {
      "pattern": "Header becomes a glass bar over hero imagery: cp-glass + cp-glass-border, slightly stronger blur (20px) and tighter radius.",
      "tailwind": "sticky top-0 z-50 bg-[rgba(10,10,12,0.42)] backdrop-blur-[20px] border-b border-[rgba(255,255,255,0.10)]",
      "micro_interaction": "On scroll (after 24px): increase opacity slightly and add deeper shadow; implement via a small scroll listener or CSS (if already present)."
    },
    "announcement_bar": {
      "keep": "Marquee behavior",
      "style": "Dark strip with brass separators; keep height 40px; text in cp-paper-warm 80%"
    },
    "footer": {
      "pattern": "Dark cinematic footer with glass newsletter panel; avoid gradients >20% viewport.",
      "trust": "Use cp-mono labels + lucide icons; keep contrast high."
    },
    "mobile_bottom_nav": "Use glass pill dock with 4–5 icons; backdrop blur 18px; safe-area padding."
  },

  "forms_and_inputs": {
    "component_paths": {
      "input": "/app/frontend/src/components/ui/input.jsx",
      "textarea": "/app/frontend/src/components/ui/textarea.jsx",
      "select": "/app/frontend/src/components/ui/select.jsx",
      "checkbox": "/app/frontend/src/components/ui/checkbox.jsx",
      "radio": "/app/frontend/src/components/ui/radio-group.jsx"
    },
    "style": {
      "input": "Glass input: bg rgba + blur 12–14px, border hairline, focus ring champagne",
      "helper": "Use muted warm text; errors in destructive but softened on dark"
    },
    "data_testid_examples": [
      "data-testid=\"checkout-email-input\"",
      "data-testid=\"contact-form-message-textarea\"",
      "data-testid=\"shop-filter-price-range-slider\""
    ]
  },

  "motion": {
    "library": "framer-motion (already available)",
    "principles": [
      "Entrance: fade + slight y (8–14px) for sections.",
      "Hover: lift -2px for cards; buttons: press scale 0.97 on tap.",
      "Parallax: only on hero/media images; subtle (6–12px).",
      "Respect prefers-reduced-motion: disable parallax and continuous animations."
    ],
    "timings": {
      "fast": "160–200ms",
      "standard": "240–320ms",
      "easing": "cubic-bezier(0.22, 1, 0.36, 1)"
    }
  },

  "accessibility": {
    "contrast": "On dark backgrounds, body text uses cp-paper-warm at >= 0.85 opacity; avoid low-contrast brass for paragraphs (brass only for accents).",
    "focus": "Keep :focus-visible outline/ring; prefer ring in cp-champagne.",
    "hit_targets": "Minimum 44px height for primary touch targets.",
    "reduced_motion": "Honor prefers-reduced-motion (already in index.css)."
  },

  "image_urls": {
    "note": "Use local assets; no external stock provider available in this environment.",
    "categories": [
      {
        "category": "hero",
        "description": "Homepage hero full-bleed editorial",
        "urls": ["/images/home/hero-main.jpg", "/images/home/hero-float.jpg"]
      },
      {
        "category": "media_grid",
        "description": "Editorial media grid",
        "urls": ["/images/home/media-large.jpg", "/images/home/media-card-1.jpg", "/images/home/media-card-2.jpg"]
      },
      {
        "category": "featured_collection",
        "description": "Collection banners",
        "urls": [
          "/images/home/featured-woody.jpg",
          "/images/home/featured-floral.jpg",
          "/images/home/featured-men.jpg",
          "/images/home/featured-women.jpg",
          "/images/home/featured-promo.jpg"
        ]
      },
      {
        "category": "categories",
        "description": "Category cards",
        "urls": [
          "/images/home/cat-amber.jpg",
          "/images/home/cat-citrus.jpg",
          "/images/home/cat-floral.jpg",
          "/images/home/cat-fresh.jpg",
          "/images/home/cat-gourmand.jpg",
          "/images/home/cat-woody.jpg"
        ]
      },
      {
        "category": "video",
        "description": "Behind-the-scenes poster",
        "urls": ["/images/home/video-poster.jpg"]
      },
      {
        "category": "faq",
        "description": "FAQ backdrop",
        "urls": ["/images/home/faq.jpg"]
      }
    ]
  },

  "component_path": {
    "shadcn_ui": [
      "/app/frontend/src/components/ui/button.jsx",
      "/app/frontend/src/components/ui/card.jsx",
      "/app/frontend/src/components/ui/badge.jsx",
      "/app/frontend/src/components/ui/accordion.jsx",
      "/app/frontend/src/components/ui/dialog.jsx",
      "/app/frontend/src/components/ui/drawer.jsx",
      "/app/frontend/src/components/ui/sheet.jsx",
      "/app/frontend/src/components/ui/tabs.jsx",
      "/app/frontend/src/components/ui/toggle-group.jsx",
      "/app/frontend/src/components/ui/tooltip.jsx",
      "/app/frontend/src/components/ui/breadcrumb.jsx",
      "/app/frontend/src/components/ui/carousel.jsx",
      "/app/frontend/src/components/ui/sonner.jsx"
    ],
    "notes": "Project uses .jsx (not .tsx). Keep exports consistent with existing patterns."
  },

  "instructions_to_main_agent": {
    "1_global_backdrop": "Switch storefront pages to cp-night backdrop with image headers. Use cp-noise overlay and cp-vignette on hero/header sections only (<=20% viewport gradient rule).",
    "2_glass_everywhere": "Apply cp-glass + cp-glass-border to all storefront cards/panels/drawers/modals/buttons. Ensure strong 3D depth via shadow ladder + inset highlight.",
    "3_product_cards": "Do not touch bottle artwork rendering; only wrap/reframe with glass frame and replace buttons with glass variants.",
    "4_header_gap_bug": "Update sticky header to top-0; do not offset by announcement height. Announcement bar remains in normal flow above.",
    "5_testing": "Preserve existing data-testid attributes; add missing ones to every interactive element and key info text.",
    "6_performance": "Reduce blur on dense grids if needed; keep blur strongest on hero/nav/drawers/modals."
  }
}

<General UI UX Design Guidelines>  
    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms
    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text
   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json

 **GRADIENT RESTRICTION RULE**
NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc
NEVER use dark gradients for logo, testimonial, footer etc
NEVER let gradients cover more than 20% of the viewport.
NEVER apply gradients to text-heavy content or reading areas.
NEVER use gradients on small UI elements (<100px width).
NEVER stack multiple gradient layers in the same viewport.

**ENFORCEMENT RULE:**
    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors

**How and where to use:**
   • Section backgrounds (not content backgrounds)
   • Hero section header content. Eg: dark to light to dark color
   • Decorative overlays and accent elements only
     • Hero section with 2-3 mild color
   • Gradients creation can be done for any angle say horizontal, vertical or diagonal

- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**

</Font Guidelines>

- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. 
   
- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.

- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.
   
- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly
    Eg: - if it implies playful/energetic, choose a colorful scheme
           - if it implies monochrome/minimal, choose a black–white/neutral scheme

**Component Reuse:**
	- Prioritize using pre-existing components from src/components/ui when applicable
	- Create new components that match the style and conventions of existing components when needed
	- Examine existing components to understand the project's component patterns before creating new ones

**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component

**Best Practices:**
	- Use Shadcn/UI as the primary component library for consistency and accessibility
	- Import path: ./components/[component-name]

**Export Conventions:**
	- Components MUST use named exports (export const ComponentName = ...)
	- Pages MUST use default exports (export default function PageName() {...})

**Toasts:**
  - Use `sonner` for toasts"
  - Sonner component are located in `/app/src/components/ui/sonner.tsx`

Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.
</General UI UX Design Guidelines>
