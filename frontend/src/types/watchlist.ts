export interface Watchlist {
  id: number;
  name: string;
  description: string | null;
  member_count: number;
  post_count: number;
  created_at: string;
  updated_at: string;
}

export interface Member {
  id: number;
  username: string;
  display_name: string | null;
  profile_image_url: string | null;
  notes: string | null;
  tags: string[];
  created_at: string;
}

export interface PostMetrics {
  likes: number | null;
  retweets: number | null;
  replies: number | null;
  views: number | null;
}

export interface PostMedia {
  type: "image" | "video";
  url: string;
  preview_url?: string;
}

export interface Post {
  id: number;
  platform_id: string;
  author_username: string;
  author_display_name: string | null;
  author_profile_image_url: string | null;
  content: string | null;
  metrics: PostMetrics | null;
  media: PostMedia[] | null;
  posted_at: string;
  translation: string | null;
  editorial: string | null;
  quoted_translation: string | null;
}
