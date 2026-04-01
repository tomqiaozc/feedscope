"use client";

import { Pencil, Trash2, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Member } from "@/types/watchlist";

const TAG_COLORS = [
  "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200",
  "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200",
];

function tagColor(tag: string): string {
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = ((hash << 5) - hash + tag.charCodeAt(i)) | 0;
  }
  return TAG_COLORS[Math.abs(hash) % TAG_COLORS.length];
}

interface MemberRowProps {
  member: Member;
  onEdit?: (member: Member) => void;
  onDelete?: (member: Member) => void;
  onRemoveTag?: (member: Member, tag: string) => void;
}

export function MemberRow({ member, onEdit, onDelete, onRemoveTag }: MemberRowProps) {
  return (
    <div className="flex items-center gap-3 rounded-widget px-3 py-2.5 transition-colors hover:bg-secondary/50">
      {/* Avatar */}
      {member.profile_image_url ? (
        <img
          src={member.profile_image_url}
          alt={member.username}
          className="h-8 w-8 shrink-0 rounded-full object-cover"
        />
      ) : (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
          <User className="h-4 w-4 text-muted-foreground" />
        </div>
      )}

      {/* Info */}
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-1.5">
          <span className="text-sm font-medium truncate">@{member.username}</span>
          {member.display_name && (
            <span className="text-xs text-muted-foreground truncate">
              {member.display_name}
            </span>
          )}
        </div>
        {member.notes && (
          <p className="text-xs text-muted-foreground truncate">{member.notes}</p>
        )}
      </div>

      {/* Tags */}
      {member.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {member.tags.map((tag) => (
            <span
              key={tag}
              className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-medium ${tagColor(tag)}`}
            >
              {tag}
              {onRemoveTag && (
                <button
                  type="button"
                  onClick={() => onRemoveTag(member, tag)}
                  className="ml-0.5 hover:opacity-70"
                  aria-label={`Remove tag ${tag}`}
                >
                  &times;
                </button>
              )}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex shrink-0 gap-1">
        {onEdit && (
          <Button variant="ghost" size="icon-xs" onClick={() => onEdit(member)}>
            <Pencil className="h-3 w-3" />
          </Button>
        )}
        {onDelete && (
          <Button variant="ghost" size="icon-xs" onClick={() => onDelete(member)}>
            <Trash2 className="h-3 w-3" />
          </Button>
        )}
      </div>
    </div>
  );
}
