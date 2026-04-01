"use client";

import Link from "next/link";
import { List, Pencil, Trash2, Clock } from "lucide-react";
import { cn, relativeTime } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import type { Watchlist } from "@/types/watchlist";

interface WatchlistCardProps {
  watchlist: Watchlist;
  onEdit?: (watchlist: Watchlist) => void;
  onDelete?: (watchlist: Watchlist) => void;
}

export function WatchlistCard({ watchlist, onEdit, onDelete }: WatchlistCardProps) {
  return (
    <div className="group relative rounded-widget bg-secondary/50 p-4 transition-shadow hover:shadow-md">
      <Link
        href={`/watchlist/${watchlist.id}`}
        className="absolute inset-0 z-0 rounded-widget"
      >
        <span className="sr-only">View {watchlist.name}</span>
      </Link>

      <div className="relative z-10">
        <div className="flex items-start justify-between">
          <h3 className="font-medium text-sm">{watchlist.name}</h3>
          <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
            {onEdit && (
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={(e) => { e.preventDefault(); onEdit(watchlist); }}
              >
                <Pencil className="h-3 w-3" />
              </Button>
            )}
            {onDelete && (
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={(e) => { e.preventDefault(); onDelete(watchlist); }}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>

        {watchlist.description && (
          <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
            {watchlist.description}
          </p>
        )}

        <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <List className="h-3 w-3" />
            {watchlist.member_count} members
          </span>
          <span>{watchlist.post_count} posts</span>
          <span className={cn("ml-auto flex items-center gap-1")}>
            <Clock className="h-3 w-3" />
            {relativeTime(watchlist.updated_at)}
          </span>
        </div>
      </div>
    </div>
  );
}
