export interface Group {
  id: number;
  name: string;
  description: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface GroupMember {
  id: number;
  username: string;
  display_name: string | null;
  profile_image_url: string | null;
  notes: string | null;
  created_at: string;
}
