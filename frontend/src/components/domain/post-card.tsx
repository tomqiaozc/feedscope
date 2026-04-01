"use client";

import { Heart, Repeat2, MessageCircle, Eye, Trash2, Languages, User, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { relativeTime } from "@/lib/utils";
import type { Post } from "@/types/watchlist";

function formatCount(n: number | null): string {
  if (n == null) return "–";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function linkify(text: string): React.ReactNode {
  const parts = text.split(/(https?:\/\/[^\s]+)/g);
  return parts.map((part, i) =>
    part.startsWith("http") ? (
      <a
        key={i}
        href={part}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:underline dark:text-blue-400"
      >
        {part}
      </a>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

interface PostCardProps {
  post: Post;
  translating?: boolean;
  onTranslate?: (post: Post) => void;
  onDelete?: (post: Post) => void;
}

export function PostCard({ post, translating, onTranslate, onDelete }: PostCardProps) {
  const m = post.metrics;

  return (
    <div className="rounded-widget bg-secondary/50 p-4 space-y-3">
      {/* Author header */}
      <div className="flex items-center gap-2.5">
        {post.author_profile_image_url ? (
          <img
            src={post.author_profile_image_url}
            alt={post.author_username}
            className="h-8 w-8 rounded-full object-cover"
          />
        ) : (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
            <User className="h-4 w-4 text-muted-foreground" />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-1.5">
            <span className="text-sm font-medium truncate">
              {post.author_display_name ?? post.author_username}
            </span>
            <span className="text-xs text-muted-foreground">
              @{post.author_username}
            </span>
          </div>
          <span className="text-xs text-muted-foreground">
            {relativeTime(post.posted_at)}
          </span>
        </div>
        <div className="flex gap-1 shrink-0">
          {!post.translation && onTranslate && (
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => onTranslate(post)}
              disabled={translating}
              title="Translate"
            >
              {translating ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Languages className="h-3.5 w-3.5" />
              )}
            </Button>
          )}
          {onDelete && (
            <Button variant="ghost" size="icon-xs" onClick={() => onDelete(post)} title="Delete">
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      {post.content && (
        <p className="text-sm whitespace-pre-wrap break-words">
          {linkify(post.content)}
        </p>
      )}

      {/* Media grid */}
      {post.media && post.media.length > 0 && (
        <div
          className={`grid gap-1.5 ${
            post.media.length === 1
              ? "grid-cols-1"
              : post.media.length <= 4
                ? "grid-cols-2"
                : "grid-cols-3"
          }`}
        >
          {post.media.map((item, i) => (
            <div key={i} className="relative aspect-video overflow-hidden rounded-lg bg-muted">
              <img
                src={item.preview_url ?? item.url}
                alt=""
                className="h-full w-full object-cover"
              />
              {item.type === "video" && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                  <div className="rounded-full bg-black/60 p-2">
                    <svg className="h-4 w-4 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Metrics */}
      {m && (
        <div className="flex gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Heart className="h-3 w-3" /> {formatCount(m.likes)}
          </span>
          <span className="flex items-center gap-1">
            <Repeat2 className="h-3 w-3" /> {formatCount(m.retweets)}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircle className="h-3 w-3" /> {formatCount(m.replies)}
          </span>
          <span className="flex items-center gap-1">
            <Eye className="h-3 w-3" /> {formatCount(m.views)}
          </span>
        </div>
      )}

      {/* Translation section */}
      {post.translation && (
        <div className="border-t border-border pt-3 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <Languages className="h-3 w-3" />
            Translation
          </div>
          <p className="text-sm">{post.translation}</p>
          {post.editorial && (
            <p className="text-xs italic text-muted-foreground">{post.editorial}</p>
          )}
          {post.quoted_translation && (
            <blockquote className="border-l-2 border-muted-foreground/30 pl-3 text-xs text-muted-foreground">
              {post.quoted_translation}
            </blockquote>
          )}
        </div>
      )}
    </div>
  );
}
