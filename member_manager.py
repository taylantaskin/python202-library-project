# member_manager.py
import json
from pathlib import Path
from typing import List, Optional
from member import Member

class MemberManager:
    """
    Manages library members and stores them in a JSON file.
    """
    def __init__(self, data_file: str = "members.json"):
        self.data_file = Path(data_file)
        self.members: List[Member] = []
        self.load_members()

    def load_members(self) -> None:
        """Loads members from the JSON file."""
        if not self.data_file.exists():
            self.members = []
            return
        try:
            raw = json.loads(self.data_file.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise ValueError("members.json must contain a list")
            self.members = [Member.from_dict(item) for item in raw]
        except Exception as e:
            print(f"[WARN] Couldn't load {self.data_file}: {e}. Starting with empty list.")
            self.members = []

    def save_members(self) -> None:
        """Saves the current list of members to the JSON file (atomically)."""
        data = [m.to_dict() for m in self.members]
        tmp = self.data_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.data_file)

    def add_member(self, member: Member) -> None:
        """Adds a new member and saves the change."""
        if any(m.member_id == member.member_id for m in self.members):
            raise ValueError(f"A member with ID {member.member_id} already exists.")
        self.members.append(member)
        self.save_members()

    def remove_member(self, member_id: str) -> None:
        """Removes a member by ID and saves the change."""
        for m in self.members:
            if m.member_id == member_id:
                self.members.remove(m)
                self.save_members()
                return
        raise ValueError(f"No member found with ID {member_id}.")

    def find_member(self, member_id: str) -> Optional[Member]:
        """Finds and returns a member by ID."""
        for member in self.members:
            if member.member_id == member_id:
                return member
        return None

    def list_members(self) -> List[Member]:
        """Returns all members (CLI tarafında yazdırılır)."""
        return list(self.members)
