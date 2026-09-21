import React from 'react';
import { Skeleton } from '../ui/skeleton';

// Kerangka kartu produk (loading state katalog) — rasio & tipografi mengikuti
// ProductCard versi immersive (gambar 4:5, meta satu kolom).
export const ProductCardSkeleton = () => (
  <div data-testid="product-card-skeleton" className="group p-1.5 sm:p-2">
    <Skeleton className="aspect-[4/5] w-full rounded-[15px]" />
    <div className="pt-2.5 px-1 space-y-1.5">
      <Skeleton className="h-2 w-1/3" />
      <Skeleton className="h-3.5 w-2/3" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  </div>
);

export const ProductGridSkeleton = ({ count = 12, testId = 'shop-grid-loading', className }) => (
  <div
    data-testid={testId}
    className={
      className ||
      'grid gap-3 sm:gap-4 grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
    }
  >
    {Array.from({ length: count }).map((_, i) => (
      <ProductCardSkeleton key={i} />
    ))}
  </div>
);

// Kerangka baris carousel horizontal.
export const ProductRowSkeleton = ({ count = 4, testId = 'home-best-sellers-loading' }) => (
  <div data-testid={testId} className="flex gap-4 sm:gap-6 overflow-hidden">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="min-w-[70%] sm:min-w-[46%] lg:min-w-[26%]">
        <ProductCardSkeleton />
      </div>
    ))}
  </div>
);
