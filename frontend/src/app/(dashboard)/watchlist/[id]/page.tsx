"use client";

import { useState, useEffect, useMemo, use } from "react";
import { Plus, Download, Languages } from "lucide-react";
import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";
import { useFetch } from "@/hooks/use-fetch";
import { fetchApi } from "@/lib/api";
import { useSSE } from "@/hooks/use-sse";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionSkeleton } from "@/components/ui/section-skeleton";
import { ErrorBanner } from "@/components/ui/error-banner";
import { StatusMessage } from "@/components/ui/status-message";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { MemberRow } from "@/components/domain/member-row";
import { PostCard } from "@/components/domain/post-card";
import type { Watchlist, Member, Post } from "@/types/watchlist";

type Tab = "members" | "posts";

interface FetchProgress {
  current: number;
  total: number;
  username: string;
  postCount: number;
  errors: string[];
}

export default function WatchlistDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const { data: watchlist } = useFetch<Watchlist>(`watchlists/${id}`);

  const crumbs = useMemo(
    () => [
      { label: "Watchlists", href: "/watchlist" },
      { label: watchlist?.name ?? "..." },
    ],
    [watchlist?.name],
  );
  useBreadcrumbs(crumbs);

  const [tab, setTab] = useState<Tab>("members");

  // --- Members ---
  const {
    data: members,
    loading: membersLoading,
    error: membersError,
    refetch: refetchMembers,
  } = useFetch<Member[]>(`watchlists/${id}/members`);

  const [memberFormOpen, setMemberFormOpen] = useState(false);
  const [memberEditTarget, setMemberEditTarget] = useState<Member | null>(null);
  const [memberUsername, setMemberUsername] = useState("");
  const [memberDisplayName, setMemberDisplayName] = useState("");
  const [memberNotes, setMemberNotes] = useState("");
  const [memberTags, setMemberTags] = useState("");
  const [memberSaving, setMemberSaving] = useState(false);
  const [deleteMemberTarget, setDeleteMemberTarget] = useState<Member | null>(null);
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // --- Posts ---
  const [postsOffset, setPostsOffset] = useState(0);
  const [allPosts, setAllPosts] = useState<Post[]>([]);
  const [postsHasMore, setPostsHasMore] = useState(true);
  const {
    data: postsPage,
    loading: postsLoading,
    error: postsError,
    refetch: refetchPosts,
  } = useFetch<Post[]>(`watchlists/${id}/posts?offset=0&limit=50`);

  // Sync initial posts page into allPosts
  useEffect(() => {
    if (postsPage && postsPage.length > 0) {
      setAllPosts(postsPage);
      if (postsPage.length < 50) setPostsHasMore(false);
    }
  }, [postsPage]);

  const [tagFilter, setTagFilter] = useState<string | null>(null);
  const [memberFilter, setMemberFilter] = useState<number | null>(null);
  const [deletePostTarget, setDeletePostTarget] = useState<Post | null>(null);

  // --- Per-post translation ---
  const [translatingPostId, setTranslatingPostId] = useState<number | null>(null);

  async function handleTranslatePost(post: Post) {
    setTranslatingPostId(post.id);
    setStatus(null);
    try {
      const result = await fetchApi<{
        translation: string;
        editorial: string | null;
        quoted_translation: string | null;
      }>("translate", {
        method: "POST",
        body: JSON.stringify({
          text: post.content,
          quoted_text: post.quoted_translation,
        }),
      });
      setAllPosts((prev) =>
        prev.map((p) =>
          p.id === post.id
            ? {
                ...p,
                translation: result.translation,
                editorial: result.editorial,
                quoted_translation: result.quoted_translation,
              }
            : p,
        ),
      );
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Translation failed",
      });
    } finally {
      setTranslatingPostId(null);
    }
  }

  // --- Batch translate SSE ---
  interface TranslateProgress {
    current: number;
    total: number;
    success: number;
    errors: number;
  }
  const [translateProgress, setTranslateProgress] = useState<TranslateProgress | null>(null);

  const translateSSE = useSSE<Record<string, unknown>>({
    url: `/api/proxy/watchlists/${id}/translate`,
    method: "POST",
    onEvent: (event, data) => {
      switch (event) {
        case "start":
          setTranslateProgress({ current: 0, total: (data.total as number) ?? 0, success: 0, errors: 0 });
          break;
        case "translating":
          setTranslateProgress((prev) =>
            prev ? { ...prev, current: (data.current as number) ?? prev.current } : prev,
          );
          break;
        case "translated": {
          const postId = data.post_id as number;
          const translation = data.translation as string;
          const editorial = (data.editorial as string) ?? null;
          const quotedTranslation = (data.quoted_translation as string) ?? null;
          setAllPosts((prev) =>
            prev.map((p) =>
              p.id === postId
                ? { ...p, translation, editorial, quoted_translation: quotedTranslation }
                : p,
            ),
          );
          setTranslateProgress((prev) =>
            prev ? { ...prev, success: prev.success + 1 } : prev,
          );
          break;
        }
        case "error":
          setTranslateProgress((prev) =>
            prev ? { ...prev, errors: prev.errors + 1 } : prev,
          );
          break;
      }
    },
    onDone: () => {
      const p = translateProgress;
      setTranslateProgress(null);
      setStatus({
        type: "success",
        message: `Batch translate complete: ${p?.success ?? 0} translated, ${p?.errors ?? 0} errors.`,
      });
    },
    onError: (err) => {
      setTranslateProgress(null);
      setStatus({ type: "error", message: err.message });
    },
  });

  const untranslatedCount = allPosts.filter((p) => !p.translation && p.content).length;

  // Derive all tags from members
  const allTags = Array.from(new Set((members ?? []).flatMap((m) => m.tags)));

  // Filtered posts
  const filteredPosts = allPosts.filter((p) => {
    if (tagFilter) {
      const member = members?.find((m) => m.username === p.author_username);
      if (!member?.tags.includes(tagFilter)) return false;
    }
    if (memberFilter) {
      const member = members?.find((m) => m.id === memberFilter);
      if (member && p.author_username !== member.username) return false;
    }
    return true;
  });

  // --- SSE Fetch ---
  const [fetchProgress, setFetchProgress] = useState<FetchProgress | null>(null);

  const sse = useSSE<Record<string, unknown>>({
    url: `/api/proxy/watchlists/${id}/fetch`,
    method: "POST",
    onEvent: (event, data) => {
      setFetchProgress((prev) => {
        const p = prev ?? { current: 0, total: 0, username: "", postCount: 0, errors: [] };
        switch (event) {
          case "cleanup":
            return { ...p, username: "Preparing..." };
          case "progress":
            return {
              ...p,
              current: (data.current as number) ?? p.current,
              total: (data.total as number) ?? p.total,
              username: (data.username as string) ?? p.username,
            };
          case "posts":
            return { ...p, postCount: p.postCount + ((data.count as number) ?? 0) };
          case "error":
            return { ...p, errors: [...p.errors, (data.message as string) ?? "Unknown error"] };
          default:
            return p;
        }
      });
    },
    onDone: () => {
      setFetchProgress(null);
      setStatus({ type: "success", message: "Fetch complete." });
      setAllPosts([]);
      setPostsOffset(0);
      setPostsHasMore(true);
      refetchPosts();
    },
    onError: (err) => {
      setFetchProgress(null);
      setStatus({ type: "error", message: err.message });
    },
  });

  // --- Member form ---
  function openAddMember() {
    setMemberEditTarget(null);
    setMemberUsername("");
    setMemberDisplayName("");
    setMemberNotes("");
    setMemberTags("");
    setMemberFormOpen(true);
    setStatus(null);
  }

  function openEditMember(m: Member) {
    setMemberEditTarget(m);
    setMemberUsername(m.username);
    setMemberDisplayName(m.display_name ?? "");
    setMemberNotes(m.notes ?? "");
    setMemberTags(m.tags.join(", "));
    setMemberFormOpen(true);
    setStatus(null);
  }

  function closeMemberForm() {
    setMemberFormOpen(false);
    setMemberEditTarget(null);
  }

  async function handleMemberSubmit() {
    setMemberSaving(true);
    setStatus(null);
    const tags = memberTags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    try {
      if (memberEditTarget) {
        await fetchApi(`watchlists/${id}/members/${memberEditTarget.id}`, {
          method: "PUT",
          body: JSON.stringify({
            display_name: memberDisplayName || null,
            notes: memberNotes || null,
            tags,
          }),
        });
        setStatus({ type: "success", message: "Member updated." });
      } else {
        await fetchApi(`watchlists/${id}/members`, {
          method: "POST",
          body: JSON.stringify({
            username: memberUsername,
            display_name: memberDisplayName || null,
            notes: memberNotes || null,
            tags,
          }),
        });
        setStatus({ type: "success", message: "Member added." });
      }
      closeMemberForm();
      refetchMembers();
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to save member",
      });
    } finally {
      setMemberSaving(false);
    }
  }

  async function handleDeleteMember() {
    if (!deleteMemberTarget) return;
    try {
      await fetchApi(`watchlists/${id}/members/${deleteMemberTarget.id}`, {
        method: "DELETE",
      });
      setDeleteMemberTarget(null);
      setStatus({ type: "success", message: "Member removed." });
      refetchMembers();
    } catch (err) {
      setDeleteMemberTarget(null);
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to remove member",
      });
    }
  }

  async function handleDeletePost() {
    if (!deletePostTarget) return;
    try {
      await fetchApi(`watchlists/${id}/posts/${deletePostTarget.id}`, {
        method: "DELETE",
      });
      setAllPosts((prev) => prev.filter((p) => p.id !== deletePostTarget.id));
      setDeletePostTarget(null);
      setStatus({ type: "success", message: "Post deleted." });
    } catch (err) {
      setDeletePostTarget(null);
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to delete post",
      });
    }
  }

  async function loadMorePosts() {
    const nextOffset = postsOffset + 50;
    try {
      const page = await fetchApi<Post[]>(
        `watchlists/${id}/posts?offset=${nextOffset}&limit=50`,
      );
      setAllPosts((prev) => [...prev, ...page]);
      setPostsOffset(nextOffset);
      if (page.length < 50) setPostsHasMore(false);
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to load more posts",
      });
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between fade-up-stagger-1">
        <h1 className="text-2xl font-bold">{watchlist?.name ?? "..."}</h1>
        <div className="flex gap-2">
          {sse.isStreaming ? (
            <Button variant="outline" size="sm" onClick={sse.abort}>
              Cancel Fetch
            </Button>
          ) : (
            <Button size="sm" onClick={sse.start} disabled={sse.isStreaming}>
              <Download className="h-4 w-4" />
              Fetch
            </Button>
          )}
        </div>
      </div>

      {/* Fetch progress */}
      {fetchProgress && (
        <div className="rounded-widget bg-secondary/50 p-4 space-y-2 fade-up-stagger-2">
          <div className="flex items-center justify-between text-sm">
            <span>
              {fetchProgress.username === "Preparing..."
                ? "Preparing..."
                : `Fetching @${fetchProgress.username} (${fetchProgress.current}/${fetchProgress.total})...`}
            </span>
            <span className="text-muted-foreground">{fetchProgress.postCount} posts</span>
          </div>
          {fetchProgress.total > 0 && (
            <div className="h-1.5 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-primary transition-all"
                style={{
                  width: `${Math.round((fetchProgress.current / fetchProgress.total) * 100)}%`,
                }}
              />
            </div>
          )}
          {fetchProgress.errors.map((err, i) => (
            <p key={i} className="text-xs text-destructive">{err}</p>
          ))}
        </div>
      )}

      {status && <StatusMessage type={status.type} message={status.message} />}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border fade-up-stagger-2">
        {(["members", "posts"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px",
              tab === t
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t === "members" ? `Members (${members?.length ?? 0})` : `Posts (${allPosts.length})`}
          </button>
        ))}
      </div>

      {/* Members tab */}
      {tab === "members" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button size="sm" onClick={openAddMember}>
              <Plus className="h-4 w-4" />
              Add Member
            </Button>
          </div>

          {membersError && <ErrorBanner message={membersError} />}

          {membersLoading ? (
            <SectionSkeleton />
          ) : members && members.length > 0 ? (
            <div className="space-y-1">
              {members.map((m) => (
                <MemberRow
                  key={m.id}
                  member={m}
                  onEdit={openEditMember}
                  onDelete={setDeleteMemberTarget}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No members yet"
              message="Add Twitter/X accounts to start tracking."
            />
          )}
        </div>
      )}

      {/* Posts tab */}
      {tab === "posts" && (
        <div className="space-y-4">
          {/* Filters + Translate All */}
          <div className="flex flex-wrap items-center gap-2">
            {allTags.map((tag) => (
              <button
                key={tag}
                onClick={() => setTagFilter(tagFilter === tag ? null : tag)}
                className={cn(
                  "rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
                  tagFilter === tag
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
                )}
              >
                {tag}
              </button>
            ))}
            {members && members.length > 1 && (
              <select
                value={memberFilter ?? ""}
                onChange={(e) =>
                  setMemberFilter(e.target.value ? Number(e.target.value) : null)
                }
                className="rounded-lg border border-border bg-background px-2.5 py-1 text-xs outline-none"
              >
                <option value="">All members</option>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    @{m.username}
                  </option>
                ))}
              </select>
            )}
            <div className="ml-auto">
              {translateSSE.isStreaming ? (
                <Button variant="outline" size="sm" onClick={translateSSE.abort}>
                  Cancel Translate
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={translateSSE.start}
                  disabled={untranslatedCount === 0 || sse.isStreaming}
                >
                  <Languages className="h-3.5 w-3.5" />
                  Translate All ({untranslatedCount})
                </Button>
              )}
            </div>
          </div>

          {/* Batch translate progress */}
          {translateProgress && (
            <div className="rounded-widget bg-secondary/50 p-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Translating post {translateProgress.current}/{translateProgress.total}...</span>
                <span className="text-muted-foreground">
                  {translateProgress.success} done, {translateProgress.errors} errors
                </span>
              </div>
              {translateProgress.total > 0 && (
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{
                      width: `${Math.round(
                        ((translateProgress.success + translateProgress.errors) / translateProgress.total) * 100,
                      )}%`,
                    }}
                  />
                </div>
              )}
            </div>
          )}

          {postsError && <ErrorBanner message={postsError} />}

          {postsLoading ? (
            <SectionSkeleton />
          ) : filteredPosts.length > 0 ? (
            <div className="space-y-4">
              {filteredPosts.map((p) => (
                <PostCard
                  key={p.id}
                  post={p}
                  translating={translatingPostId === p.id}
                  onTranslate={handleTranslatePost}
                  onDelete={setDeletePostTarget}
                />
              ))}
              {postsHasMore && !tagFilter && !memberFilter && (
                <div className="flex justify-center">
                  <Button variant="outline" size="sm" onClick={loadMorePosts}>
                    Load More
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <EmptyState
              title="No posts yet"
              message="Click Fetch to pull the latest posts from tracked members."
            />
          )}
        </div>
      )}

      {/* Member form dialog */}
      <Dialog open={memberFormOpen} onOpenChange={(open) => { if (!open) closeMemberForm(); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{memberEditTarget ? "Edit Member" : "Add Member"}</DialogTitle>
            <DialogDescription>
              {memberEditTarget
                ? "Update member details and tags."
                : "Add a Twitter/X account to this watchlist."}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="m-username" className="text-xs font-medium text-muted-foreground">
                Username *
              </label>
              <input
                id="m-username"
                type="text"
                value={memberUsername}
                onChange={(e) => setMemberUsername(e.target.value)}
                placeholder="e.g. elonmusk"
                disabled={!!memberEditTarget}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50 disabled:opacity-50"
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="m-display" className="text-xs font-medium text-muted-foreground">
                Display Name
              </label>
              <input
                id="m-display"
                type="text"
                value={memberDisplayName}
                onChange={(e) => setMemberDisplayName(e.target.value)}
                placeholder="Optional display name"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="m-notes" className="text-xs font-medium text-muted-foreground">
                Notes
              </label>
              <textarea
                id="m-notes"
                value={memberNotes}
                onChange={(e) => setMemberNotes(e.target.value)}
                placeholder="Optional notes"
                rows={2}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50 resize-none"
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="m-tags" className="text-xs font-medium text-muted-foreground">
                Tags (comma-separated)
              </label>
              <input
                id="m-tags"
                type="text"
                value={memberTags}
                onChange={(e) => setMemberTags(e.target.value)}
                placeholder="e.g. tech, influencer"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={closeMemberForm} disabled={memberSaving}>
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleMemberSubmit}
              disabled={memberSaving || (!memberEditTarget && !memberUsername.trim())}
            >
              {memberSaving ? "Saving..." : memberEditTarget ? "Update" : "Add"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete member confirm */}
      <ConfirmDialog
        open={!!deleteMemberTarget}
        onOpenChange={(open) => { if (!open) setDeleteMemberTarget(null); }}
        title="Remove Member"
        description={`Remove @${deleteMemberTarget?.username} from this watchlist? Their posts will remain.`}
        confirmLabel="Remove"
        variant="destructive"
        onConfirm={handleDeleteMember}
      />

      {/* Delete post confirm */}
      <ConfirmDialog
        open={!!deletePostTarget}
        onOpenChange={(open) => { if (!open) setDeletePostTarget(null); }}
        title="Delete Post"
        description="Are you sure you want to delete this post? This cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDeletePost}
      />
    </div>
  );
}
