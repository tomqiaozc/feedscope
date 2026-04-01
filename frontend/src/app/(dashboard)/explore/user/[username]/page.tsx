"use client";

import { useState, useMemo, use } from "react";
import Link from "next/link";
import { MapPin, Link as LinkIcon, BadgeCheck, User } from "lucide-react";
import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";
import { useFetch } from "@/hooks/use-fetch";
import { cn } from "@/lib/utils";
import { SectionSkeleton } from "@/components/ui/section-skeleton";
import { ErrorBanner } from "@/components/ui/error-banner";
import { EmptyState } from "@/components/ui/empty-state";
import { MasonryGrid } from "@/components/ui/masonry-grid";
import { PostCard } from "@/components/domain/post-card";
import type { UserInfo } from "@/types/explore";
import type { Post } from "@/types/watchlist";

const TABS = [
  { key: "tweets", label: "Tweets" },
  { key: "timeline", label: "Timeline" },
  { key: "replies", label: "Replies" },
  { key: "highlights", label: "Highlights" },
  { key: "followers", label: "Followers" },
  { key: "following", label: "Following" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

interface UserCardProps {
  user: { username: string; display_name?: string | null; profile_image_url?: string | null; follower_count?: number };
}

function UserCard({ user }: UserCardProps) {
  return (
    <Link
      href={`/explore/user/${user.username}`}
      className="flex items-center gap-3 rounded-widget px-3 py-2.5 transition-colors hover:bg-secondary/50"
    >
      {user.profile_image_url ? (
        <img src={user.profile_image_url} alt={user.username} className="h-8 w-8 rounded-full object-cover" />
      ) : (
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
          <User className="h-4 w-4 text-muted-foreground" />
        </div>
      )}
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium truncate block">
          {user.display_name ?? user.username}
        </span>
        <span className="text-xs text-muted-foreground">@{user.username}</span>
      </div>
      {user.follower_count != null && (
        <span className="text-xs text-muted-foreground">{formatCount(user.follower_count)} followers</span>
      )}
    </Link>
  );
}

export default function UserProfilePage({
  params,
}: {
  params: Promise<{ username: string }>;
}) {
  const { username } = use(params);

  const crumbs = useMemo(
    () => [
      { label: "Explore", href: "/explore" },
      { label: `@${username}` },
    ],
    [username],
  );
  useBreadcrumbs(crumbs);

  const { data: profile, loading: profileLoading, error: profileError } =
    useFetch<UserInfo>(`explore/user/${username}`);

  const [tab, setTab] = useState<TabKey>("tweets");

  // Content for current tab
  const isPostTab = tab === "tweets" || tab === "timeline" || tab === "replies" || tab === "highlights";
  const endpoint = `explore/user/${username}/${tab}`;

  const { data: tabData, loading: tabLoading, error: tabError } = useFetch<unknown[]>(endpoint);

  return (
    <div className="space-y-6">
      {profileError && <ErrorBanner message={profileError} />}

      {/* Profile header */}
      {profileLoading ? (
        <SectionSkeleton />
      ) : profile ? (
        <div className="rounded-widget bg-secondary/50 p-5 fade-up-stagger-1">
          <div className="flex items-start gap-4">
            {profile.profile_image_url ? (
              <img
                src={profile.profile_image_url}
                alt={username}
                className="h-16 w-16 shrink-0 rounded-full object-cover"
              />
            ) : (
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-muted">
                <User className="h-8 w-8 text-muted-foreground" />
              </div>
            )}
            <div className="min-w-0 flex-1 space-y-1">
              <div className="flex items-center gap-1.5">
                <h1 className="text-xl font-bold truncate">
                  {profile.display_name ?? username}
                </h1>
                {profile.is_verified && (
                  <BadgeCheck className="h-5 w-5 text-blue-500 shrink-0" />
                )}
              </div>
              <p className="text-sm text-muted-foreground">@{username}</p>
              {profile.description && (
                <p className="text-sm">{profile.description}</p>
              )}
              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground pt-1">
                {profile.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3 w-3" /> {profile.location}
                  </span>
                )}
                {profile.website && (
                  <a
                    href={profile.website.startsWith("http") ? profile.website : `https://${profile.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 hover:text-foreground transition-colors"
                  >
                    <LinkIcon className="h-3 w-3" /> {profile.website}
                  </a>
                )}
                <span>{formatCount(profile.follower_count)} followers</span>
                <span>{formatCount(profile.following_count)} following</span>
                <span>{formatCount(profile.tweet_count)} tweets</span>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border overflow-x-auto fade-up-stagger-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "whitespace-nowrap px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px",
              tab === t.key
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tabError && <ErrorBanner message={tabError} />}

      {tabLoading ? (
        <SectionSkeleton />
      ) : tabData && tabData.length > 0 ? (
        isPostTab ? (
          <MasonryGrid>
            {(tabData as Post[]).map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </MasonryGrid>
        ) : (
          <div className="space-y-1">
            {(tabData as UserCardProps["user"][]).map((user) => (
              <UserCard key={user.username} user={user} />
            ))}
          </div>
        )
      ) : (
        <EmptyState
          title="Nothing here yet"
          message={`No ${tab} found for @${username}.`}
        />
      )}
    </div>
  );
}
