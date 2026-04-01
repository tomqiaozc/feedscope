export interface UserInfo {
  username: string;
  display_name: string | null;
  profile_image_url: string | null;
  description: string | null;
  follower_count: number;
  following_count: number;
  tweet_count: number;
  is_verified: boolean;
  location: string | null;
  website: string | null;
}
