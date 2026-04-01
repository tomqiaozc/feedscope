"use client";

import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";
import { useSearch } from "@/hooks/use-search";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionSkeleton } from "@/components/ui/section-skeleton";
import { ErrorBanner } from "@/components/ui/error-banner";
import { MasonryGrid } from "@/components/ui/masonry-grid";
import { PostCard } from "@/components/domain/post-card";
import type { Post } from "@/types/watchlist";

const crumbs = [{ label: "Explore" }];

export default function ExplorePage() {
  useBreadcrumbs(crumbs);

  const [query, setQuery] = useState("");
  const { data: results, loading, error, searched, execute } = useSearch<Post>();

  function handleSearch() {
    const q = query.trim();
    if (!q) return;
    execute("explore/search", { q, count: "50" });
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold fade-up-stagger-1">Explore</h1>

      {/* Search bar */}
      <div className="flex gap-2 fade-up-stagger-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
            placeholder="Search tweets by keyword..."
            className="w-full rounded-lg border border-border bg-background pl-9 pr-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
          />
        </div>
        <Button size="sm" onClick={handleSearch} disabled={loading || !query.trim()}>
          {loading ? "Searching..." : "Search"}
        </Button>
      </div>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <SectionSkeleton />
      ) : results && results.length > 0 ? (
        <MasonryGrid>
          {results.map((post) => (
            <div key={post.id}>
              <PostCard post={post} />
              <Link
                href={`/explore/user/${post.author_username}`}
                className="mt-1 block text-xs text-muted-foreground hover:text-foreground"
              >
                View @{post.author_username} profile
              </Link>
            </div>
          ))}
        </MasonryGrid>
      ) : searched ? (
        <EmptyState
          title={`No results found for "${query}"`}
          message="Try different keywords or check your spelling."
        />
      ) : (
        <EmptyState
          title="Search for tweets"
          message="Enter a keyword to search Twitter/X posts."
        />
      )}
    </div>
  );
}
