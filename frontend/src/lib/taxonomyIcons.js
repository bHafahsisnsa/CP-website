// lib/taxonomyIcons.js — pemetaan kunci ikon (disimpan di taksonomi occasion/character
// oleh admin) -> komponen lucide-react. Menjaga tampilan tetap premium (tanpa emoji).
// Kunci mengikuti nama lucide dalam kebab-case. Fallback: Sparkles.
import {
  Briefcase, Dumbbell, Wine, Sun, Plane, Moon, PartyPopper, Gem,
  Leaf, Flower2, IceCream, TreePine, Citrus, Feather, Waves, Flame,
  Flower, Cloud, Sprout, Sparkles, Tag, Heart, Star, Droplets, Snowflake,
} from 'lucide-react';

const MAP = {
  // occasions
  briefcase: Briefcase,
  dumbbell: Dumbbell,
  wine: Wine,
  sun: Sun,
  plane: Plane,
  moon: Moon,
  'party-popper': PartyPopper,
  gem: Gem,
  // characters
  leaf: Leaf,
  'flower-2': Flower2,
  flower2: Flower2,
  'ice-cream': IceCream,
  'tree-pine': TreePine,
  citrus: Citrus,
  feather: Feather,
  waves: Waves,
  flame: Flame,
  flower: Flower,
  cloud: Cloud,
  sprout: Sprout,
  sparkles: Sparkles,
  // extra aliases (untuk admin memilih ikon lain)
  tag: Tag,
  heart: Heart,
  star: Star,
  droplets: Droplets,
  snowflake: Snowflake,
};

// Daftar kunci yang bisa dipilih admin (dropdown ikon).
export const FACET_ICON_KEYS = Object.keys(MAP);

// Kembalikan komponen ikon lucide untuk sebuah kunci (fallback Sparkles).
export const getFacetIcon = (key) => MAP[(key || '').toLowerCase()] || Sparkles;
