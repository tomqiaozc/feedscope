"use client";

import Link from "next/link";
import { Users, Pencil, Trash2, Clock } from "lucide-react";
import { cn, relativeTime } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import type { Group } from "@/types/group";

interface GroupCardProps {
  group: Group;
  onEdit?: (group: Group) => void;
  onDelete?: (group: Group) => void;
}

export function GroupCard({ group, onEdit, onDelete }: GroupCardProps) {
  return (
    <div className="group relative rounded-widget bg-secondary/50 p-4 transition-shadow hover:shadow-md">
      <Link
        href={`/groups/${group.id}`}
        className="absolute inset-0 z-0 rounded-widget"
      >
        <span className="sr-only">View {group.name}</span>
      </Link>

      <div className="relative z-10">
        <div className="flex items-start justify-between">
          <h3 className="font-medium text-sm">{group.name}</h3>
          <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
            {onEdit && (
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={(e) => { e.preventDefault(); onEdit(group); }}
              >
                <Pencil className="h-3 w-3" />
              </Button>
            )}
            {onDelete && (
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={(e) => { e.preventDefault(); onDelete(group); }}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>

        {group.description && (
          <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
            {group.description}
          </p>
        )}

        <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Users className="h-3 w-3" />
            {group.member_count} members
          </span>
          <span className={cn("ml-auto flex items-center gap-1")}>
            <Clock className="h-3 w-3" />
            {relativeTime(group.updated_at)}
          </span>
        </div>
      </div>
    </div>
  );
}
